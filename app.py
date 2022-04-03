import random
import datetime
import flask_login
import pymysql
from flask import Flask, redirect, request, sessions, render_template, flash, url_for, g, jsonify, current_app
from flask_login import LoginManager, current_user, logout_user
from modules import User, Friend
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from PIL import Image
import time
from sqlalchemy import or_

app = Flask(__name__)


class Config(object):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:123456@localhost:3306/chat'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "west2online"


app.config.from_object(Config)

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = '/login'

socketio = SocketIO()
socketio.init_app(app, cors_allowed_origins='*')


def judge(tel1, tel2):
    if tel1 == tel2:
        return False
    else:
        temp1 = str(min(int(tel1), int(tel2)))
        temp2 = str(max(int(tel1), int(tel2)))
        friend = Friend.query.filter(Friend.tel1 == temp1, Friend.tel2 == temp2).first()
        if not friend:
            return True
        else:
            return False


app.jinja_env.globals.update(judge=judge)


def change_db(sql, data):
    db = pymysql.connect(host='localhost', user='root', password='123456', port=3306, db='chat')
    cursor = db.cursor()
    try:
        cursor.execute(sql, data)
        db.commit()
    except:
        db.rollback()
    db.close()


@login_manager.user_loader
def user_loader(telephone):
    telephone = str(telephone)
    if not User.query.filter(User.telephone == telephone).first():
        return
    user = User.query.filter(User.telephone == telephone).first()
    user.id = telephone
    return user


# @login_manager.request_loader
# def request_loader(request):
#     telephone = str(request.form.get('telephone'))
#     print(telephone)
#     if not User.query.filter(User.telephone == telephone).first():
#         return
#     user = User.query.filter(User.telephone == telephone).first()
#     user.id = telephone
#     return user


@app.route('/')
@flask_login.login_required
def index():
    users = User.query.filter(User.state == '在线').all()
    time.sleep(1)
    return render_template('index.html', users=users)


@app.route('/logout')
@flask_login.login_required
def logout():
    sql = 'UPDATE users SET state = %s WHERE telephone = %s'
    change_db(sql, ("离线", current_user.telephone))
    logout_user()
    return render_template('login.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        telephone = str(request.form.get('telephone'))
        type1 = request.form.get('login')
        type2 = request.form.get('register')
        if len(telephone) != 11 and str(telephone)[0] != 1:
            flash("输入手机号码格式不正确")
        else:
            # 登录类型
            if type1:
                if not all([password, telephone]):
                    flash("请输入完整的账号密码")
                else:
                    user = User.query.filter(User.telephone == telephone).first()
                    # 判断数据库中是否存在user
                    if user:
                        # 判断密码是否正确
                        if not user.check_password(password):
                            flash("密码错误")
                        else:
                            sql = 'UPDATE users SET state = %s WHERE telephone = %s'
                            change_db(sql, ("在线", user.telephone))
                            if request.form.get('remember') == 'remember':
                                user.id = telephone
                                flask_login.login_user(user, remember=True, duration=datetime.timedelta(minutes=20))
                                next = request.args.get('next')
                                time.sleep(1)
                                return redirect(next or url_for('index'))
                            else:
                                user.id = telephone
                                flask_login.login_user(user)
                                next = request.args.get('next')
                                time.sleep(1)
                                return redirect(next or url_for('index'))
                    else:
                        flash("该账号不存在")
            # 注册
            elif type2:
                if not all([password, telephone]):
                    flash("请输入完整的账号密码")
                else:
                    user = User.query.filter(User.telephone == telephone).first()
                    # 判断数据库中是否存在user
                    if user:
                        flash("该账号已存在")
                    else:
                        nick_name = "用户昵称" + str(random.randint(1001, 99999))
                        user = User(telephone=telephone, nick_name=nick_name)
                        user.set_password(password)
                        db.session.add(user)
                        db.session.commit()
                        flash("注册成功")
                        file1 = open(f'./static/{telephone}.png', 'wb')
                        file2 = open('./static/first.png', 'rb')
                        file1.write(file2.read())
                        file1.close()
                        file2.close()
                        time.sleep(1)
                        return render_template("login.html")
    time.sleep(1)
    return render_template("login.html")


@app.route('/home', methods=['POST', 'GET'])
@flask_login.login_required
def user_home():
    telephone = current_user.telephone
    user = User.query.filter(User.telephone == telephone).first()
    if request.method == 'POST':
        user.nick_name = request.form.get('nick_name')
        new_avatar = request.files.get('file')
        if new_avatar:
            img = Image.open(new_avatar)
            img.save(f'./static/{user.telephone}.png')
        sql = 'UPDATE users SET nick_name = %s WHERE telephone = %s'
        change_db(sql, (user.nick_name, user.telephone))
        # db.session.commit()
    time.sleep(1)
    return render_template('user_home.html')


@app.route('/add_friend/<tel>', methods=['POST'])
@flask_login.login_required
def add_friend(tel):
    current_user_telephone = int(current_user.telephone)
    tel = int(tel)
    if current_user_telephone > tel:
        tel2 = current_user.telephone
        tel1 = tel
    else:
        tel2 = tel
        tel1 = current_user.telephone
    friend = Friend(tel1=str(tel1), tel2=str(tel2))
    db.session.add(friend)
    db.session.commit()
    # return jsonify(code=200,data={"tel1" : tel1,"tel2" : tel2})
    time.sleep(1)
    return render_template('add_success.html')


@app.route('/get_friends')
@flask_login.login_required
def get_friends():
    friends_user = []
    friends1 = Friend.query.filter(Friend.tel1 == current_user.telephone).all()
    if friends1:
        for friend in friends1:
            tel = friend.tel2
            user = User.query.filter(User.telephone == tel).first()
            friends_user.append(user)
    friends2 = Friend.query.filter(Friend.tel2 == current_user.telephone).all()
    if friends2:
        for friend in friends2:
            tel = friend.tel1
            user = User.query.filter(User.telephone == tel).first()
            friends_user.append(user)
    time.sleep(1)
    return render_template('friends.html', friends=friends_user)


# @app.route('/add_room',methods=['POST','GET'])
# @flask_login.login_required
# def add_room():
#     if request.method == 'POST':
#     return render_template('add_room.html')

@app.route('/image/<int:telephone>')
def get_image(telephone):
    image = open(f"./static/{telephone}.png", 'rb')
    return image.read()


@app.route("/favicon.ico")
def get_web_logo():
    return current_app.send_static_file('favicon.ico')


@socketio.on('client_event')
def client_msg(msg):
    local_time = '(' + str(time.strftime('%H:%M:%S', time.localtime(time.time()))) + ')'
    socketio.emit('server_response', {'data': msg['data'], 'nick_name': current_user.nick_name, 'time': local_time,
                                      'tel': str(current_user.telephone)})
    # print("client")


@socketio.on('connect_event')
def connected_msg(msg):
    local_time = '(' + str(time.strftime('%H:%M:%S', time.localtime(time.time()))) + ')'
    socketio.emit('server_response',
                  {'data': msg['data'], 'nick_name': current_user.nick_name, 'time': local_time,
                   'tel': current_user.telephone})
    # print("connect")


# @socketio.on('disconnect_event')
# def disconnected_msg(msg):
#     local_time = '(' + str(time.strftime('%H:%M:%S', time.localtime(time.time()))) + ')'
#     socketio.emit('server_response',
#                   {'data': msg['data'], 'nick_name': current_user.nick_name, 'time': local_time, 'code': 'leave'})
#     print("disconnect")

if __name__ == '__main__':
    socketio.run(app, port=5000, debug=True)
