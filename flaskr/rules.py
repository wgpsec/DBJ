#coding=UTF-8
ruleDatas = {
    #   指纹格式请严格遵守如下格式
    #   多个匹配特征在小括号内用 | 分割，比如下边 “Tomcat默认页面” 这个
    #  '应用名称':{'value':'小写应用关键描述','finger':'(匹配关键字)'},

    ###高危中间件
    'Shiro框架':{'value':'shiro','finger':'(deleteMe)'},
    'Weblogic':{'value':'weblogic','finger':'(Hypertext Transfer Protocol -- HTTP/1.1</i>)'},
    'Jboss':{'value':'jboss','finger':'(jboss.css)'},
    'Tomcat默认页面':{'value':'tomcat','finger':'(/manager/html|/manager/status)'},
    'Spring框架':{'value':'spring','finger':'(116323821)'},

    #协同办公
    '致远OA':{'value':'seeyon','finger':'(/seeyon/USER-DATA/IMAGES/LOGIN/login.gif|/seeyon/common|SY8045|Seeyon-Server/1.0|yyoa/)'},
    '通达OA':{'value':'tongda','finger':'(tongda.ico|onmouseover="this.focus()")'},
    '泛微OA':{'value':'ecology','finger':'(/wui/theme|/js/ecology8/lang/weaver_lang_7_wev8.js|WVS)'},
    'e-Bridge':{'value':'e-bridge','finger':'(/main/login/images/loginlogo.png|e-Bridge)'},
    'E-Mobile':{'value':'e-mobile','finger':'(weaver,e-mobile|E-Mobile&nbsp;)'},
    '蓝凌OA':{'value':'landray','finger':'(kmss_onsubmit|sys/ui/extend/theme/default/style/icon.css)'},
    '用友软件':{'value':'yongyou','finger':'(uclient.yonyou.com)'},
    'Zentao-禅道':{'value':'zentao','finger':'(zentaosid|/zentao/js|/zentao/theme/|/theme/default/images/main/zt-logo.png)'},
    '协众OA':{'value':'xiezhong','finger':'(CNOAOASESSID|Powered by 协众OA)'},
    '金和OA':{'value':'jinheoa','finger':'(金和协同管理平台)'},
    '金碟EAS':{'value':'kdgs','finger':'(easSessionId)'},
    '金碟政务GSiS':{'value':'kdgs','finger':'(/kdgs/script/kdgs.js)'},

    ###内容管理CMS
    'WordPress':{'value':'wordpress','finger':'(wp-content)'},
    'ThinkCMF':{'value':'thinkcmf','finger':'({Simple content manage Framework)'},
    'ThinkPHP':{'value':'thinkphp','finger':'(ThinkPHP</a>|十年磨一剑-为API开发设计的高性能框架|<h1>页面错误！请稍后再试～</h1>)'},
    'ThinkPHP-3.x':{'value':'thinkphp3','finger':'(Simple OOP PHP Framework)'},
    'Spring-Boot':{'value':'springboot','finger':'(<title>Spring Boot开发平台</title>)'},


    ###邮件服务器
    'Exchange':{'value':'exchange','finger':'(/owa/auth.owa)'},
    'CoreMail':{'value':'coremail','finger':'(coremail/common)'},

    ###网站管理 集群、监控、仓库、队列 、大数据
    'Swagger-UI':{'value':'swaggerui','finger':'(/swagger-ui.css|swagger-ui-bundle.js)'},
    'Gitlab':{'value':'gitlab','finger':'(assets/gitlab_logo|GitLab</title>)'},
    '宝塔面板':{'value':'baota','finger':'(app.bt.cn/static/app.png|安全入口校验失败)'},
    'phpMyAdmin':{'value':'phpmyadmin','finger':'(phpmyadmin.css|img/logo_right.png)'},
    'Zabbix':{'value':'zabbix','finger':'(zbx_sessionid|images/general/zabbix.ico|Zabbix SIA)'},
    'Nagios':{'value':'nagios','finger':'(Nagios Access)'},
    'Nexus':{'value':'nexus','finger':'(Nexus Repository Manager|NX-ANTI-CSRF-TOKEN)'},
    'Harbor':{'value':'harbor','finger':'(harbor-lang|<title>Harbor</title>)'},
    'Jenkins':{'value':'jenkins','finger':'(M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z)'},
    'RabbitMQ':{'value':'rabbitmq','finger':'(<title>RabbitMQ Management</title>)'},
    'Jira':{'value':'jira','finger':'(jira.webresources)'},
    'Spark_Master':{'value':'spark','finger':'(Spark Master at)'},
    'Spark_Worke':{'value':'spark','finger':'(Spark Worker at)'},
    'Elasticsearch':{'value':'elasticsearch','finger':'(1611729805)'},
    'XXL-Job':{'value':'xxljob','finger':'(分布式任务调度平台XXL-JOB)'},
    #华为
    '华为IBMC':{'value':'huawei','finger':'(/bmc/resources/images/product/img_01.png)'},
    #其它网络设备
    '锐捷产品（Ruijie）':{'value':'ruijie','finger':'(4008 111 000)'},
    'TOTOLink路由器':{'value':'totolink','finger':'(window.location.href="/home.asp")'},
}