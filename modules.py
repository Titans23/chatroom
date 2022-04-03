from flask_login import UserMixin
from sql import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model,UserMixin):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}
    telephone = db.Column(db.String(32), primary_key=True, nullable=False)  # 手机号码作为主键
    password_hash = db.Column(db.String(256), nullable=False)
    nick_name = db.Column(db.String(32))  # 用户昵称
    state = db.Column(db.String(32))      # 用户登录状态
    room_id = db.Column(db.Integer)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Friend(db.Model):
    __tablename__ = "friends"
    __table_args__ = {'extend_existing': True}
    tel1 = db.Column(db.String(32), primary_key=True, nullable=False)
    tel2 = db.Column(db.String(32), primary_key=True)

class Room(db.Model):
    __tablename__ = 'rooms'
    __table_args__ = {'extend_existing':True}
    id = db.Column(db.Integer,primary_key=True,nullable=False)  # 房间号id
    telephone = db.Column(db.String(32), nullable=False)


if __name__ == '__main__':
    db.drop_all()
    db.create_all()
