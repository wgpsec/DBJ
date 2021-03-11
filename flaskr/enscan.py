#conding=utf-8
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for,jsonify,current_app,Flask
)
from requests.packages import urllib3
import threading
import requests
import random
import json
import sys
import os
import re
import redis

bp = Blueprint('enscan', __name__,url_prefix='/enscan')

pool = redis.ConnectionPool(host='127.0.0.1', port=6379,decode_responses=True, encoding='UTF-8')
re_dis = redis.Redis(connection_pool=pool)

# 设置最大线程数
thread_max = threading.BoundedSemaphore(value=100)
threads=[]
check_threads=[]#复检线程池

#消除安全请求的提示信息,增加重试连接次数
urllib3.disable_warnings()
requests.adapters.DEFAULT_RETRIES = 3

#关闭连接，防止出现最大连接数限制错误
s = requests.Session()
s.keep_alive = False

errors = []         #错误复检列表
proxys = []         #代理列表

domains = []        #一级域名列表
sub_company_id=[]   #二级单位的PID列表
success_company_ids=[]  #成功查到的所有公司ID

Websites=[]         #用于ICP反查域名的网站列表

#HTTP请求-head头
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded'
}

#set-cookie
def setcookie():
    cs='n'
    with open('./baidu_cookie.txt','r',encoding='utf-8') as f:
        cooks=f.read()
        cooks=json.loads(cooks)
        for cks in cooks:
            if cks['name']=='BAIDUID':
                cs=cks['name']+"="+cks['value']+";"
                return cs

#随机生成IP
def random_ip():
    ip = ".".join(map(str, (random.randint(0, 255) for _ in range(4)))) 
    return ip

# 百分数转为浮点数
def percent_to_int(string):
    if "%" in string:
        string = string.strip("%")
        string = float(string)
        string = int(string)
        newint = string / 100
        return newint
    else:
        return 0.5
        #print("你输入的不是百分比！")

def get_icp(target):
    '''ICP备案反查域名列表'''
    api='https://www.beianx.cn/bacx/'
    url=api+target
    resp = s.get(url,verify=False,headers=headers,timeout=8)
    pat = r'<div><a href="/bacx/(.*?)">.*?</a></div>'
    rs=re.findall(pat,resp.text)
    for dom in rs:
        re_dis.hmset(dom,{'domain':dom,'domain_from':"ICP备案查询"})
        re_dis.rpush('alldomains',dom)
        domains.append(dom)

def get_whois(company_name):
    '''whois反查域名'''
    try:
        url = "http://whois.chinaz.com/reverse?host={0}&ddlSearchMode=2".format(company_name)
        resp = s.get(url,verify=False,headers=headers,timeout=8)
        page_pat = r'<span class="col-gray02">共(.*?)页.*?</span>'
        page = re.findall(page_pat,resp.text)
        resp.close()
        if len(page):
            i=0
            while i< int(page[0]):
                i = i+1
                url = "http://whois.chinaz.com/reverse?host={0}&ddlSearchMode=2&st=&startDay=&endDay=&wTimefilter=$wTimefilter&page={1}".format(company_name,str(i))
                resp = s.get(url,verify=False,headers=headers,timeout=8)
                pat = r'<div class="listOther"><a href="/.*?>(.*?)</a></div>'
                dns_domains = re.findall(pat,resp.text)
                for domain in dns_domains:
                    if domain not in domains:
                        re_dis.hmset(domain,{'domain':domain,'domain_from':"whois查询"})
                        re_dis.rpush('alldomains',domain)
                        domains.append(domain)
        else:
            url = "http://whois.chinaz.com/reverse?host={0}&ddlSearchMode=2&st=&startDay=&endDay=&wTimefilter=$wTimefilter&page=1".format(company_name)
            resp = s.get(url,verify=False,headers=headers,timeout=8)
            pat = r'<div class="listOther"><a href="/.*?>(.*?)</a></div>'
            dns_domains = re.findall(pat,resp.text)
            for domain in dns_domains:
                if domain not in domains:
                    re_dis.hmset(domain,{'domain':domain,'domain_from':"whois查询"})
                    re_dis.rpush('alldomains',domain)
                    domains.append(domain)
    except Exception as ef:
        print(str(ef))

def parse_index(content):
    tag_1 = 'window.pageData ='
    tag_2 = '/* eslint-enable */</script><script data-app'
    
    idx_1 = content.find(tag_1)
    idx_2 = content.find(tag_2)
    
    mystr = content[idx_1 + len(tag_1): idx_2].strip()
    len_str = len(mystr)
    if mystr[len_str - 1] == ';':
        mystr = mystr[0:len_str - 1]
        json_data = json.loads(mystr)
        if len(json_data["result"]) > 0:
            item = json_data["result"]
            return item
        else:
            return None
    else:
        return None

def get_root_companyid(company_name):
    global root_company_id
    url = 'https://aiqicha.baidu.com/s?q='+company_name
    try:
        s.headers.update({'Cookie':cookies})
        resp = s.get(url, headers=headers, timeout=12,verify=False)
        item = parse_index(resp.text)
        root_company_id = item["resultList"][0]['pid']
        resp.close()
    except Exception as ex_com:
        print(str(ex_com)+' 获取主公司ID时出错')


def get_company_info(company_id,level,regrate,hunit):
    global pdomain
    global pname
    global num
    api = 'https://aiqicha.baidu.com/company_detail_'
    api = api + str(company_id)
    rip = random_ip()
    try:
        s.headers.update({'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'})
        s.headers.update({'Connection': 'close'})
        s.headers.update({'Content-Type':'application/x-www-form-urlencoded'})
        s.headers.update({'X-Remote-Addr': rip})
        resp = s.get(api,verify=False,timeout=15)
        item = parse_index(resp.text)
        company_name = item['entName']  #公司名
        website = item['website']       #网站首页
        email = item['email']           #邮箱
        phone = item['telephone']       #电话号码
        resp.close()

        # #域名入缓存数据库，三级单位偏差太大，暂时取消 此渠道，请手动处理
        # if website[0:4]=="www.":
        #     dom = website[4:]
        #     if dom not in domains:
        #         re_dis.hmset(dom,{'domain':dom,'domain_from':"爱企查"})
        #         re_dis.rpush('alldomains',dom)
        #         domains.append(dom.strip())

        #取主公司的首页和公司名用于 ICP和Whois查询
        if level=="主公司":
            pname = company_name
        else:
            pass
        
        #存储进所有公司名 和 组织架构信息进缓存数据库
        re_dis.rpush('allcompanys',company_name)   
        re_dis.hmset(company_name,{'index':str(num),'company_name':company_name,'website':website,'email':email,'tel_phone':phone,'level':level,'regrate':regrate,'hunit':hunit})
        success_company_ids.append(str(company_id))

        #打印扫描进展（数据来源:企业组织架构缓存数据）
        print(re_dis.hmget(company_name,['index','company_name','website','email','tel_phone','level','regrate','hunit']))
        num = num+1

    except Exception as x:
        print(str(x))
        error = []
        error.append(company_id)
        error.append(level)
        error.append(regrate)
        error.append(hunit)
        errors.append(error)
        

def get_sub_companys(root_company_id,level):
    '''通过爱企查主公司ID,查询子公司名称和信息'''
    invest_url="https://aiqicha.baidu.com/detail/investajax?p=1&size=110&pid={0}&f=%7b\"openStatus\":\"开业\"%7d".format(root_company_id)
    hunit_url = "https://aiqicha.baidu.com/company_detail_{0}".format(root_company_id)
    try:
        resp = s.get(invest_url,verify=False,headers=headers,timeout=8)
        invests = json.loads(resp.text) 
        invests = invests['data']['list']
        resp.close()

        resp = s.get(hunit_url,verify=False,headers=headers,timeout=8)
        item = parse_index(resp.text)
        company_name = item['entName']  #公司名

        for invest in invests:
            regrate = percent_to_int(invest['regRate'])
            if(invest['openStatus']=='开业' and regrate > 0.2):
                if level=="二级单位":
                    sub_company_id.append(invest['pid'])
                    #get_company_info(invest['pid'],level,invest['regRate'],pname)
                    thread_max.acquire()
                    t=threading.Thread(target=get_company_info,args=(invest['pid'],level,invest['regRate'],pname))
                    threads.append(t)
                    t.start()
                else:
                    get_company_info(invest['pid'],level,invest['regRate'],company_name,)   
    except Exception as ex:
        print(str(ex))

def Two_sub(pid):
    branch_url="https://aiqicha.baidu.com/detail/branchajax?p=1&size=100&pid={0}&f=%7b\"openStatus\":\"开业\"%7d".format(root_company_id)
    resp_b = s.get(branch_url,verify=False,headers=headers,timeout=8)
    branchs = json.loads(resp_b.text)
    branchs = branchs['data']['list']
    resp_b.close()
    for branch in branchs:
        if(branch['openStatus']=='开业'):
            get_company_info(branch['pid'],"分支机构","100%",pname,)
    get_sub_companys(pid,"二级单位")
    for j in threads:
        j.join()

def Three_sub():
    for pid in sub_company_id:
        thread_max.acquire()
        t=threading.Thread(target=get_sub_companys,args=(pid,"三级单位",))
        threads.append(t)
        t.start()
    for j in threads:
        j.join()

#错误任务复检
def check_error():
    for err in errors:
        thread_max.acquire()
        t=threading.Thread(target=get_company_info,args=(err[0],err[1],err[2],err[3],))
        check_threads.append(t)
        t.start()
    for j in check_threads:
        j.join()


#企业组织架构查询
@bp.route('/escan', methods=('GET', 'POST'))
def escan():
    if request.method == 'POST':
        company = request.form['company']
        global num
        global cookies
        num = 1   #重置序号
        cookies=setcookie()
        re_dis.flushall()#先清空Redis缓存

        get_root_companyid(company) #获取主公司ID
        get_company_info(root_company_id,"主公司","100%","主公司") #获取主公司信息

        get_icp(pname)      #ICP反查域名
        get_whois(pname)    #whois反查域名

        Two_sub(root_company_id)    #获取二级单位的信息
        Three_sub()                 #获取三级单位的信息
        check_error()               #复检报错的线程任务

        #最后输出没查到的错误信息
        for err in errors:
            if err[0] in success_company_ids:
                errors.remove(err)
            else:
                with open('error.txt','a') as f:
                    f.write(str(err)+'\n')

        return render_template('admin/escan.html')
    else:
        return render_template('admin/escan.html')

#企业组织架构数据表查询接口
@bp.route('/getinfo', methods=('GET', 'POST'))
def getinfo():
    rs_list = []
    val={}
    count=0
    companys = re_dis.lrange('allcompanys',0,-1)
    for company in companys:
        tmp = re_dis.hmget(company,['index','company_name','website','email','tel_phone','level','regrate','hunit'])
        val={'index':tmp[0],'company_name':tmp[1],'website':tmp[2],'email':tmp[3],'tel_phone':tmp[4],'level':tmp[5],'regrate':tmp[6],'hunit':tmp[7]}
        rs_list.append(val)
        count = count+1
    table_result = {"code": 0, "msg": None, "count": count, "data": rs_list}
    return jsonify(table_result)

#域名统计数据表查询接口
@bp.route('/getdomains', methods=('GET', 'POST'))
def getdomains():
    rs_list = []
    val={}
    count=0
    domains = re_dis.lrange('alldomains',0,-1)
    for domain in domains:
        tmp = re_dis.hmget(domain,['domain','domain_from'])
        val={'domain':tmp[0],'domain_from':tmp[1]}
        rs_list.append(val)
        count = count+1
    table_result = {"code": 0, "msg": None, "count": count, "data": rs_list}
    return jsonify(table_result)

#ICON_HASH接口
@bp.route('/geticon_webs', methods=('GET', 'POST'))
def geticon_webs():
    rs_list = []
    val={}
    count=0
    icowebs = re_dis.lrange('all_ico_webs',0,-1)
    for icow in icowebs:
        tmp = re_dis.hmget(icow,['index','host','ip','port','web_title','container','country','province','city'])
        val={'index':tmp[0],'host':tmp[1],'ip':tmp[2],'port':tmp[3],'web_title':tmp[4],'container':tmp[5],'country':tmp[6],'province':tmp[7],'city':tmp[8]}
        rs_list.append(val)
        count = count+1
    table_result = {"code": 0, "msg": None, "count": count, "data": rs_list}
    return jsonify(table_result)