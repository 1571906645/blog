# coding: utf-8
from search import db
from datetime import datetime


class New(db.Model):
    __tablename__ = 'new'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    text = db.Column(db.Text)
    cover = db.Column(db.String(255))
    clicknum = db.Column(db.Integer)
    comnum = db.Column(db.Integer)
    createtime = db.Column(db.DateTime)
    altertime = db.Column(db.DateTime)
    uid = db.Column(db.Integer, db.ForeignKey('user.id'))
    tid = db.Column(db.Integer, db.ForeignKey('type.id'))
    user = db.relationship('User', backref=db.backref('new'))
    type = db.relationship('Type', backref=db.backref('new'))

    def __repr__(self):
        return "<id %r>" % self.id


class Fatherart(db.Model):
    __tablename__ = 'fatherart'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(255))
    viewcount = db.Column(db.Integer)
    viewtime = db.Column(db.DateTime)
    uid = db.Column(db.Integer, db.ForeignKey('user.id'))
    nid = db.Column(db.Integer, db.ForeignKey('new.id'))
    user = db.relationship('User', backref=db.backref('fatherart'))
    new = db.relationship('New', backref=db.backref('fatherart'))

    def __repr__(self):
        return "<id %r>" % self.id


class Sonart(db.Model):
    __tablename__ = 'sonart'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(255))
    viewtime = db.Column(db.DateTime)
    uid = db.Column(db.Integer, db.ForeignKey('user.id'))
    fid = db.Column(db.Integer, db.ForeignKey('fatherart.id'))
    user = db.relationship('User', backref=db.backref('sonart'))
    fatherart = db.relationship('Fatherart', backref=db.backref('sonart'))

    def __repr__(self):
        return "<id %r>" % self.id


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255))
    password = db.Column(db.String(255))
    email = db.Column(db.String(255))
    face = db.Column(db.String(255))
    signature = db.Column(db.String(255))
    addtime = db.Column(db.DateTime)

    def __repr__(self):
        return "<id %s>" % self.id


class Type(db.Model):
    __tablename__ = 'type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    addtime = db.Column(db.DateTime)

    def __repr__(self):
        return "<id %s>" % self.id


class Admin(db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255))
    password = db.Column(db.String(255))
    face = db.Column(db.String(255))
    addtime = db.Column(db.DateTime)

    def __repr__(self):
        return "<id %s>" % self.id


if __name__ == '__main__':
    pass
    # db.create_all()
