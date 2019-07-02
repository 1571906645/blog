# coding: utf-8
from . import admin
from flask import render_template, redirect, url_for, flash, session, request, Response, abort, send_file, \
    make_response, jsonify
import json
from search.models import New, User, Type, Admin, Fatherart, Sonart
from search import db, app
import datetime
from functools import wraps
from sqlalchemy import func
import os
import uuid
import re


# 生成当前时间
def now_date():
    nowdate = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return nowdate


# 登录装饰器
def admin_login_req(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin = session.get('adminname')
        if not admin:
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)

    return decorated_function


def my_key(s):
    value = ''
    num = len(s)
    if num < 5:
        s = 'b' + s + 'o' + s + 'x'
    for i in s:
        new = ord(i)
        if new % 3 == 0:
            value = value + str(new // 3) + i + i
        else:
            value = value + str(new // 5) + i
    return value


# 登录页面及登录验证
@admin.route("/login", methods=["GET", "POST"])
def login():
    if 'adminid' in session:
        return redirect(url_for('admin.index'))
    if request.method == 'POST':
        code = False
        msg = '账号或密码错误'
        ajdata = request.get_data()
        ajdata = json.loads(ajdata)
        username = ajdata['username']
        password = ajdata['password']
        admin = Admin.query.filter_by(username=username, password=password).first()
        if admin:
            code = True
            msg = '登录成功'
            session['adminname'] = admin.username
            session['adminid'] = admin.id
            if admin.face:
                session['adminface'] = admin.face
            else:
                session['adminface'] = 'favicon.ico'
            return json.dumps({
                'code': code,
                'msg': msg
            })
        else:
            return json.dumps({
                'code': code,
                'msg': msg
            })

    return render_template('admin/login.html')


# 主页
@admin.route("", methods=["GET", "POST"])
@admin.route("/index", methods=["GET", "POST"])
@admin_login_req
def index():
    return render_template('admin/index.html')


# 退出登录
@admin.route("/loginout", methods=["GET", "POST"])
def loginout():
    session.pop('adminid')
    session.pop('adminname')
    session.pop('adminface')
    return redirect(url_for('admin.login'))


# 添加用户页面
@admin.route("/adduser", methods=["GET", "POST"])
@admin_login_req
def adduser():
    return render_template('admin/adduser.html')


# 用户列表
@admin.route("/userlist", methods=["GET", "POST"])
@admin_login_req
def userlist():
    return render_template('admin/userlist.html')


# 返回用户数据
@admin.route("/alluser", methods=["GET", "POST"])
@admin_login_req
def alluser():
    if request.method == 'POST':
        ajdata = request.get_data()
        ajdata = json.loads(ajdata)
        name = ajdata['name']
        page = int(ajdata['page'])
        senddata = []
        if name:
            userdata = User.query.filter(User.username.like("%{}%".format(name))).order_by(
                User.addtime.desc()
            ).paginate(page=page, per_page=5)
        else:
            # usercount = User.query(func.count(User.id))
            userdata = User.query.order_by(
                User.addtime.desc()
            ).paginate(page=page, per_page=5)
        for i in userdata.items:
            result = {}
            result['id'] = i.id
            result['username'] = i.username
            result['email'] = i.email
            result['face'] = i.face
            result['addtime'] = str(i.addtime)
            senddata.append(result)
        return jsonify({
            'basedata': senddata,
            'count': userdata.total,
            'allpage': userdata.pages,
            'pagelist': list(userdata.iter_pages())
        })

    return None


# 删除用户
@admin.route("/deluser", methods=["GET", "POST"])
@admin_login_req
def deluser():
    if request.method == 'POST':
        code = False
        ajdata = request.get_data(as_text=True)
        user = User.query.filter_by(id=ajdata).first()
        new = New.query.filter_by(uid=user.id).first()
        if new:
            msg = '该用户还有发表的文章哦，不能删除'
            return jsonify({
                'code': code,
                'msg': msg
            })
        else:
            code = True
            if user.face:
                filepath = app.config["static"] + 'upload/' + user.face
                # print(filepath)
                if os.path.isfile(filepath):
                    os.remove(filepath)
            db.session.delete(user)
            db.session.commit()
            msg = '删除成功'
            return jsonify({
                'code': code,
                'msg': msg
            })

    return None


# 强制删除用户信息（包括用户发布的所有信息）
@admin.route("/forceddeluser", methods=["GET", "POST"])
@admin_login_req
def forceddeluser():
    if request.method == 'POST':
        ajdata = request.get_data(as_text=True)
        user = User.query.filter_by(id=ajdata).first()
        New.query.filter(New.uid == user.id).delete()
        if user.face:
            filepath = app.config["static"] + 'upload/' + user.face
            if os.path.isfile(filepath):
                os.remove(filepath)
        db.session.delete(user)
        db.session.commit()
        msg = '删除成功'
        return jsonify({
            'msg': msg
        })
    return False


# 个人信息页面
@admin.route("/me", methods=["GET", "POST"])
@admin_login_req
def me():
    if request.method == 'POST':
        ajdata = request.get_data(as_text=True)
        if ajdata == 'me':
            admin = Admin.query.filter_by(id=session.get('adminid')).first()
            return jsonify({
                'id': admin.id,
                'username': admin.username,
                'face': admin.face
            })
        else:
            return False
    return render_template('admin/me.html')


# 更改个人信息
@admin.route("/changeme", methods=["GET", "POST"])
@admin_login_req
def changeme():
    if request.method == 'POST':
        code = False
        id = request.form.get('userid')
        if id != str(session.get('adminid')):
            return '未知错误'
        name = request.form.get('username')
        face = request.files.get('facefile')
        admin1 = Admin.query.filter_by(id=id).first()
        admin2 = Admin.query.filter_by(username=name).first()
        if admin2 and admin1.username != name:
            msg = '这个名字已经有人用了，换个试试吧'
            return jsonify({
                'code': code,
                'msg': msg
            })
        elif not admin2 and admin1.username != name:
            admin1.username = name
        if bool(face):
            oldname = admin1.face
            if oldname:
                oldfile = app.config["static"] + 'upload/' + oldname
                if os.path.isfile(oldfile):
                    os.remove(oldfile)
            newname = uuid.uuid4().hex + '.' + face.filename.split('.')[-1]
            face.save(app.config["static"] + 'upload/' + newname)
            admin1.face = newname
            session['adminface'] = newname
        db.session.add(admin1)
        db.session.commit()
        session['adminname'] = name

        msg = '修改成功'
        code = True
        return jsonify({
            'code': code,
            'msg': msg
        })

    return False


# 更改密码
@admin.route("/changekw", methods=["GET", "POST"])
@admin_login_req
def changekw():
    if request.method == 'POST':
        code = False
        ajdata = request.get_data()
        ajdata = json.loads(ajdata)
        old = ajdata['old']
        new = ajdata['new']
        admin = Admin.query.filter_by(id=session.get('adminid'), password=old).first()
        if admin:
            admin.password = new
            db.session.add(admin)
            db.session.commit()
            session.pop('adminid')
            session.pop('adminname')
            msg = '修改成功，请重新登录'
            code = True
            return jsonify({
                'code': code,
                'msg': msg
            })
        else:
            msg = '密码输入错误'
            return jsonify({
                'code': code,
                'msg': msg
            })
    return render_template('admin/changekw.html')


# 添加类型
@admin.route("/addtype", methods=["GET", "POST"])
@admin_login_req
def addtype():
    if request.method == 'POST':
        code = False
        name = request.get_data(as_text=True)
        hastype = Type.query.filter_by(name=name).first()
        if hastype:
            msg = '这个名字已经有了，换个试试吧'
            return jsonify({
                'code': code,
                'msg': msg
            })
        else:
            type = Type(name=name, addtime=now_date())
            db.session.add(type)
            db.session.commit()
            msg = '添加成功'
            code = True
            return jsonify({
                'code': code,
                'msg': msg
            })
    return render_template('admin/addtype.html')


# 类型列表
@admin.route("/typelist", methods=["GET", "POST"])
@admin_login_req
def typelist():
    if request.method == 'POST':
        ajdata = request.get_data()
        ajdata = json.loads(ajdata)
        name = ajdata['name']
        page = int(ajdata['page'])
        senddata = []
        if name:
            typedata = Type.query.filter(Type.name.like("%{}%".format(name))).order_by(
                Type.addtime.desc()
            ).paginate(page=page, per_page=5)
        else:
            # usercount = User.query(func.count(User.id))
            typedata = Type.query.order_by(
                Type.addtime.desc()
            ).paginate(page=page, per_page=5)
        for i in typedata.items:
            result = {}
            result['id'] = i.id
            result['name'] = i.name
            result['addtime'] = str(i.addtime)
            # print(i.addtime)
            senddata.append(result)
        return jsonify({
            'basedata': senddata,
            'count': typedata.total,
            'allpage': typedata.pages,
            'pagelist': list(typedata.iter_pages())
        })
    return render_template('admin/typelist.html')


# 删除类型
@admin.route("/deltype", methods=["GET", "POST"])
@admin_login_req
def deltype():
    code = False
    ajdata = request.get_data(as_text=True)
    new = New.query.filter_by(tid=ajdata).first()
    if new:
        msg = '该类型有发表的文章，无法删除'
        return jsonify({
            'code': code,
            'msg': msg
        })
    else:
        type = Type.query.filter_by(id=ajdata).first()
        db.session.delete(type)
        db.session.commit()
        code = True
        msg = '删除成功'
        return jsonify({
            'code': code,
            'msg': msg
        })


# 添加文章
@admin.route("/addnew", methods=["GET", "POST"])
@admin_login_req
def addnew():
    if request.method == 'POST':
        typeid = request.form.get('type')
        title = request.form.get('title')
        text = request.form.get('editor')
        cover = request.files.get('cover')
        if cover:
            newname = uuid.uuid4().hex + '.' + cover.filename.split('.')[-1]
            cover.save(app.config["static"] + 'upload/' + newname)
            new = New(
                title=title,
                text=text,
                cover=newname,
                createtime=now_date(),
                tid=typeid
            )
        else:
            new = New(
                title=title,
                text=text,
                createtime=now_date(),
                tid=typeid
            )
        db.session.add(new)
        db.session.commit()
        return '发布成功'
    typedata = Type.query.all()
    return render_template('admin/addnew.html', typedata=typedata)


# 文章列表
@admin.route("/newlist", methods=["GET", "POST"])
@admin_login_req
def newlist():
    if request.method == 'POST':
        basedata = []
        ajdata = request.get_data()
        ajdata = json.loads(ajdata)
        titlename = ajdata['title']
        page = ajdata['page']
        typeid = ajdata['typeid']
        if titlename and not typeid:
            newdata = New.query.outerjoin(User, User.id == New.uid).filter(
                New.title.like("%{}%".format(titlename))).outerjoin(Type, Type.id == New.tid).order_by(
                New.createtime.desc()
            ).paginate(page=page, per_page=5)
        elif titlename and typeid:
            newdata = New.query.outerjoin(User, User.id == New.uid).filter(
                New.title.like("%{}%".format(titlename)), New.tid == typeid).outerjoin(Type,
                                                                                       Type.id == New.tid).order_by(
                New.createtime.desc()
            ).paginate(page=page, per_page=5)
        elif typeid and not titlename:
            newdata = New.query.outerjoin(User, User.id == New.uid).filter(
                New.tid == typeid).outerjoin(Type, Type.id == New.tid).order_by(
                New.createtime.desc()
            ).paginate(page=page, per_page=5)
        else:
            newdata = New.query.outerjoin(User, User.id == New.uid).outerjoin(Type, Type.id == New.tid).order_by(
                New.createtime.desc()
            ).paginate(page=page, per_page=5)
        for i in newdata.items:
            result = {}
            result['id'] = i.id
            result['title'] = i.title
            result['createtime'] = str(i.createtime)
            if i.user:
                result['user'] = i.user.username
            result['type'] = i.type.name
            basedata.append(result)
        return jsonify({
            'basedata': basedata,
            'count': newdata.total,
            'allpage': newdata.pages,
            'pagelist': list(newdata.iter_pages())
        })

    typedata = Type.query.all()
    return render_template('admin/newlist.html', typedata=typedata)


# 删除文章
@admin.route('/delnew', methods=["GET", "POST"])
@admin_login_req
def delnew():
    code = False
    id = request.get_data(as_text=True)
    new = New.query.filter_by(id=id).first()
    if new:
        text = new.text
        # print(text)
        filepaths = re.findall('(src|href)="(.*?)"', text)
        if bool(filepaths):
            # print(filepaths)
            for i in filepaths:
                newfile = app.config["static"] + '/'.join(i[1].split('/')[2:])
                if os.path.isfile(newfile) and 'php/upload' in newfile:
                    # print(newfile)
                    os.remove(newfile)
        if new.cover and os.path.isfile(app.config["static"] + 'upload/' + new.cover):
            os.remove(app.config["static"] + 'upload/' + new.cover)
        farts = Fatherart.query.filter(Fatherart.nid == new.id)
        for f in farts:
            Sonart.query.filter(Sonart.fid == f.id).delete()
        farts.delete()
        db.session.delete(new)
        db.session.commit()
        code = True
        msg = '删除成功'
        return jsonify({'code': code, 'msg': msg})
    else:
        msg = '该文章不存在'
        return jsonify({'code': code, 'msg': msg})


# 添加管理员
@admin.route('/addadmin', methods=["GET", "POST"])
@admin_login_req
def addadmin():
    if request.method == 'POST':
        name = request.form.get('username')
        pw = request.form.get('password')
        admin1 = Admin.query.filter_by(username=name).first()
        if admin1:
            msg = '这个名字有人用了，换个试试？'
            return jsonify({'msg': msg})
        else:
            face = request.files.get('facefile')
            if bool(face):
                newname = uuid.uuid4().hex + '.' + face.filename.split('.')[-1]
                face.save(app.config["static"] + 'upload/' + newname)
                admin = Admin(username=name, password=pw, face=newname, addtime=now_date())
            else:
                admin = Admin(username=name, password=pw, addtime=now_date())
            db.session.add(admin)
            db.session.commit()
            msg = '添加成功'
            return jsonify({'msg': msg})
    else:
        return render_template('admin/addadmin.html')


# 管理员列表
@admin.route('/adminlist', methods=["GET", "POST"])
@admin_login_req
def adminlist():
    if request.method == 'POST':
        basedata = list()
        ajdata = request.get_data()
        ajdata = json.loads(ajdata)
        name = ajdata['aname']
        page = ajdata['page']
        if name:
            admindata = Admin.query.filter(Admin.username.like('%{}%'.format(name))).order_by(
                Admin.addtime.desc()
            ).paginate(page=page, per_page=5)
        else:
            admindata = Admin.query.paginate(page=page, per_page=5)
        for i in admindata.items:
            result = {}
            result['id'] = i.id
            result['username'] = i.username
            result['addtime'] = str(i.addtime)
            result['face'] = i.face
            basedata.append(result)
        return jsonify({
            'basedata': basedata,
            'count': admindata.total,
            'allpage': admindata.pages,
            'pagelist': list(admindata.iter_pages())
        })
    else:
        return render_template('admin/adminlist.html')
