#coding=utf-8
import os
from urllib import parse
from flask import Flask
from flask_pymongo import PyMongo
from .import admin
from . import auth
from . import enscan

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    #注册蓝图
    app.register_blueprint(admin.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(enscan.bp)

    #设置根目录路由
    app.add_url_rule('/',endpoint='admin.index')
    app.config.from_mapping(SECRET_KEY='dev')

    #连接MongoDB
    app.config['MONGO_URI'] =  "mongodb://{host}:{port}/{database}".format(
        host='localhost',
        port=27017,
        database='webapp'
    )
    
    return app