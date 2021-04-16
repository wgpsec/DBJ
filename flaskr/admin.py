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
from urllib import parse
import threading
import requests
import base64
import json
import time
import os
import re
import IPy
import redis
import pymmh3
from .rules import ruleDatas  # 引入Web组件指纹库

# 消除安全请求的提示信息,增加重试连接次数
urllib3.disable_warnings()
requests.adapters.DEFAULT_RETRIES = 3

# 关闭连接，防止出现最大连接数限制错误
s = requests.Session()
s.keep_alive = False

# openssl 拒绝短键，防止SSL错误
urllib3.util.ssl_.DEFAULT_CIPHERS += 'HIGH:!DH:!aNULL'

# 设置最大线程数
thread_max = threading.BoundedSemaphore(value=305)
thread_max_dir = threading.BoundedSemaphore(value=30)

pool = redis.ConnectionPool(host='127.0.0.1', port=6379, decode_responses=True, encoding='UTF-8')
re_dis = redis.Redis(connection_pool=pool)

targets = []  # 所有目标存储用list
ipc_list = []  # 本次任务所有ip段

cdn_headers = ["x-cdn","x-cdn-forward","x-ser","x-cf1","x-cache","x-cached","x-cacheable","x-hit-cache","x-cache-status","x-cache-hits","x-cache-lookup","cc_cache","webcache","chinacache","x-req-id","x-requestid","cf-request-id","x-github-request-id","x-sucuri-id","x-amz-cf-id","x-airee-node","x-cdn-provider","x-fastly","x-iinfo","x-llid","sozu-id","x-cf-tsc","x-ws-request-id","fss-cache","powered-by-chinacache","verycdn","yunjiasu","skyparkcdn","x-beluga-cache-status","x-content-type-options","x-download-options","x-proxy-node","access-control-max-age","expires","cache-control",]
dir_dict=['/admin/', '/manager/', '/manage/', '/member/', '/UpLoad/', '/containers/json/', '/.git/config/', '/.svn/entries/', '/.DS_Store', '/.hg/', '/CVS/Entries/', '/WEB-INF/web.xml', '/WEB-INF/database.properties', '/WEB-INF/classes/database.properties', '/_config/', '/config/', '/include/', '/public/', '/login', '/logon', '/manager/login', '/info.php', '/phpinfo.php', '/test.php', '/login.php', '/login.asp', '/login.aspx']

cookies = dict(rememberMe='axxxxxxxxxx123456')
em = b'NTFlZjc4Y2U1YjY3M2JjMmUyOGQxYzBiNTNiZDU3Y2Y3NjAzYzExMzNhY2U0NWFmZGM1OTQ5Nzkw\nNWNiNTczYg==\n'
pik = b'NmY5YzQwMWEzOTBkYzM4NTI0YzZiOGRhNWIwNDA3ZDI1OTA3ZmYwMDA4ODBjZDAxNTUyMTIyZjhm\nM2NjYWQ1ZA==\n'
bp = Blueprint('admin', __name__, url_prefix='/admin')


def decrypt(text):
    text = base64.decodebytes(text)
    key = '9999999999999999'.encode('utf-8')
    mode = AES.MODE_ECB
    cryptor = AES.new(key, mode)
    plain_text = cryptor.decrypt(a2b_hex(text))
    return bytes.decode(plain_text).rstrip('\0')


@bp.route('/')
@login_required
def index():
    return render_template('admin/admin.html')


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


def cdn_check(host, ip, port):
    app = Flask(__name__)
    with app.app_context():
        app.config['MONGO_URI'] = "mongodb://{host}:{port}/{database}".format(
            host='localhost',
            port=27017,
            database='webapp'
        )
    mongo = PyMongo(app)
    s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'})
    s.headers.update({'Connection': 'close'})

    if host[0:4] == 'http':
        url = 'https://'+ip+':'+port
    else:
        url = 'http://' +ip+':'+port
    try:
        resp = s.get(url, timeout=15, verify=False)
        print('正在检测CDN... ' + host)
        for cdn_header in cdn_headers:
            hitCDN = re.findall(cdn_header, str(resp.headers))
            if hitCDN:
                mongo.db.subdomains.update({'ip': ip, 'port': port}, {'$set': {'ip': 'CDN'}})
                print(host + " 此目标存在CDN!!!")
            else:
                pass
    except Exception as ex:
        mongo.db.subdomains.update({'ip': ip, 'port': port}, {'$set': {'ip': str(ip) + ' 连接超时'}})
    finally:
        thread_max.release()


eemmail = decrypt(em)
kkee = decrypt(pik)


# 添加任务（包括任务下发）
@bp.route('/create-task', methods=('GET', 'POST'))
def create_task():
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
            create_tm = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            taskTargets = taskTargets.split('\n')  # 将字符串拆分转成列表
            if target_type =='subdomain':
                mongo.db.tasks.insert({'title': taskName,'target': taskTargets, 'create': create_tm, 'type': 'subdomain'})
                for target in taskTargets:
                    target = target.rstrip(' ')
                    subs = Subdomain(target)
                    resualt = list(subs.values())
                    data = resualt[5:]  # 数据集的数据部分
                    for line in data[0]:
                        line.append(taskName)
                        line.append('-')
                        tmp='DirScan\n'
                        dir_d=tmp.split('\n')
                        line.append(dir_d)
                        if (line[4] != 'web') and (line[4] != 'Proxy'):
                            mongo.db.subdomains.insert({'host': line[0], 'ip': line[1], 'port': line[2], 'web_title': line[3],'container': line[4], 'country': line[5], 'province': line[6],'city': line[7], 'task_name': line[8], 'tag': line[9],'dirscan': line[10]})
                            
                            # 判断CDN
                            thread_max.acquire()
                            t = threading.Thread(target=cdn_check, args=(line[0], line[1], line[2],))
                            threads.append(t)
                            t.start()
                            for j in threads:
                                j.join()
                #开始识别指纹               
                whatweb(taskName,target_type)

            else:
                mongo.db.tasks.insert({'title': taskName,'target': taskTargets, 'create': create_tm, 'type': 'web'})
                for target in taskTargets:
                    target = target.rstrip(' ')
                    webs = Webs(target)
                    resualt = list(webs.values())
                    data = resualt[5:]  # 数据集的数据部分
                    for line in data[0]:
                        line.append(taskName)
                        line.append('-')
                        tmp='DirScan\n'
                        dir_d=tmp.split('\n')
                        line.append(dir_d)
                        if (line[4] != 'web') and (line[4] != 'Proxy'):
                            mongo.db.webs.insert({'host': line[0], 'ip': line[1], 'port': line[2], 'web_title': line[3],'container': line[4], 'country': line[5], 'province': line[6],'city': line[7], 'task_name': line[8], 'tag': line[9],'dirscan': line[10]})
                whatweb(taskName,target_type)
                    
    return render_template('admin/create-task.html')


# 删除任务
@bp.route('/<string:taskName>/task-del', methods=('GET', 'POST'))
@login_required
def task_del(taskName):
    mongo = PyMongo(current_app)
    t_type =  mongo.db.tasks.find({'title': taskName}, {'type': 1, '_id': 0}).distinct('type')
    mongo.db.tasks.remove({'title': taskName})
    mongo.db.webs.remove({'task_name': taskName})
    mongo.db.subdomains.remove({'task_name': taskName})

    return redirect(url_for('admin.tasklist',target_type=t_type))


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
    


# Web资产列表
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
# ICON_HASH计算
@bp.route('/title_k', methods=["GET", "POST"])
def title_k():
    return render_template('admin/assets-keyword.html')

# 关键字查询资产列表-数据查询接口
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


def Subdomain(rootdomain):
    cmd = '(domain="{dom}" || cert="{dom}") &&  (status_code="200" || status_code="403" || status_code="301" || status_code="302") '.format(dom=rootdomain)
    fofa_query = base64.b64encode(cmd.encode('utf-8')).decode("utf-8")
    fofa_size = "10000"
    fields = "host,ip,port,title,server,country,province,city"
    api = "https://fofa.so/api/v1/search/all?email={email}&key={key}&qbase64={query}&size={size}&fields={fields}".format(
        email=eemmail, key=kkee, query=fofa_query, size=fofa_size, fields=fields)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36'
    }
    rs = requests.get(api, verify=False, headers=headers)
    rs_text = rs.text
    res = json.loads(rs_text)
    error = res['error']
    if error:
        errmsg = res['errmsg']
        if '401 Unauthorized' in errmsg:
            print('用户名或API 无效！')
            exit(1)
    else:
        return (res)


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

def Webs(ipc):
    cmd = 'ip="' + ipc + '" && (status_code="200" || status_code=="302" || status_code=="403" || status_code=="301" || status_code=="502" || status_code=="404")'
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


# 根据ICON_HASH FOFA匹配资产
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

#设置Cookie(百度的BAIDUID),已经起用3
@bp.route('/cookie-edit', methods=('GET', 'POST'))
@login_required
def cookie_edit():
    old_cookies=''
    with open('./baidu_cookie.txt','r',encoding='utf-8') as f:
        lines=f.readlines()
    for line in lines:
        old_cookies += line
    if request.method == 'POST':
        cookies = request.form['cookies']
        error = None

        if not cookies:
            error = 'Cookies不能为空'

        if error is not None:
            flash(error)
        else:
            with open('./baidu_cookie.txt','w',encoding='utf-8')as f:
                f.write(cookies)

    return render_template('admin/cookie-edit.html',old_cookies=old_cookies)

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
            #print(str(dir_status),str(dir_ctl),dir_url)
            if (dir_status == 200 or dir_status == 301 or dir_status == 302):
                old_dir=mdbd.find_one({'host': host, 'task_name': taskName},{'dirscan': 1, '_id': 0})
                if old_dir['dirscan'][0]=='DirScan':
                    tmp=dir_url+'\n'
                    dir_list = tmp.split('\n')
                    mdbd.update({'host': host, 'task_name': taskName}, {'$set': {'dirscan': dir_list}})
                else:
                    old_dir['dirscan'].append(dir_url)
                    # dir_url=old_dir['dirscan']+'\n'+dir_url
                    # dir_list = dir_url.split('\n')
                    mdbd.update({'host': host, 'task_name': taskName}, {'$set': {'dirscan': old_dir['dirscan']}})
            else:
                pass
        except Exception as direx:
            print(dir_url+' '+str(direx))
        finally:
            mongo.db.client.close()
            mongo = None
            thread_max_dir.release()

# Web指纹识别
def resWeb(url, host, taskName,target_type):
    threads_dir=[]
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

            resp = s.get(url, cookies=cookies, timeout=15, verify=False)
            resp_err = s.get(url + '/tt', timeout=15, verify=False)  # 请求不存在的页面去让页面报错
            for cms, finger in ruleDatas.items():
                hitHeads = re.findall(finger, str(resp.headers))
                hitBody = re.findall(finger, resp.text)
                hitBody_err = re.findall(finger, resp_err.text)
                if hitHeads or hitBody or hitBody_err:
                    if tag == '-':
                        print("===========组件信息-{0}：".format(cms) + url)
                        mdb.update({'host': host, 'task_name': taskName}, {'$set': {'tag': cms}})
                        break
                else:
                    pass

            print("--未识别--" + url)
            resp.close()
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
            print("--连接失败--" + url)
        finally:
            mongo.db.client.close()
            mongo = None
            thread_max.release()

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
        t = threading.Thread(target=resWeb, args=(url, host, taskName,tar_type,))
        threads.append(t)
        t.start()
    for j in threads:
        j.join()


# ICON_HASH计算
@bp.route('/icohash', methods=["GET", "POST"])
def icohash():
    return render_template('admin/icohash.html')


# ICON_HASH接口
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
        print("[!] Request Error"+"\n"+str(ex))
        hash = None
    return hash

#清空全部redis缓存
@bp.route('/clear_redis')
@login_required
def clear_redis():
    re_dis.flushall()
    return redirect(url_for('admin.index'))

# POC插件漏扫
@bp.route('/poc-scan', methods=('GET', 'POST'))
def poc_scan():
    return render_template('admin/poc-scan.html')
