# conding=utf-8

from flask import (
    Blueprint, render_template, request, jsonify,
)
from requests.packages import urllib3
import threading
import requests
import random
import json
import re
import redis

bp = Blueprint('enscan', __name__, url_prefix='/enscan')

pool = redis.ConnectionPool(host='127.0.0.1', port=6379, decode_responses=True, encoding='UTF-8')
re_dis = redis.Redis(connection_pool=pool)

# 设置最大线程数
thread_max = threading.BoundedSemaphore(value=100)
threads = []
check_threads = []  # 复检线程池

# 消除安全请求的提示信息,增加重试连接次数
urllib3.disable_warnings()
requests.adapters.DEFAULT_RETRIES = 1

# 关闭连接，防止出现最大连接数限制错误
s = requests.Session()
s.keep_alive = False

errors = []  # 错误复检列表
data_list = []  #存储每个公司信息
success_company_ids = []  # 成功查到的所有公司ID
sub_company_id = []  # 二级单位的PID列表

domains = []  # 一级域名列表，用于处理重复数据
domains_rs = []  # 一级域名结果展示列表
icp_targets = []          # 所有公司名，用于ICP反查

# HTTP请求-head头
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Cookie': 'BAIDUID=7932DC5339ABD6E84CB01EBD612A789S:FG=1;'
}

def clear_lists():
    errors.clear()
    data_list.clear()
    sub_company_id.clear()
    success_company_ids.clear()

# set-cookie
def setcookie():
    cs = 'n'
    with open('./baidu_cookie.txt', 'r', encoding='utf-8') as f:
        cooks = f.read()
        cooks = json.loads(cooks)
        for cks in cooks:
            if cks['name'] == 'BAIDUID':
                cs = cks['name'] + "=" + cks['value'] + ";"
                return cs
            else:
                return 'Cookie失效'


# 随机生成IP
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


def get_icp(target):
    '''ICP备案反查域名列表'''
    api = 'https://www.beianx.cn/bacx/'
    url = api + target
    resp = s.get(url, verify=False, headers=headers, timeout=15)
    pat = r'<div><a href="/bacx/(.*?)">.*?</a></div>'
    rs = re.findall(pat, resp.text)
    for dom in rs:
        key_data={'domain': dom,'domain_from': "ICP备案查询"}
        print(key_data)
        if dom not in domains:
            domains.append(dom)
            domains_rs.append(key_data)


def get_whois(company_name):
    '''whois反查域名'''
    try:
        url = "http://whois.chinaz.com/reverse?host={0}&ddlSearchMode=2".format(company_name)
        resp = s.get(url, verify=False, headers=headers, timeout=15)
        page_pat = r'<span class="col-gray02">共(.*?)页.*?</span>'
        page = re.findall(page_pat, resp.text)
        resp.close()
        if len(page):
            i = 0
            while i < int(page[0]):
                i = i + 1
                url = "http://whois.chinaz.com/reverse?host={0}&ddlSearchMode=2&st=&startDay=&endDay=&wTimefilter=$wTimefilter&page={1}".format(
                    company_name, str(i))
                resp = s.get(url, verify=False, headers=headers, timeout=8)
                pat = r'<div class="listOther"><a href="/.*?>(.*?)</a></div>'
                dns_domains = re.findall(pat, resp.text)
                for domain in dns_domains:
                    key_data={'domain': domain,'domain_from': "whois查询"}
                    print(key_data)
                    for domrs in domains:
                        print(domrs)
                    if domain not in domains:
                        domains.append(domain)
                        domains_rs.append(key_data)
        else:
            url = "http://whois.chinaz.com/reverse?host={0}&ddlSearchMode=2&st=&startDay=&endDay=&wTimefilter=$wTimefilter&page=1".format(
                company_name)
            resp = s.get(url, verify=False, headers=headers, timeout=8)
            pat = r'<div class="listOther"><a href="/.*?>(.*?)</a></div>'
            dns_domains = re.findall(pat, resp.text)
            for domain in dns_domains:
                key_data={'domain': domain,'domain_from': "whois查询"}
                print(key_data)
                if domain not in domains:
                    domains.append(domain)
                    domains_rs.append(key_data)
                    
    except Exception as ef:
        print(str(ef))


def parse_index(content):
    tag_1 = 'window.pageData = '
    tag_2 = '/* eslint-enable */</script><script data-app'

    idx_1 = content.find(tag_1)
    idx_2 = content.find(tag_2)

    # 判断关键词区间中的JSON数据来进行匹配
    if idx_2 > idx_1:
        # 关键词提取判断，去除多余字符
        mystr = content[idx_1 + len(tag_1): idx_2].strip()
        mystr = mystr.replace("\n", "")
        mystr = mystr.replace("window.isSpider = null;", "")
        mystr = mystr.replace("window.updateTime = null;", "")
        mystr = mystr.replace(" ", "")
        mystr = mystr.replace("if(window.pageData.result.isDidiwei){window.location.href=`/login?u=${encodeURIComponent(window.location.href)}`}", "")
        mystr = mystr.replace(" ", "")
        len_str = len(mystr)
        if mystr[len_str - 1] == ';':
            mystr = mystr[0:len_str - 1]
        # 数据JSON转化
        j = json.loads(mystr)

        if len(j["result"]) > 0:
            item = j["result"]
            return item
        else:
            return None

    else:
        print("【关键词数据提取失败】")
        return None


def get_root_companyid(company_name):
    url = 'https://aiqicha.baidu.com/s?q=' + company_name
    try:
        resp = s.get(url, headers=headers, timeout=12, verify=False)
        item = parse_index(resp.text)
        root_company_id = item["resultList"][0]['pid']
        resp.close()
        print(root_company_id)
        return root_company_id
    except Exception as ex_com:
        print(str(ex_com) + '请设置Cookie并通过验证')

def get_pname(pid):
    api = 'https://aiqicha.baidu.com/company_detail_'
    api = api + str(pid)
    #rip = random_ip()
    #s.headers.update({'X-Remote-Addr': rip})
    try:
        resp = s.get(api, verify=False, timeout=15)
        item = parse_index(resp.text)
        company_name = item['entName']  # 公司名
        resp.close()
        return company_name
    except Exception as ex:
        print(ex)

def get_company_info(company_id, level, regrate, hunit):
    global pname
    api = 'https://aiqicha.baidu.com/company_detail_'
    api = api + str(company_id)
    rip = random_ip()
    s.headers.update({'X-Remote-Addr': rip})
    try:
        resp = s.get(api, verify=False, timeout=8)
        item = parse_index(resp.text)
        company_name = item['entName']  # 公司名
        website = item['website']  # 网站首页
        email = item['email']  # 邮箱
        phone = item['telephone']  # 电话号码
        resp.close()

        # 域名入缓存数据库
        if website[0:3]=='www':
            dom = website[4:]
            key_data={'domain':dom,'domain_from':"爱企查"}
            domains.append(dom)
            domains_rs.append(key_data)


        if level=='主公司':
            pname=company_name

        key_data={'company_name': company_name, 'website': website, 'email': email,'tel_phone': phone, 'level': level, 'regrate': regrate, 'hunit': hunit}
        data_list.append(key_data)
  
        #打印扫描进展（数据来源:企业组织架构缓存数据）
        print('[+]',company_name,website,email,level,regrate)
        success_company_ids.append(str(company_id))
        icp_targets.append(str(company_name))

    except Exception as x:
        print(str(x))
        error = []
        error.append(company_id)
        error.append(level)
        error.append(regrate)
        error.append(hunit)
        errors.append(error)
        
    


def get_sub_companys(pid, level):
    '''通过爱企查主公司ID,查询子公司名称和信息'''
    invest_url = "https://aiqicha.baidu.com/detail/investajax?p=1&size=110&pid={0}&f=%7b\"openStatus\":\"开业\"%7d".format(
        pid)
    hunit_url = "https://aiqicha.baidu.com/company_detail_{0}".format(pid)
    try:
        resp = s.get(invest_url, verify=False, headers=headers, timeout=8)
        invests = json.loads(resp.text)
        invests = invests['data']['list']
        resp.close()

        resp = s.get(hunit_url, verify=False, headers=headers, timeout=8)
        item = parse_index(resp.text)
        company_name = item['entName']  # 公司名

        for invest in invests:
            regrate = percent_to_int(invest['regRate'])
            if (invest['openStatus'] == '开业' and regrate > 0.2):
                if level == "二级单位":
                    sub_company_id.append(invest['pid'])
                    thread_max.acquire()
                    t = threading.Thread(target=get_company_info, args=(invest['pid'], level, invest['regRate'], pname))
                    threads.append(t)
                    t.start()
                else:
                    get_company_info(invest['pid'], level, invest['regRate'], company_name, )
    except Exception as ex:
        print(str(ex))


def Two_sub(pid):
    Referer = {'Referer':'https://aiqicha.baidu.com/company_detail_99402966917291?tab=basic'}
    s.headers.update(Referer)
    branch_url = "https://aiqicha.baidu.com/detail/branchajax?p=1&size=100&pid={0}&f=%7b\"openStatus\":\"开业\"%7d".format(
        pid)
    resp_b = s.get(branch_url, verify=False, headers=headers, timeout=8)
    branchs = json.loads(resp_b.text)
    branchs = branchs['data']['list']
    resp_b.close()
    for branch in branchs:
        if (branch['openStatus'] == '开业'):
            get_company_info(branch['pid'], "分支机构", "100%", pname, )
    get_sub_companys(pid, "二级单位")
    for j in threads:
        j.join()


def request_aiqicha(pid):
    get_company_info(pid, "主公司", "100%", "主公司")  # 获取主公司信息
    Two_sub(pid)  # 获取二级单位的信息

# 企业组织架构查询
@bp.route('/escan', methods=('GET', 'POST'))
def escan():
    s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'})
    s.headers.update({'Connection': 'close'})
    s.headers.update({'Content-Type': 'application/x-www-form-urlencoded'})
    return render_template('admin/escan.html')


# 企业组织架构数据表查询接口
@bp.route('/getinfo', methods=('GET', 'POST'))
def getinfo():
    clear_lists()
    company = request.form['company']
    if not re_dis.exists("company_info:key:" + company):
        pid = get_root_companyid(company)
        re_dis.set("company_info:key:" + company, pid, ex=3600)
    else:
        pid = re_dis.get("company_info:key:" + company)
        
    # 判断是否已经查询过（避免短时间重复查询）
    if not re_dis.exists("company_info:" + str(pid)):
        request_aiqicha(str(pid))
        re_dis.set("company_info:" + str(pid), json.dumps(data_list), ex=3600)
        company_data = json.loads(re_dis.get("company_info:" + str(pid)))
        res_data = {"code": 0, "msg": None, "count": len(company_data), "data": company_data}
    else:
        company_data = json.loads(re_dis.get("company_info:" + str(pid)))
        res_data = {"code": 0, "msg": None, "count": len(company_data), "data": company_data}
    return jsonify(res_data)


# 域名统计数据表查询接口
@bp.route('/getdomains', methods=('GET', 'POST'))
def getdomains():
    company = request.form['company']
    if not re_dis.exists("domains:key:" + company):
        re_dis.set("domains:key:" + company, company, ex=3600)
    else:
        company = re_dis.get("domains:key:" + company)
        
    # 判断是否已经查询过（避免短时间重复查询）
    if not re_dis.exists("domains:" + company):
        p_id=get_root_companyid(company)
        p_name=get_pname(p_id)

        # ICP反查域名
        for cp in icp_targets:
            get_icp(cp)
        icp_targets.clear()

        get_whois(p_name)  # whois反查域名ss
        re_dis.set("domains:" + company, json.dumps(domains_rs), ex=3600)
        
        domain_data = json.loads(re_dis.get("domains:" + company))
        res_data = {"code": 0, "msg": None, "count": len(domain_data), "data": domain_data}
    else:
        domain_data = json.loads(re_dis.get("domains:" + company))
        res_data = {"code": 0, "msg": None, "count": len(domain_data), "data": domain_data}
    domains.clear()
    domains_rs.clear()
    return jsonify(res_data)