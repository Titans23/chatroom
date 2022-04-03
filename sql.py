from flask_sqlalchemy import SQLAlchemy
from flask import Flask
app = Flask(__name__)
# 配置信息
class Config(object):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:123456@localhost:3306/chat'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "west2online"

app.config.from_object(Config)

db = SQLAlchemy(app)