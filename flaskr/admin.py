# coding=utf-8
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify, current_app, Flask
)
from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex
from flaskr.auth import login_required
from werkzeug.exceptions import abort
from requests.packages import urllib3
from flask_pymongo import PyMongo
import threading
import requests
import base64
import json
import time
import os
import re
import redis
import pymmh3
import dns.resolver #DNS解析
from .rules import ruleDatas  # 引入Web组件指纹库
from .vulnscan import vuln

# 消除安全请求的提示信息,增加重试连接次数
urllib3.disable_warnings()
requests.adapters.DEFAULT_RETRIES = 3

# 关闭连接，防止出现最大连接数限制错误
s = requests.Session()
s.keep_alive = False

# openssl 拒绝短键，防止SSL错误
urllib3.util.ssl_.DEFAULT_CIPHERS += 'HIGH:!DH:!aNULL'

#HTTP请求-head头
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 12_10) AppleWebKit/600.1.25 (KHTML, like Gecko) Version/12.0 Safari/1200.1.25',
}

# 设置最大线程数
thread_max = threading.BoundedSemaphore(value=500)
thread_max_dir = threading.BoundedSemaphore(value=30)

#Redis缓存数据库连接设置
pool = redis.ConnectionPool(host='127.0.0.1', port=6379, decode_responses=True, encoding='UTF-8')
re_dis = redis.Redis(connection_pool=pool)

targets = []    # 所有目标存储用list
ipc_list = []   # 本次任务所有ip-c段
proxy=None      #漏扫代理
subdomains_all=[] #所有收集到的子域名，准备拿去做CDN识别
target_ip_all=[]  #所有目标IP,用于获取IP地理位置和运营商信息

#CDN Header特征 和 目录扫描的字典（一些登录和源码泄露）
cdn_headers = ["akamai","x-cdn","x-cdn-forward","x-ser","x-cf1","x-cache","x-cached","x-cacheable","x-hit-cache","x-cache-status","x-cache-hits","x-cache-lookup","cc_cache","webcache","chinacache","x-req-id","x-requestid","cf-request-id","x-github-request-id","x-sucuri-id","x-amz-cf-id","x-airee-node","x-cdn-provider","x-fastly","x-iinfo","x-llid","sozu-id","x-cf-tsc","x-ws-request-id","fss-cache","powered-by-chinacache","verycdn","yunjiasu","skyparkcdn","x-beluga-cache-status","x-content-type-options","x-download-options","x-proxy-node","access-control-max-age","expires","cache-control",]
dir_dict=['/admin', '/manager/', '/manage', '/member', '/UpLoad', '/config', '/login', '/manager/login']
dns_dict=[]     #DNS爆破字典

cookies = dict(rememberMe='axxxxxxxxxx123456')
em = b'NTFlZjc4Y2U1YjY3M2JjMmUyOGQxYzBiNTNiZDU3Y2Y3NjAzYzExMzNhY2U0NWFmZGM1OTQ5Nzkw\nNWNiNTczYg==\n'
pik = b'NmY5YzQwMWEzOTBkYzM4NTI0YzZiOGRhNWIwNDA3ZDI1OTA3ZmYwMDA4ODBjZDAxNTUyMTIyZjhm\nM2NjYWQ1ZA==\n'

def decrypt(text):
    text = base64.decodebytes(text)
    key = '9999999999999999'.encode('utf-8')
    mode = AES.MODE_ECB
    cryptor = AES.new(key, mode)
    plain_text = cryptor.decrypt(a2b_hex(text))
    return bytes.decode(plain_text).rstrip('\0')

bp = Blueprint('admin', __name__, url_prefix='/admin') #蓝图

#首页视图
@bp.route('/')
@login_required
def index():
    return render_template('admin/admin.html')

#可视化大屏视图
@bp.route('/show_index')
@login_required
def show_index():
    apps = ''
    app_list=[]
    apps_num ='' #应用和应用的数量一一对应的列表
    #设置数据库连接参数
    app = Flask(__name__)
    with app.app_context():
        app.config['MONGO_URI'] = "mongodb://{host}:{port}/{database}".format(
        host='localhost',
        port=27017,
        database='webapp'
        )
    mongo = PyMongo(app)
    mdb=mongo.db.vulns
    vuln_num = mdb.find().count()   #漏洞总数
    new_host_num = mongo.db.new_hosts.find().count()    #新增资产总数
    all_hosts = (mongo.db.webs.find().count())+(mongo.db.subdomains.find().count())
    hosts = mongo.db.tasks.find()   #新增的资产数据->改为所有任务列表
    vulns =  mongo.db.vulns.find()      #所有漏洞数据

    tags = mongo.db.webs.find().distinct('tag') #所有应用指纹列表
    for tag in tags:
        tag = str(tag).strip()
        if tag == "-":
            tag="未知应用"
        else:
            pass
        if tag not in apps:
            app_list.append(tag)
            apps += tag+"aka"
    apps = apps.strip("aka")
    for app in app_list:
        if app == "未知应用":
            app="-"
        num_tmp = mongo.db.webs.find({'tag':app}).count()
        num_tmp =str(num_tmp).strip()
        apps_num += num_tmp+"aka"
    apps_num =apps_num.strip("aka")

    vuln_data = []
    vuln_datas =''
    vulns_name =  mongo.db.vulns.find().distinct('vuln_name')      #所有漏洞数据,列出漏洞分类
    for vuln_name in vulns_name:
        if vulns_name not in vuln_data:
            vuln_data.append(vuln_name)
    for vuln_name in vuln_data:
        count_num = mongo.db.vulns.find({'vuln_name':vuln_name}).count()    #统计某类漏洞数量
        msg = '{{"value":{0},"name":"{1}"}}aka'.format(count_num,vuln_name)
        vuln_datas += msg.strip()
    vuln_datas = vuln_datas.strip("aka")

    return render_template('admin/ksh-index.html',vuln_num=vuln_num,new_host_num=new_host_num,hosts=hosts,all_hosts =all_hosts, vulns=vulns,apps=apps,apps_num=apps_num,vuln_datas=vuln_datas)

#任务列表视图
@bp.route('/tasklist')
@login_required
def tasklist():
    target_type = request.args.get("target_type")
    mongo = PyMongo(current_app)
    if target_type == "subdomain":
        all_tasklist = mongo.db.tasks.find({'type':'subdomain'})
    elif target_type == "web":
        all_tasklist = mongo.db.tasks.find({'type':'web'})
    else:
        all_tasklist = 'None'
    return render_template('admin/tasklist.html', lists=all_tasklist,target_type=target_type)

#清空全部redis缓存
@bp.route('/clear_redis')
@login_required
def clear_redis():
    re_dis.flushall()
    return redirect(url_for('admin.index'))


# 添加任务（包括任务下发）
@bp.route('/create-task', methods=('GET', 'POST'))
def create_task():
    get_dns_dict()  #加载DNS爆破字典
    subdomains_all.clear()
    target_ip_all.clear()
    target_type=request.args.get('target_type')
    mongo = PyMongo(current_app)
    threads = []
    if request.method == 'POST':
        taskName = request.form['task_name']
        taskTargets = request.form['targets']
        error = None

        if not taskName:
            error = '任务名称不能为空'

        if error is not None:
            flash(error)
        else:
            create_tm = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())    #任务创建时间
            taskTargets = taskTargets.split('\n')  # 将字符串拆分转成列表，把扫描目标转成list列表方便单个取出下任务
            
            if taskTargets[-1]=='':
                taskTargets=taskTargets[:-1] #处理下任务时行尾的换行，防止跑出一堆未知资产
            else:
                pass
            if target_type =='subdomain':
                mongo.db.tasks.insert({'title': taskName,'target': taskTargets, 'create': create_tm, 'type': 'subdomain'})  #任务列表入库
                for target in taskTargets:
                    target=str(target).strip()
                    target = target.strip(' ')
                    subs = Subdomain(target)    #开始调用FOFA-API取子域名数据
                    certs=Subdomain_cert(target)
                    resualt = list(subs.values())
                    resualt_certs = list(certs.values())
                    data = resualt[4:]  # 数据集的数据部分
                    data_certs = resualt_certs[4:]  # cert证书取到的IP资产

                    for line in data[0]:
                        line.append(taskName)
                        line.append('-')    #初始添加Web指纹
                        tmp='DirScan\n'
                        dir_d=tmp.split('\n')
                        line.append(dir_d) #初始添加Dir目录
                        line.append('-')   #初始添加解析IP

                        #处理下host格式，转成domain
                        if line[0][0:5]=='https':
                            subdomain = str(line[0][8:])
                        else:
                            subdomain = str(line[0])
                        
                        #将子域名加入列表暂存
                        if subdomain not in subdomains_all:
                            subdomain=subdomain.strip()
                            subdomains_all.append(subdomain)

                        #先将现在的结果存入mongo数据库
                        if (line[2] != 'web') and (line[2] != 'Proxy'):
                            mongo.db.subdomains.insert({'host': subdomain, 'web_title': line[1], 'container': line[2],'task_name': line[3], 'tag': line[4],'dirscan': line[5],'ip':line[6],'geo':'-','isp':'-'})
                        else:
                            pass

                    #通过cert语法获取IP资产
                    for line in data_certs[0]:
                        line.append(taskName)
                        line.append('-')    #初始添加Web指纹
                        tmp='DirScan\n'
                        dir_d=tmp.split('\n')
                        line.append(dir_d) #初始添加Dir目录

                        #处理下host格式，转成domain
                        if line[0][0:5]=='https':
                            subdomain = str(line[0][8:])
                        elif line[0][0:4]=='http':
                            subdomain = str(line[0][7:])
                        else:
                            subdomain = str(line[0])
                        
                        #将子域名加入列表暂存
                        #将通过CERT取到的IP资产结果存入mongo数据库
                        if subdomain not in subdomains_all:
                            subdomain=subdomain.strip()
                            if ('.com' in subdomain) or ('.cn' in subdomain) or ('.net' in subdomain) or ('www.' in subdomain):
                                subdomains_all.append(subdomain)
                                mongo.db.subdomains.insert({'host': subdomain, 'web_title': line[1], 'container': line[2],'ip':line[3],'task_name': line[4], 'tag': line[5],'dirscan': line[6],'geo':'-','isp':'-'})
                            else:
                                mongo.db.subdomains.insert({'host': subdomain, 'web_title': line[1], 'container': line[2],'ip':line[3],'task_name': line[4], 'tag': line[5],'dirscan': line[6],'geo':'-','isp':'-'})
                                #ip加入list
                                ip = str(line[3]).strip()
                                if ip not in target_ip_all:
                                    target_ip_all.append(ip)
                    
                    dns_enum(target,taskName)   #调用DNS爆破模块

                #CDN识别（DNS解析,先入库完在开始识别）
                for dom in subdomains_all:
                    thread_max.acquire()
                    t = threading.Thread(target=cdn_check, args=(dom,taskName,))
                    threads.append(t)
                    t.start()
                for j in threads:
                    j.join()
                
                #IP地理位置打标签
                for ip in target_ip_all:
                    thread_max.acquire()
                    t = threading.Thread(target=get_ip_info, args=(ip,taskName,target_type,))
                    threads.append(t)
                    t.start()
                for x in threads:
                    x.join()

                #开始识别指纹               
                whatweb(taskName,target_type)

            else:
                mongo.db.tasks.insert({'title': taskName,'target': taskTargets, 'create': create_tm, 'type': 'web'})
                for target in taskTargets:
                    target = target.rstrip(' ')
                    webs = Webs(target)
                    resualt = list(webs.values())
                    data = resualt[4:]  # 数据集的数据部分
                    for line in data[0]:
                        line.append(taskName)
                        line.append('-')
                        tmp='DirScan\n'
                        dir_d=tmp.split('\n')
                        line.append(dir_d)

                        ip=str(line[3]).strip()
                        if ip not in target_ip_all:
                            target_ip_all.append(ip)
                        
                        if (line[4] != 'web') and (line[4] != 'Proxy'):
                            mongo.db.webs.insert({'host': line[0], 'web_title': line[1],'container': line[2], 'ip':ip, 'task_name': line[4], 'tag': line[5],'dirscan': line[6],'geo':'-','isp':'-'})
                        else:
                            pass
                
                #IP地理位置打标签
                for ip in target_ip_all:
                    thread_max.acquire()
                    t = threading.Thread(target=get_ip_info, args=(ip,taskName,target_type,))
                    threads.append(t)
                    t.start()
                for x in threads:
                    x.join()
                
                #开始识别指纹 
                whatweb(taskName,target_type)
                    
    return render_template('admin/create-task.html')


# 删除任务
@bp.route('/<string:taskName>/task-del', methods=('GET', 'POST'))
@login_required
def task_del(taskName):
    mongo = PyMongo(current_app)
    t_type =  mongo.db.tasks.find({'title': taskName}, {'type': 1, '_id': 0}).distinct('type')
    if t_type == 'subdomain':
        mongo.db.subdomains.remove({'task_name': taskName})
    else:
        mongo.db.webs.remove({'task_name': taskName})
    mongo.db.tasks.remove({'title': taskName})

    return redirect(url_for('admin.tasklist',target_type=t_type))

# 删除漏洞
@bp.route('/<string:host>/vuln_del', methods=('GET', 'POST'))
@login_required
def vuln_del(host):
    mongo = PyMongo(current_app)
    mongo.db.vulns.remove({'host': host})

    return redirect(url_for('admin.res_vuln'))

# 子域名列表
@bp.route('/<string:taskName>/subdomain-list', methods=('GET', 'POST'))
@login_required
def subdomain_list(taskName):
    mongo = PyMongo(current_app)
    if taskName is not None:
        tags = mongo.db.subdomains.find({'task_name': taskName}, {'tag': 1, '_id': 0}).distinct('tag')  # 只查tag
        if request.method == 'POST':
            web_tag = request.form['webtag']
            if not web_tag:
                lists = mongo.db.subdomains.find({'task_name': taskName})
            else:
                lists = mongo.db.subdomains.find({'task_name': taskName, 'tag': web_tag})
            return render_template('admin/subdomain-list.html', lists=lists, tags=tags, taskname=taskName, web_tag=web_tag,target_type='subdomain')
        else:
            lists = mongo.db.subdomains.find({'task_name': taskName})
            return render_template('admin/subdomain-list.html', lists=lists, tags=tags, taskname=taskName,target_type='subdomain')
    else:
        return render_template('admin/subdomain-list.html')

#从FOFA取子域名数据
def Subdomain(rootdomain):
    cmd = 'domain="{dom}"'.format(dom=rootdomain)
    fofa_query = base64.b64encode(cmd.encode('utf-8')).decode("utf-8")
    fofa_size = "10000"
    fields = "host,title,server"
    api = "https://fofa.so/api/v1/search/all?email={email}&key={key}&qbase64={query}&size={size}&fields={fields}".format(email=eemmail, key=kkee, query=fofa_query, size=fofa_size, fields=fields)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36'
    }
    rs = s.get(api, verify=False, headers=headers,timeout=20)
    rs_text = rs.text
    res = json.loads(rs_text)
    print('[*] 从FOFA获取数据-根域名为: {0}'.format(rootdomain))
    print(res['results'])
    error = res['error']
    if error:
        errmsg = res['errmsg']
        if '401 Unauthorized' in errmsg:
            print('用户名或API 无效！')
            exit(1)
    else:
        return (res)

#根据domain的cert证书从FOFA取IP资产
def Subdomain_cert(rootdomain):
    cmd = 'cert="{dom}"'.format(dom=rootdomain)
    fofa_query = base64.b64encode(cmd.encode('utf-8')).decode("utf-8")
    fofa_size = "10000"
    fields = "host,title,server,ip"
    api = "https://fofa.so/api/v1/search/all?email={email}&key={key}&qbase64={query}&size={size}&fields={fields}".format(email=eemmail, key=kkee, query=fofa_query, size=fofa_size, fields=fields)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36'
    }
    rs = s.get(api, verify=False, headers=headers,timeout=20)
    rs_text = rs.text
    res = json.loads(rs_text)
    print('[*] 从FOFA获IP资产数据-证书根域名为: {0}'.format(rootdomain))
    print(res['results'])
    error = res['error']
    if error:
        errmsg = res['errmsg']
        if '401 Unauthorized' in errmsg:
            print('用户名或API 无效！')
            exit(1)
    else:
        return (res)

#加载DNS字典
def get_dns_dict():
    dns_dict.clear()
    with open('data/dns_dict.txt','r',encoding='utf-8') as f:
        lines=f.readlines()
        for line in lines:
            line=line.strip('\n')
            dns_dict.append(line)

#DNS爆破任务入口
def dns_enum(rootdomain,task_name):
    threads=[]
    for domain in dns_dict:
        thread_max.acquire()
        domain=str(domain).strip('\n')
        domain=domain+'.'+rootdomain
        t = threading.Thread(target=dns_enum_start, args=(domain,task_name,))
        threads.append(t)
        t.start()
    for j in threads:
        j.join()

#DNS爆破任务实际work
def dns_enum_start(domain,task_name):
    app = Flask(__name__)
    with app.app_context():
        app.config['MONGO_URI'] = "mongodb://{host}:{port}/{database}".format(
            host='localhost',
            port=27017,
            database='webapp'
        )
    mongo = PyMongo(app)
    try:
        answer = dns.resolver.resolve(domain,'A', raise_on_no_answer=False)
        if answer.rrset is not None:
            print('[+] DNS爆破命中：'+domain+"＜（＾－＾）＞")
            if domain not in subdomains_all:
                domain=domain.strip()
                subdomains_all.append(domain)
                mongo.db.subdomains.insert({'host': domain, 'web_title': '-', 'container': '-','task_name': task_name, 'tag': '-','dirscan': '-','ip':'-','geo':'-','isp':'-'})
        else:
            print('[-] DNS爆破无果,子域名不存在 '+domain)
    except Ellipsis as ex:
        print("[+] 子域名不存在\t"+domain)
    finally:
        mongo = None
        thread_max.release()


#DNS解析识别CDN
def cdn_check(dom,task_name):
    dom=str(dom)
    dom=dom.strip()
    app = Flask(__name__)
    with app.app_context():
        app.config['MONGO_URI'] = "mongodb://{host}:{port}/{database}".format(
            host='localhost',
            port=27017,
            database='webapp'
        )
    mongo = PyMongo(app)

    try:
        answer = dns.resolver.resolve(dom,'A', raise_on_no_answer=False)
        if answer.rrset is not None:
            dns_cname = str(answer.canonical_name) #这条能输出CNAME的名称
            dns_cname=dns_cname.strip('.')
            #dom=dom.strip('.')
            if dns_cname == dom:
                dns_rs_A=str(answer.rrset)
                dns_A = dns_rs_A.split(' ',4)
                dns_ip=dns_A[4]
                
                mongo.db.subdomains.update({'host': dom,'task_name':task_name}, {'$set': {'ip':str(dns_ip)}})
                print('[+] CDN识别中 '+dom,dns_ip,'A记录')

                ip=dns_ip.strip()
                if ip not in target_ip_all:
                    target_ip_all.append(ip)
                else:
                    pass
            else:
                mongo.db.subdomains.update({'host': dom,'task_name':task_name}, {'$set':{'ip':'CDN'}})
                print('[+] CDN识别中 '+dom,'CDN')
        else:
            print('[+] CDN识别中 '+dom+'DNS解析失败')
            mongo.db.subdomains.update({'host':dom }, {'$set': {'ip':'DNS解析失败'}})

    except Exception as ex:
        print('[+] DNS识别中 '+'查询出错: '+str(ex))
        mongo.db.subdomains.update({'host': dom}, {'$set': {'ip':'DNS解析出错'}})
    finally:
        thread_max.release()

#获取IP地理位置
def get_ip_info(ip,task_name,target_type):
    app = Flask(__name__)
    with app.app_context():
        app.config['MONGO_URI'] = "mongodb://{host}:{port}/{database}".format(
            host='localhost',
            port=27017,
            database='webapp'
        )
    mongo = PyMongo(app)
    #淘宝IP地址库接口
    try:
        r = s.get('https://ip.taobao.com/outGetIpInfo?ip=%s' %ip)              
        if  r.json()['code'] == 0 :
            i = r.json()['data']
            country = i['country']  #国家
            region = i['region']    #省份
            city = i['city']        #城市
            isp = i['isp']          #运营商
            geo = country+' '+region+' '+city
            # print(ip)
            # print('地理位置: '+ geo)
            # print('运营商: '+isp+'\n')
            if target_type == 'subdomain':
                mongo.db.subdomains.update_many({'ip': ip,'task_name': task_name}, {'$set': {'geo':geo,'isp':isp}}) #update_many 更新多条记录
            else:
                mongo.db.webs.update_many({'ip': ip,'task_name': task_name}, {'$set': {'geo':geo,'isp':isp}})
            
        elif r.json()['code'] == 4:
            get_ip_info(ip,task_name,target_type) #API查询限制吞吐量，递归查询多试几次保证IP全查完
        else:
            mongo.db.webs.update_many({'ip': ip,'task_name': task_name}, {'$set': {'geo':'查不到','isp':'查不到'}})
    except Exception as exs:
        geo_status = mongo.db.tasks.find({'ip': ip,'task_name': task_name}, {'geo': 1, '_id': 0}).distinct('geo')
        # print(geo_status)
        if geo_status == "查询异常":
            get_ip_info(ip,task_name,target_type)
        elif geo_status =='-':
            mongo.db.webs.update_many({'ip': ip,'task_name': task_name}, {'$set': {'geo':'查询异常','isp':'查询异常'}})
        else:
            pass

    finally:
        mongo.db.client.close()
        mongo = None
        thread_max.release()


# Web资产列表（IP资产）
@bp.route('/<string:taskName>/web-list', methods=('GET', 'POST'))
@login_required
def web_list(taskName):
    mongo = PyMongo(current_app)
    if taskName is not None:
        tags = mongo.db.webs.find({'task_name': taskName}, {'tag': 1, '_id': 0}).distinct('tag')  # 只查tag
        if request.method == 'POST':
            web_tag = request.form['webtag']
            if not web_tag:
                lists = mongo.db.webs.find({'task_name': taskName})
            else:
                lists = mongo.db.webs.find({'task_name': taskName, 'tag': web_tag})
            return render_template('admin/web-list.html', lists=lists, tags=tags, taskname=taskName, web_tag=web_tag,target_type='web')
        else:
            lists = mongo.db.webs.find({'task_name': taskName})
            return render_template('admin/web-list.html', lists=lists, tags=tags, taskname=taskName,target_type='web')
    else:
        return render_template('admin/web-list.html')

#从FOFA取IP资产
def Webs(ipc):
    cmd = 'ip="' + ipc + '" && (status_code="200" || status_code=="302" || status_code=="302" || status_code=="301" || status_code=="403" || status_code=="404")'
    #cmd='ip="' + ipc + '"'
    fofa_query = base64.b64encode(cmd.encode('utf-8')).decode("utf-8")
    fofa_size = "10000"
    fields = "host,title,server,ip"
    api = "https://fofa.so/api/v1/search/all?email={email}&key={key}&qbase64={query}&size={size}&fields={fields}".format(
        email=eemmail, key=kkee, query=fofa_query, size=fofa_size, fields=fields)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36'
    }
    r = requests.get(api, verify=False, headers=headers)
    rs_text = r.text
    res = json.loads(rs_text)

    print('\n'+'='*50)
    print('[*] 从FOFA获取IP资产数据-IP为: {0}'.format(ipc))
    print('='*50)
    print(res['results'])


    error = res['error']
    if error:
        errmsg = res['errmsg']
        if '401 Unauthorized' in errmsg:
            print('用户名或API 无效！')
            exit(1)
    else:
        return (res)

# ICON_HASH计算-web页面
@bp.route('/icohash', methods=["GET", "POST"])
def icohash():
    return render_template('admin/icohash.html')

# ICON_HASH数据API接口
@bp.route('/get_icohash', methods=["POST", "GET"])
def get_icohash():
    ico_url = request.form['icourl']
    if not re_dis.exists("fofa_icon:key:" + str(ico_url)):
        i_hash = getfaviconhash(ico_url)
        re_dis.set("fofa_icon:key:" + str(ico_url), i_hash, ex=3600)
    else:
        i_hash = re_dis.get("fofa_icon:key:" + str(ico_url))
    print(ico_url,i_hash)
        
    # 判断是否已经查询过（避免短时间重复查询）
    if not re_dis.exists("fofa_icon:" + str(i_hash)):
        icon_hash = 'icon_hash="{0}"'.format(str(i_hash))
        ico_webs = iconhash_search(icon_hash)
        data_list = []
        for line in ico_webs['results']:
            key_list = ['host', 'ip', 'port', 'web_title', 'container', 'country', 'province', 'city']
            key_data = zip(key_list, line)
            key_data=dict(key_data)
            ihash={'i_hash':i_hash}
            key_data.update(ihash)
            data_list.append(key_data)
        re_dis.set("fofa_icon:" + str(i_hash), json.dumps(data_list), ex=3600)
    icon_data = json.loads(re_dis.get("fofa_icon:" + str(i_hash)))

    res_data = {"code": 0, "msg": None, "count": len(icon_data), "data": icon_data}
    return jsonify(res_data)

#ICON_HASH格式转换
def change_format(content):
    count = len(content) % 76
    items = re.findall(r".{76}", content)
    final_item = content[-count:]
    items.append(final_item)
    return "{0}\n".format("\n".join(items))


# 获取远程 favicon hash信息
def getfaviconhash(url):
    try:
        resp = s.get(url, verify=False)
        if "image" in resp.headers['Content-Type']:
            favicon = base64.b64encode(resp.content).decode('utf-8')
            hash = pymmh3.hash(change_format(favicon))
        else:
            hash = None
        resp.close()
    except Exception as ex:
        print("[!] ICON Request Error"+"\n"+str(ex))
        hash = None
    return hash

# 根据ICON_HASH 从FOFA匹配资产
def iconhash_search(icon_hash):
    cmd = icon_hash
    fofa_query = base64.b64encode(cmd.encode('utf-8')).decode("utf-8")
    fofa_size = "10000"
    fields = "host,ip,port,title,server,country,province,city"
    api = "https://fofa.so/api/v1/search/all?email={email}&key={key}&qbase64={query}&size={size}&fields={fields}".format(
        email=eemmail, key=kkee, query=fofa_query, size=fofa_size, fields=fields)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36'
    }
    r = requests.get(api, verify=False, headers=headers)
    rs_text = r.text
    res = json.loads(rs_text)
    error = res['error']
    if error:
        errmsg = res['errmsg']
        if '401 Unauthorized' in errmsg:
            print('用户名或API 无效！')
            exit(1)
    else:
        return (res)

# Title关键字Web页面
@bp.route('/title_k', methods=["GET", "POST"])
def title_k():
    return render_template('admin/assets-keyword.html')

# title关键字查询资产列表-数据查询接口
@bp.route('/get_keywords', methods=["POST", "GET"])
def get_keywords():
    keyword = request.form['keyw']
    keyword=str(keyword)
    # 判断是否已经查询过（避免短时间重复查询）
    if not re_dis.exists("title_keyword:key:" + keyword):
        re_dis.set("title_keyword:key:" + keyword, keyword, ex=3600)
        key_webs = keywords(keyword)
        data_list = []
        for line in key_webs['results']:
            key_list = ['host', 'ip', 'port', 'web_title', 'container', 'country', 'province', 'city']
            key_data = zip(key_list, line)
            key_data=dict(key_data)
            data_list.append(key_data)
        re_dis.set("title_keyword:key:" + keyword, json.dumps(data_list), ex=3600)
        webkey_data = json.loads(re_dis.get("title_keyword:key:" + keyword))
        res_data = {"code": 0, "msg": None, "count": len(webkey_data), "data": webkey_data}
    else:
        webkey_data = json.loads(re_dis.get("title_keyword:key:" + keyword))
        res_data = {"code": 0, "msg": None, "count": len(webkey_data), "data": webkey_data}
    return jsonify(res_data)


#从FOFA取title关键字数据
def keywords(keywd):
    cmd = 'title="' + keywd + '" && (status_code="200" || status_code=="302" || status_code=="403" || status_code=="301" || status_code=="502" || status_code=="404")'
    fofa_query = base64.b64encode(cmd.encode('utf-8')).decode("utf-8")
    fofa_size = "10000"
    fields = "host,ip,port,title,server,country,province,city"
    api = "https://fofa.so/api/v1/search/all?email={email}&key={key}&qbase64={query}&size={size}&fields={fields}".format(
        email=eemmail, key=kkee, query=fofa_query, size=fofa_size, fields=fields)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36'
    }
    r = requests.get(api, verify=False, headers=headers)
    rs_text = r.text
    res = json.loads(rs_text)
    error = res['error']
    if error:
        errmsg = res['errmsg']
        if '401 Unauthorized' in errmsg:
            print('用户名或API 无效！')
            exit(1)
    else:
        return (res)


# 修改密码
@bp.route('/<int:uid>/pass-edit', methods=('GET', 'POST'))
@login_required
def pass_edit(uid):
    if request.method == 'POST':
        password = request.form['password']
        error = None

        if not password:
            error = '密码不能为空'

        if error is not None:
            flash(error)
        else:
            mongo = PyMongo(current_app)
            mongo.db.user.update({'uid': uid}, {'$set': {'password': password}})

    return render_template('admin/password-edit.html')


# 导出URL
@bp.route('/<string:taskName>/export_url', methods=('GET', 'POST'))
def export_url(taskName):
    all_url = []
    mongo = PyMongo(current_app)
    web_tag = request.args.get("web_tag")
    target_type = request.args.get("target_type")
    if target_type == 'web':
        mdb=mongo.db.webs
    else:
        mdb=mongo.db.subdomains
    if web_tag:
        URLS = mdb.find({'task_name': taskName, 'tag': web_tag}, {'host': 1, '_id': 0})
    else:
        URLS = mdb.find({'task_name': taskName}, {'host': 1, '_id': 0})
    for url in URLS:
        url = url['host'].rstrip()
        if (url[0:4] == "http"):
            url = url
        else:
            url = "http://" + url
        if url not in all_url:
            all_url.append(url)
    return render_template('admin/exp-url.html', all_url=all_url)

#目录扫描
def dirScan(dir_url,target_type,host,taskName):
    app = Flask(__name__)
    with app.app_context():
        app.config['MONGO_URI'] = "mongodb://{host}:{port}/{database}".format(
            host='localhost',
            port=27017,
            database='webapp'
        )
        try:
            mongo = PyMongo(app)
            if target_type=='web':
                mdbd=mongo.db.webs
            else:
                mdbd=mongo.db.subdomains
            resp_dir = s.get(dir_url,timeout=10, verify=False)
            resp_dir.close()
            dir_status = resp_dir.status_code
            if (dir_status == 200 or dir_status == 301 or dir_status == 302):
                # print(dir_url + '   命中目录, 请验证！！！')
                old_dir=mdbd.find_one({'host': host, 'task_name': taskName},{'dirscan': 1, '_id': 0})
                if old_dir['dirscan'][0]=='DirScan':
                    tmp=dir_url+'\n'
                    dir_list = tmp.split('\n')
                    mdbd.update({'host': host, 'task_name': taskName}, {'$set': {'dirscan': dir_list}})
                elif len(old_dir['dirscan']) > 5:
                    bad_dir = '-'.split('\n')
                    mdbd.update({'host': host, 'task_name': taskName}, {'$set': {'dirscan': bad_dir}})
                else:
                    if old_dir['dirscan'][0]=='-':
                        # print(dir_url+" 属于误报XXX")
                        pass
                    else:
                        old_dir['dirscan'].append(dir_url)
                        mdbd.update({'host': host, 'task_name': taskName}, {'$set': {'dirscan': old_dir['dirscan']}})
            else:
                pass
        except Exception as direx:
            print(dir_url+' '+str(direx))
        finally:
            mongo.db.client.close()
            mongo = None
            thread_max_dir.release()

#指纹识别任务下发
def whatweb(taskName,tar_type):
    mongo = PyMongo(current_app)
    if tar_type == 'web':
        hosts = mongo.db.webs.find({'task_name': taskName}, {'host': 1, '_id': 0})
    elif tar_type == 'subdomain':
        hosts = mongo.db.subdomains.find({'task_name': taskName}, {'host': 1, '_id': 0})
    threads = []
    for hs in hosts:
        if hs['host'][0:4] == 'http':
            host = hs['host']
            url = hs['host']
        else:
            host = hs['host']
            url = "http://" + hs['host']
        thread_max.acquire()
        t = threading.Thread(target=resqweb, args=(url, host, taskName,tar_type,))
        threads.append(t)
        t.start()
    for j in threads:
        j.join()

# Web指纹识别
def resqweb(url, host, taskName,target_type):
    threads_dir=[] #目录扫描线程池
    ico_url=url+'/favicon.ico'
    app = Flask(__name__)
    with app.app_context():
        app.config['MONGO_URI'] = "mongodb://{host}:{port}/{database}".format(
            host='localhost',
            port=27017,
            database='webapp'
        )
        try:
            mongo = PyMongo(app)
            if target_type=='web':
                mdb=mongo.db.webs
            else:
                mdb=mongo.db.subdomains

            tags = mdb.find_one({'task_name': taskName, 'host': host}, {'tag': 1, '_id': 0})
            tag=tags['tag'] 

            #Header和Body匹配
            resp = s.get(url, cookies=cookies, timeout=20, verify=False,headers=headers)
            resp.close()
            resp_err = s.get(url + '/tt', timeout=20, verify=False,headers=headers)     # 请求不存在的页面去让页面报错
            resp_err.close()

            #ICON_HASH匹配
            ico_hash = getfaviconhash(ico_url)
            if ico_hash is not None:
                icon_hash=str(ico_hash)
            else:
                icon_hash='12121212'    #肯定不存在的ICON_HASH

            for app_name, app_info in ruleDatas.items():
                finger = app_info['finger']
                hitHeads = re.findall(finger, str(resp.headers))
                hitBody = re.findall(finger, str(resp.text))
                hitBody_err = re.findall(finger, resp_err.text)
                hiticon = re.findall(finger,icon_hash)

                if hitHeads or hitBody or hitBody_err or hiticon:
                    if tag == "-":
                        print("[CMS组件信息]-{0}：{1}".format(app_name,url) +'\tHead头匹配到 '+str(hitHeads)+'\tBody匹配到 '+str(hitBody)+'\tEorror匹配到 '+str(hitBody_err)+'\tICON匹配到 '+str(hiticon))
                        mdb.update({'host': host, 'task_name': taskName}, {'$set': {'tag': app_name}})
                        break
                    elif app_name.lower() not in str(tag).lower():
                        print("[CMS组件信息]-{0}：{1}".format(app_name,url) +'\tHead头匹配到 '+str(hitHeads)+'\tBody匹配到 '+str(hitBody)+'\tEorror匹配到 '+str(hitBody_err)+'\tICON匹配到 '+str(hiticon))
                        mdb.update({'host': host, 'task_name': taskName}, {'$set': {'tag': str(tag)+','+str(app_name)}})
                        break
                    else:
                        pass
                else:
                    pass    #不能改
            #print("[x] 未识别: " + url)
            
            #目录扫描
            for dd in dir_dict:
                dir_url=url+dd
                thread_max_dir.acquire()
                t_dir = threading.Thread(target=dirScan, args=(dir_url,target_type,host,taskName,))
                threads_dir.append(t_dir)
                t_dir.start()
            for ddx in threads_dir:
                ddx.join()

        except Exception as exs:
            mdb.update({'host': host, 'task_name': taskName}, {'$set': {'tag': '连接失败'}})  
            # print("[x] 连接失败: " + url)
        finally:
            mongo.db.client.close()
            mongo = None
            thread_max.release()

# POC插件漏扫
@bp.route('/poc-scan', methods=('GET', 'POST'))
@login_required
def poc_scan():
    poc_list =''
    for app_name, app_info in ruleDatas.items():
        cms = app_info['value']
        msg = '{{"value":"{0}","title":"{1}"}}aka'.format(cms,app_name)
        poc_list += msg.strip()
    poc_list = poc_list.strip("aka")

    return render_template('admin/poc-scan.html',poc_list=poc_list)

# 漏洞统计
@bp.route('/resforvulns', methods=('GET', 'POST'))
@login_required
def res_vuln():
    mongo = PyMongo(current_app)
    mdb=mongo.db.vulns
    lists = mdb.find()
    return render_template('admin/resforvulns.html',lists=lists)

#设置代理
@bp.route('/proxy_set', methods=('GET', 'POST'))
@login_required
def proxy_set():
    global proxy
    if request.method == 'POST':
        proxy_url = request.form['proxy_url']

        if not proxy_url:
            proxy=None
        else:
            proxy =proxy_url

    return render_template('admin/proxy-set.html')

# 漏扫调用
def poc_scan(app_name,proxy,url):
    vuln.vuln_scan(app_name,proxy,url)

# 漏扫结果接口
@bp.route('/get_vulnable', methods=["POST", "GET"])
@login_required
def get_vulnable():
    vuln_targets = request.form['vuln_targets']
    app_name=request.form['app_name']
    app_name = str(app_name).split("undefined",1)[1].strip(",")
    app_name = app_name.split(",", 1)[0]
    #print(app_name) #转成以逗号分隔的字符串

    #写入到urls.txt文件
    with open('flaskr/vulnscan/urls.txt','w',encoding='utf-8') as f:
        f.write(vuln_targets)
        f.close()
    url=None
    poc_scan(app_name,proxy,None)    #开始扫描

    re_dis.set("vulns", json.dumps(vuln.vuln_list), ex=3600)
    vuln_data = json.loads(re_dis.get("vulns"))
    res_data = {"code": 0, "msg": None, "count": len(vuln_data), "data": vuln_data}

    return jsonify(res_data)

# 系统设置
@bp.route('/sysconf', methods=('GET', 'POST'))
@login_required
def sysconf():
    mongo = PyMongo(current_app)
    hookdb=mongo.db.http_hook

    old_hook = hookdb.find()
    old_hook = old_hook[0]['hook']

    if request.method == 'POST':
        new_hook = request.form['dd_hook']
        hookdb.update({'hook':old_hook},{'$set':{'hook':new_hook}})
    else:
        pass
    hook = hookdb.find()
    hook = hook[0]['hook']
    return render_template('admin/sysconf.html',hook=hook)

eemmail = decrypt(em)
kkee = decrypt(pik)