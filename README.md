<h1 align="center">DBJ大宝剑 🗡</h1>

## 技术栈

**边界打点资产梳理工具**

```
Layui
Python-Flask
Redis
MongoDB
```

**演示地址**：http://119.45.153.4:5000 密码：`admin/admin`

演示站只作为演示，功能不可用！！！

Web资产管理虽然可跑任务，但是所有人都能看到你跑的任务

不要改密码，不要改密码，改了别人就看不了了

## 功能简介

### 企业组织架构查询

1、爬虫从爱企查查询企业的组织架构，一级单位、二级单位、三级单位的首页和邮箱等信息

![image-20210310145840858](https://gitee.com/wintrysec/images/raw/master//image-20210310145840858.png)

2、根据企业的主公司名称whois反查一级域名、ICP备案反查一级域名

![image-20210310142814509](https://gitee.com/wintrysec/images/raw/master//image-20210310142814509.png)

某些子公司可能也会有自己的ICP备案，这样上边的方法就会漏掉资产，这时需要自己去手动查询

[ICP备案查询](https://beian.miit.gov.cn/)

另外，企业组织架构里也有很多一级域名，但有些三级单位就很偏了和目标关联性不大，所以没有自动统计到一级域名这里边来，需要手工把企业组织架构导出，然后筛选一下域名，跟一级域名统计的结果合并后去个重，就能直接扔到`Web资产梳理`模块里边收集子域名了。

去重工具可在[狼盘](https://pan.wgpsec.org/6046dc5444303cf5641749d497edf867d8488c16)下载

3、所有查询到的数据会在后台命令行输出预览

![image-20210310143948010](https://gitee.com/wintrysec/images/raw/master//image-20210310143948010.png)

4、所有查询到的数据会存入redis缓存数据库，并且可导出为CSV

​      请及时导出查询到的数据，查询其它企业信息时会清空上一个查询企业的缓存

5、**注意！注意！注意！**（重要的事情说三遍）

​      此模块调用了百度的爱企查，访问速度过快过多会封IP弹出验证码导致无法查询报错

​      使用代理池查询速度会很慢，所以为了解决这个问题我使用了`X-Remote-Addr+Cookie`绕过

​      所以，这个模块的正确使用方法请注意看第六条！

6、添加Cookie

​      首先，在你的浏览器中登录百度的账号，打开爱企查这个网站

​      然后，用`Cookie Editor`这个浏览器插件导出爱企查的Cookie（会存在粘贴板，直接去粘贴）

​      再然后，把导出的Cookie粘贴到本项目的`baidu_cookie.txt`这个文件中

​      接着去正常使用此模块，随便找个公司名试一下，如果还是报错的话，接着往下看

​      此时，打开爱企查会有一个验证码让你填，填对了它，接着就能正常使用了

![image-20210310141735270](https://gitee.com/wintrysec/images/raw/master//image-20210310141735270.png)



​    最后，如果长时间不用此模块，下一次用还会报错；

​    这次就不用导Cookie了，直接浏览器访问爱企查填写一次验证码即可

### Web资产梳理

**一、子域名资产**

原理：调用FOFA数据

```python
cmd = '(domain="{dom}") || (cert="{dom}" &&  (status_code="200" || status_code="403") )'.format(dom=rootdomain)
```

子域名会自动识别CDN，帮助你定位目标真实IP和C段。

此方法可收集到绝大部分子域名资产，但不是百分百全的

**二、IP资产（Web资产）**

原理：调用FOFA数据（节约时间和VPS、代理池等资源）

这个功能是重头戏，也是最初设计的初衷（扫描单IP或C段中http协议的网站，并识别Web指纹）

![image-20210311161144314](https://gitee.com/wintrysec/images/raw/master//image-20210311161144314.png)

来看一下此模块的特点：

根据个人渗透时的思路设计的，不知道是否适合大多数人

1、无分页，一拉到底

开着Burp，点一个链接测试一个，不用老去翻页了

2、指纹索引

统计出有哪些指纹命中了，点击相关指纹则下边的资产也只显示与指纹相关的资产

![image-20210311161921828](https://gitee.com/wintrysec/images/raw/master//image-20210311161921828.png)

3、导出URL

导出全部URL，或根据指纹索引匹配资产导出URL，然后扔到别的工具或漏扫里边跑

![image-20210311161942904](https://gitee.com/wintrysec/images/raw/master//image-20210311161942904.png)

### 关于Web指纹识别

Web指纹识别时并未发送恶意请求所以无需代理，这样速度还快

所有指纹都在`flaskr->rules.py中`，以一个Dict的形式存在，python中字典的索引比列表(list)快

目前指纹不是很多，**`只收录一些国内常见且存在安全缺陷的应用`**

指纹的每个特征用 "|" 分割开来，前后不能有空格

![image-20210311170057173](https://gitee.com/wintrysec/images/raw/master//image-20210311170057173.png)

指纹很大一部分来自棱洞Ehole，感谢[r0eXpeR](https://github.com/r0eXpeR)师傅的开源分享

同时欢迎大家提交新指纹，自己去FOFA找几个资产验证特征准确性后，提交Issues即可。

**指纹识别的速度配置**

文件位置：`flaskr->admin.py->第34行代码处`

```python
# 设置最大线程数
thread_max = threading.BoundedSemaphore(value=305)
```

### ICON_HASH计算

计算图标的哈希值，并自动匹配相关资产（适合瞄准目标时用）

![image-20210311164827806](https://gitee.com/wintrysec/images/raw/master//image-20210311164827806.png)

### POC插件漏扫

计划中~先调研漏扫引擎~

## 安装教程

> 注意：企业组织架构收集模块因需在浏览器登录验证原因，暂时只能在windows上用

一、安装第三方库

推荐使用`Python3.9`以上版本

```bash
pip install -r requirements.txt
pip install Flask
```

二、安装配置数据库

> 先安装MonGoDB和Redis

```bash
#配置MongoDB
mongo
use webapp
db.createCollection("tasks")
db.createCollection("webs")
db.createCollection("subdomains")
db.createCollection("user")
db.user.insert({uid:1,username:'admin',password:'admin'})
exit
```

三、启动应用

```bash
#Windows系统 
点击start.bat

#Linux系统
sh start.sh
```

然后打开浏览器访问 IP:5000 登录即可（账户密码默认都是admin，进去自己改）

## 使用场景

**SRC**：

SRC挖掘中可以快人一步的理清脆弱资产，先下手为强

**红队打点**：

收集目标信息，梳理目标资产，快速发现脆弱资产尽快进入内网

**蓝队资产梳理**：

梳理自身资产，及时发现脆弱资产，重点看护

**漏洞研究 & 安全开发**：

Web指纹可用于开发自己的小工具，代码都有注释，通读代码可拓展自己的开发思路。

这些指纹都是国内出现频率较高的，所以可根据这里的Web指纹去研究挖掘相关Web应用的漏洞。