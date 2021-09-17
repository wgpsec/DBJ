import subprocess
import re
from flask import Flask
from flask_pymongo import PyMongo
import requests
import json

vuln_list=[]

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
    hookdb=mongo.db.http_hook

# 钉钉通知
def Dtalk_send(msg):
    msg=str(msg)
    hook = hookdb.find()
    webhook = hook[0]['hook']
    dd_headers = {
        "Content-Type": "application/json",
        "Charset": "UTF-8"
        }
    dd_message = {
        "msgtype": "text",
        "text": {
            "content": '资产监控-'+msg
            }
        }
    fs_mssage = {
        "msg_type": "text",
        "content": {
        "text": '资产监控-'+msg
        }
    }
    if "feishu" in str(webhook):
        mssage = fs_mssage
    else:
        mssage = dd_message
    r = requests.post(url=webhook, headers=dd_headers, data=json.dumps(mssage),verify=False,timeout=15)
    print(r.text)

# 实时输出
def sh(command):
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    for line in iter(p.stdout.readline, b''): 
        line = line.strip().decode("GB2312")
        critical=re.findall('critical',line)
        high=re.findall('high',line)
        medium=re.findall('medium',line)

        #目标存在漏洞-加入数据库
        if critical or high or medium:
            vuln_time=line.split(' ',4)[0]+line.split(' ',4)[1]
            vuln_name=line.split(' ',4)[2]
            vuln_url=line.split(' ',5)[5]
            vuln_level=line.split(' ',5)[4]

            #redis缓存显示
            key_data={'vuln_name':vuln_name[1:-1],'vuln_url':vuln_url}
            vuln_list.append(key_data)

            #钉钉推送
            msg = "发现漏洞：{0}  {1}".format(vuln_name,vuln_url)
            Dtalk_send(msg)

            #持久化
            host = vuln_url.split("://",1)[1].split("/",1)[0].strip()
            mdb.insert({'vuln_name':vuln_name,'vuln_url':vuln_url,'vuln_level':vuln_level,'vuln_time':vuln_time,'host':host})
            print(vuln_time,vuln_name,vuln_url,vuln_level)
 
def vuln_scan(app_name,proxy_url,url):
    app_name=app_name
    if proxy_url is None:
        print("\n无代理,使用直连网络......")
        if url is None:
            command='nuclei -l flaskr/vulnscan/urls.txt -stats -tags {0} -timeout 20'.format(app_name)
            print(command)
        else:
            command='nuclei -u {0} -stats -tags {1} -timeout 20'.format(url,app_name)
    else:
        print("\n代理生效中,",proxy_url)
        if url is None:
            command='nuclei -l flaskr/vulnscan/urls.txt -stats -tags {0} -timeout 20 -proxy-url {1}'.format(app_name,proxy_url)
        else:
            command='nuclei -u {0} -stats -tags {1} -timeout 20 -proxy-url {2}'.format(url,app_name,proxy_url)
    sh(command)