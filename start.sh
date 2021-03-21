export FLASK_APP=flaskr			#设置运行环境
export FLASK_ENV=development	#开启debug模式，有错误可以调试一下
mongo 127.0.0.1:27017/webapp /DBJ/data.js
flask run --host=0.0.0.0 		#运行项目，绑定0.0.0.0可外网访问

