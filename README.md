<h1 align="center">DBJ大宝剑 🗡</h1>

![](https://img.shields.io/badge/ReaTeam-%E6%AD%A6%E5%99%A8%E5%BA%93-red)![](https://img.shields.io/badge/license-GPL--3.0-orange)![](https://img.shields.io/badge/version-1.0.1-brightgreen)![](https://img.shields.io/badge/author-wintrysec%20%E6%B8%A9%E9%85%92-blueviolet)![](https://img.shields.io/badge/WgpSec-%E7%8B%BC%E7%BB%84%E5%AE%89%E5%85%A8%E5%9B%A2%E9%98%9F-blue)

![](https://gitee.com/wintrysec/images/raw/master/banner.jpg)

## 概述

### 定位：边界资产梳理工具

**项目处于测试阶段，代码会时常更新，各位师傅点个`Star`关注下**

```bash
技术栈如下

前端   Layui
服务端 Python-Flask
缓存   Redis
持久化 MongoDB
```

## 功能简介

bilibili视频地址

### 企业组织架构查询

![](/data/readme/enscan1.png)

1、爬虫从爱企查查询企业的组织架构，一级单位、二级单位的首页和邮箱等信息

2、根据企业的公司名称whois反查域名、ICP备案反查域名，所有一级单位二级单位都会进行ICP反查


### 子域名资产梳理

**这块下任务的格式注意下**

```bash
#填写一级域名
baidu.com
```

**子域名查询模块**：
最终返回的信息是：`主机地址、解析IP、网站标题、Server、应用指纹、目录扫描、地理位置、运营商`

```bash
主机地址：所有子域名和通过https证书获取IP资产
解析IP：最终解析出的IP或者CDN的标识
网站标题：网站的title
Server：使用的服务器中间件，例如IIS、Apache等Web容器
应用指纹：网站使用的应用或设备类型，例如Shiro框架、Weblogic中间件、TP开发框架、各种OA系统
目录扫描：简单的扫描常见的后台和源码泄露（部分WAF会直接拦截）
地理位置：通过淘宝库查询IP的地理位置和运营商（FOFA返回的地理位置不准确）
```

**子域名获取流程**：

1、FOFA取数据
语法：`domain="baidu.com"` ，不过滤请求返回的状态码，尽可能多的获取子域名

获取数据：host、title、server

CERT证书取子域名资产数据（有些直接是真实IP资产，FOFA语法：`cert="baidu.com"`）

获取数据：host、title、server、ip

2、更多子域名获取渠道+最终结果去重

DNS爆破

使用`https://phpinfo.me/domain`的top3000字典，直接多线程调用`dns.resolver`解析域名。测试速度比`ksubdomain`无状态域名爆破工具快一点（原因是DBJ只爆破没做其它域名获取渠道，比如API查询接口这些）

3、CDN识别

解析A记录有CNAME的就是有CDN

cdn_header[host] - 放在指纹识别阶段 二次校验CDN 

4、调用指纹识别模块扫描URL识别Web指纹



### IP资产（Web资产）

**这块下任务的格式注意下**

```bash
#填写单个IP 或 C段
111.222.333.444
111.222.333.444/24
```

扫描单IP或C段中Web应用，并识别Web指纹

![image-20210311161144314](https://gitee.com/wintrysec/images/raw/master//image-20210311161144314.png)

**导出URL**

导出全部URL，或根据指纹索引匹配资产导出URL，然后扔到别的工具或漏扫里边跑

![image-20210311161942904](https://gitee.com/wintrysec/images/raw/master//image-20210311161942904.png)

### Web指纹识别

三种识别方式

> 1）HTTP-Header 匹配关键字
>
> 2）HTTP-Body 匹配关键字
>
> 3）ICON_HASH 匹配关键字

Web指纹识别时并未发送恶意请求所以无需代理。

指纹库在`rules.py`，以一个`Dict`的形式存在，python中字典的索引比列表(list)快

收录常见的应用指纹，不断更新中~

指纹的每个特征用 "|" 分割开来，前后不能有空格

![image-20210311170057173](https://gitee.com/wintrysec/images/raw/master//image-20210311170057173.png)



### ICON_HASH计算

计算图标的哈希值，并自动匹配相关资产（适合瞄准目标时用）

![image-20210311164827806](https://gitee.com/wintrysec/images/raw/master//image-20210311164827806.png)

### POC插件漏扫

漏扫调用的`nuclei`，因为这个漏扫速度快性能好，各位可自行和市面上的相关工具产品对比下

![](/data/readme/pocscan.png)

POC持续添加中.....（漏扫暂时只支持Windows平台）

**漏扫设置**

nuclei会在当前用户目录下生成一个`.config/nuclei`的配置文件夹；

修改里边两个配置文件

```bash
#.templates-config.json 模板配置文件
修改templates-directory的 路径为大宝剑当前的漏扫POC模板路径
\DBJ\flaskr\vulnscan\nuclei-templates


#config.yaml 扫描器配置文件
update-directory: C:\Users\wintrysec\Desktop\DBJ\flaskr\vulnscan/nuclei-templates
no-color: true
concurrency: 50
rate-limit: 2500
bulk-size: 50
```

## 安装教程

### Docker 安装模式

#### 手动编译
```bash
git clone https://github.com/wgpsec/DBJ.git # 速度太慢可用gitee
cd DBJ
docker build . -t dbj
docker run -d --name dbj -p 0.0.0.0:65000:5000 dbj # 映射到65000端口上
```
#### 第三方编译⚠️
```bash
docker run -it --name dbj -p 5000:5000  xrsec/dbj:latest
```

访问 http://ip:65000 

#### 查看输出信息

```bash
docker logs dbj
```

### 手动安装


一、安装第三方库

推荐使用`Python3.9`以上版本

```bash
pip install -r requirements.txt
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

然后打开浏览器访问 IP:5000 登录即可（默认账户密码admin/admin，进去自己改）

