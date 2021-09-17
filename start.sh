#!/bin/sh
export FLASK_APP=flaskr
export FLASK_ENV=development
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
nohup mongod -f /etc/mongodb.conf &
nohup redis-server &
sleep 5
mongo 127.0.0.1:27017/webapp data.js
flask run --host=0.0.0.0
