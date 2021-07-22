#!/bin/sh
clear
# [banner]

echo "\n\033[1;34m ______  ______     ___  \033[0m"
echo "\033[1;32m |  _  \ | ___ \   |_  | \033[0m"
echo "\033[1;36m | | | | | ___ \     | | \033[0m"
echo "\033[1;31m | |/ /  | |_/ / /\__/ / \033[0m"
echo "\033[1;35m |___/   \____/  \____/ \n\033[0m"
echo "\033[1;36m                 Wgpsec \n\033[0m"

# [help]
echo "\033[1;32m [help] \033[0m"
echo "\033[1;36m https://github.com/wgpsec/DBJ \n\033[0m"
echo "\033[1;36m Update DBJ ✨\n\033[0m"

# [update]
git -C /DBJ/ pull

# 对比两个文件是否一致，不一致 则 停止容器等待重启
if [ "`diff /start.sh /DBJ/start.sh -q`" = "Files /start.sh and /DBJ/start.sh differ" ]
then
        echo "\033[1;36m Update DBJ Succers ✨\n\033[0m"
        cp -rf /DBJ/start.sh /start.sh
        echo "\033[1;36m Update DBJ-PY-Tools ✨\n\033[0m"
        pip3 install -r /DBJ/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
        exit 0
fi

echo "\033[1;36m Start DBJ ✨\n\033[0m"

# [main]

export FLASK_APP=flaskr                 #设置运行环境
export FLASK_ENV=development    #开启debug模式，有错误可以调试一下
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
service mongodb start
service redis-server start
sleep 5
mongo 127.0.0.1:27017/webapp data.js
flask run --host=0.0.0.0                #运行项目，绑定0.0.0.0可外网访问   
