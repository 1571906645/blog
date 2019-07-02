# coding:utf-8
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
# from flask_redis import FlaskRedis
import os
import datetime


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+mysqlconnector://root:root@127.0.0.1:3306/search_data?charset=utf8mb4"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["SECRET_KEY"] = "147258369"
app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(days=10)
app.config["SQLALCHEMY_POOL_SIZE"] = 2000
# app.config["SQLALCHEMY_ECHO"] = True
# app.config["REDIS_URL"] = "redis://localhost:6379/0"
# app.config["REDIS_URL"] = "redis://127.0.0.1/3"
app.config["Img_DIR"] = os.path.join(os.path.abspath(os.path.dirname(__file__)), "static/imgs/")
app.config["static"] = os.path.join(os.path.abspath(os.path.dirname(__file__)), "static/")

app.debug = True
# app.ssl_context = 'adhoc'
db = SQLAlchemy(app)
# rd = FlaskRedis(app)

from search.home import home as home_blueprint
from search.admin import admin as admin_blueprint

app.register_blueprint(home_blueprint)
app.register_blueprint(admin_blueprint, url_prefix="/admin")


@app.errorhandler(404)
def page_not_found(error):
    return render_template("home/404.html"), 404


@app.errorhandler(500)
def page_not_found(error):
    return render_template("home/500.html"), 500
