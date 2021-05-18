import subprocess
import re
vuln_list=[]
# 实时输出
def sh(command):
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    for line in iter(p.stdout.readline, b''): 
        line = line.strip().decode("GB2312")
        critical=re.findall('critical',line)
        high=re.findall('critical',line)
        medium=re.findall('medium',line)

        #目标存在漏洞-加入数据库
        if critical or high or medium:
            print(line)
            vuln_time=line.split(' ',4)[0]+line.split(' ',4)[1]
            vuln_name=line.split(' ',4)[2]
            vuln_url=line.split(' ',5)[5]
            vuln_level=line.split(' ',5)[4]
            print(vuln_time)
            key_data={'vuln_name':vuln_name[6:-5],'vuln_url':vuln_url}
            vuln_list.append(key_data)
            print(vuln_name,vuln_url,vuln_level)
 
def vuln_scan(app_name):
    app_name=app_name
    command='nuclei -l urls.txt -stats -workflows workflows/{0}-workflow.yaml'.format(app_name)
    sh(command)