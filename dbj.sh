#!/bin/sh
clear
echo "\n\033[1;34m  __      __                                \033[0m"
echo "\033[1;32m /  \    /  \____ ______  ______ ____   ____  \033[0m"
echo "\033[1;36m \   \/\/   / ___\\____ \/  ___// __ \_/ ___\ \033[0m"
echo "\033[1;31m  \        / /_/  >  |_> >___ \\  ___/\  \___  \033[0m"
echo "\033[1;35m   \__/\  /\___  /|   __/____  >\___  >\___  > \033[0m"
echo "\033[1;35m        \//_____/ |__|       \/     \/     \/ \n\033[0m"


echo "\033[1;32m[help] \033[0m"
echo "\033[1;36mhttps://github.com/wgpsec/DBJ \n\033[0m"
echo "\033[1;36mUpdate DBJ-PY \033[0m"
pip3 install -r /DBJ/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
echo "\033[1;36mStart DBJ \033[0m"
sh -c "/DBJ/start.sh" 
