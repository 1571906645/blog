# coding:utf-8
from . import home
from flask import render_template, redirect, url_for, session, request, abort, send_file, make_response, jsonify
from search.models import New, User, Type, Fatherart, Sonart
import jieba
import json
from search import db, app
import qrcode
from io import BytesIO
import re
from .uploader import Uploader
import ast
import datetime
import uuid
from functools import wraps
import random
import os


# 登录装饰器
def home_login_req(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin = session.get('uid')
        if not admin:
            return redirect(url_for('home.index'))
        return f(*args, **kwargs)

    return decorated_function


def set_qrcode(url):
    qr = qrcode.QRCode(
        version=3,
        error_correction=qrcode.ERROR_CORRECT_M,
        box_size=10,
        border=4
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image()
    byte_io = BytesIO()
    img.save(byte_io, 'PNG')
    byte_io.seek(0)
    return byte_io


def send_mail(user='1571906645@qq.com', message='123456'):
    import smtplib
    from email.mime.text import MIMEText
    from email.header import Header
    from email.mime.image import MIMEImage
    from email.mime.multipart import MIMEMultipart
    from email.utils import formataddr
    sender = '1691686022@qq.com'
    msg = MIMEMultipart('related')
    # msg['From'] = Header('我自己', 'utf-8')
    msg['From'] = formataddr(['验证消息', sender])
    msg['To'] = formataddr(['收件人', user])
    msg['Subject'] = '注册验证'
    msgAlternative = MIMEMultipart('alternative')
    msg.attach(msgAlternative)
    # ft = open('123.xls', 'rb')
    # att1 = MIMEText(ft.read(), 'base64', 'utf-8')
    # ft.close()
    # att1['Content-Type'] = 'application/octet-stream'
    # att1['Content-Disposition'] = 'attachment;filename="123.xls"'
    # msg.attach(att1)
    mail_msg = """
<p>验证码</p>
<p>%s</p>
""" % (message)
    msgAlternative.attach(MIMEText(mail_msg, 'html', 'utf-8'))
    # fp = open('1.png', 'rb')
    # msgImage = MIMEImage(fp.read())
    # fp.close()
    # msgImage.add_header('Content-ID', '<image1>')
    # msg.attach(msgImage)
    server = smtplib.SMTP('smtp.qq.com', 25)
    # server.starttls()
    server.login(sender, 'ygouzzudjvchejhi')
    server.sendmail(sender, [user], msg.as_string())
    server.quit()
    return True


def now_date():
    nowdate = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return nowdate


# 二维码
@home.route("/myqrcode", methods=["GET", "POST"])
def myqrcode():
    try:
        name = request.args.get('name', '')
        # print(request.host_url)
        byte_io = set_qrcode(url="%s%s" % (request.host_url, name))
        return send_file(byte_io, mimetype='image/png')
    except Exception:
        abort(404)
        return None


# 注册页面
@home.route("/register", methods=['GET', 'POST'])
def register():
    return render_template('home/regist.html')


# 密码加密函数
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


# 注册验证
@home.route("/regist", methods=['GET', 'POST'])
def regist():
    code = False
    msg = ''
    jsdata = request.get_data()
    jsdata = json.loads(jsdata)
    name = jsdata['name']
    password = my_key(str(jsdata['password']))
    keycode = jsdata['keycode']
    email = jsdata['email']
    if 'mailcode' not in session:
        msg = '请先获取验证码'
        return json.dumps({
            'code': code,
            'msg': msg
        })
    nowdate = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user = User.query.filter_by(username=name).first()
    if user:
        msg = '该用户名已存在'
        return json.dumps({
            'code': code,
            'msg': msg
        })
    if email != session.get('email'):
        msg = '邮箱不能更改哦'
        return json.dumps({
            'code': code,
            'msg': msg
        })
    if keycode == session.get('mailcode'):
        code = True
        msg = '注册成功,跳转到登录页面'
        session.pop('mailcode')
        user = User(
            username=name,
            password=password,
            email=session.pop('email'),
            addtime=nowdate
        )
        db.session.add(user)
        db.session.commit()
        return json.dumps({
            'code': code,
            'msg': msg
        })
    else:
        msg = '验证码错误'
        return json.dumps({
            'code': code,
            'msg': msg
        })


# 登录
@home.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        code = False
        udata = request.get_data()
        udata = json.loads(udata)
        name = udata['name']
        password = my_key(udata['password'])
        user = User.query.filter_by(username=name, password=password).first()
        if user:
            code = True
            session['uid'] = user.id
            session['uname'] = user.username
            # print(code)
        else:
            user = User.query.filter_by(email=name, password=password).first()
            if user:
                name = user.username
                code = True
                session['uid'] = user.id
                session['uname'] = user.username
        return json.dumps({
            'code': code,
            'name': name
        })
    return render_template('home/login.html')


# 忘记密码
@home.route("/forget", methods=["POST", "GET"])
def forget():
    if request.method == 'POST':
        code = False
        msg = ''
        ajdata = request.get_data()
        ajdata = json.loads(ajdata)
        pw = ajdata['pw1']
        email = ajdata['email']
        keycode = ajdata['keycode']
        if 'mailcode' not in session:
            msg = '请先获取验证码'
            return json.dumps({
                'code': code,
                'msg': msg
            })
        if keycode != session.get('mailcode'):
            msg = '验证码错误'
            return json.dumps({
                'code': code,
                'msg': msg
            })
        if email != session.get('email'):
            msg = '不要更改邮箱哦'
            return json.dumps({
                'code': code,
                'msg': msg
            })
        user = User.query.filter_by(email=email).first()
        if user:
            user.password = my_key(pw)
            session.pop('mailcode')
            session.pop('email')
            db.session.add(user)
            db.session.commit()
            msg = '密码修改成功，返回登录'
            code = True
            return json.dumps({
                'code': code,
                'msg': msg
            })
        else:
            msg = '这个邮箱没有注册过哦'
            return json.dumps({
                'code': code,
                'msg': msg
            })

    return render_template('home/forget.html')


# 生成验证码
def get_num():
    import random
    s = '1234567890'
    num = ''
    for i in range(6):
        num = num + random.choice(s)
    return num


# 发送验证码
@home.route("/sendmail", methods=['GET', 'POST'])
def sendmail():
    ajaxdata = request.get_data()
    ajaxdata = json.loads(ajaxdata)
    msg = '发送成功'
    code = False
    mail = ajaxdata['mail']
    if mail == None or mail == '':
        return json.dumps({
            'code': code,
            'msg': '奇怪的错误'
        })
    type = ajaxdata['type']
    user = User.query.filter_by(email=mail).first()
    if type == 'register':
        if user:
            msg = '该邮箱已经注册过了'
            return json.dumps({
                'code': code,
                'msg': msg
            })
        else:
            code = True
    elif type == 'forget':
        if user:
            code = True
        else:
            msg = '用户邮箱不存在，请返回注册或重新输入'
            return json.dumps({
                'code': code,
                'msg': msg
            })
    num = get_num()
    session['mailcode'] = num
    session['email'] = mail
    # print(session.get('mailcode'))
    send_mail(user=mail, message=num)
    return json.dumps({
        'code': code,
        'msg': msg
    })


# ueditor上传文件的方法
@home.route('/upload', methods=["GET", "POST", "OPTIONS"])
def upload():
    mimetype = 'application/json'
    result = {}
    action = request.args.get('action')
    with open(os.path.join(app.config['static'], 'ueditor/php/config.json'), 'r', encoding='utf-8') as fp:
        try:
            CONFIG = re.sub('\/\*.*\*\/', '', fp.read())
            CONFIG = json.loads(CONFIG)
        except:
            CONFIG = {}
    if action == 'config':
        result = CONFIG
    elif action in ('uploadimage', 'uploadfile', 'uploadvideo'):
        # 图片、文件、视频上传
        if action == 'uploadimage':
            fieldName = CONFIG.get('imageFieldName')
            config = {
                "pathFormat": CONFIG['imagePathFormat'],
                "maxSize": CONFIG['imageMaxSize'],
                "allowFiles": CONFIG['imageAllowFiles']
            }
        elif action == 'uploadvideo':
            fieldName = CONFIG.get('videoFieldName')
            config = {
                "pathFormat": CONFIG['videoPathFormat'],
                "maxSize": CONFIG['videoMaxSize'],
                "allowFiles": CONFIG['videoAllowFiles']
            }
        else:
            fieldName = CONFIG.get('fileFieldName')
            config = {
                "pathFormat": CONFIG['filePathFormat'],
                "maxSize": CONFIG['fileMaxSize'],
                "allowFiles": CONFIG['fileAllowFiles']
            }
        # print(config)
        if fieldName in request.files:
            field = request.files[fieldName]
            uploader = Uploader(field, config, app.static_folder)
            result = uploader.getFileInfo()
        else:
            result['state'] = '上传接口出错'

    elif action in ('uploadscrawl'):
        # 涂鸦上传
        fieldName = CONFIG.get('scrawlFieldName')
        config = {
            "pathFormat": CONFIG.get('scrawlPathFormat'),
            "maxSize": CONFIG.get('scrawlMaxSize'),
            "allowFiles": CONFIG.get('scrawlAllowFiles'),
            "oriName": "scrawl.png"
        }
        if fieldName in request.form:
            field = request.form[fieldName]
            uploader = Uploader(field, config, app.static_folder, 'base64')
            result = uploader.getFileInfo()
        else:
            result['state'] = '上传接口出错'

    elif action in ('catchimage'):
        config = {
            "pathFormat": CONFIG['catcherPathFormat'],
            "maxSize": CONFIG['catcherMaxSize'],
            "allowFiles": CONFIG['catcherAllowFiles'],
            "oriName": "remote.png"
        }
        fieldName = CONFIG['catcherFieldName']

        if fieldName in request.form:
            # 这里比较奇怪，远程抓图提交的表单名称不是这个
            source = []
        elif '%s[]' % fieldName in request.form:
            # 而是这个
            source = request.form.getlist('%s[]' % fieldName)
        _list = []
        for imgurl in source:
            uploader = Uploader(imgurl, config, app.static_folder, 'remote')
            info = uploader.getFileInfo()
            _list.append({
                'state': info['state'],
                'url': info['url'],
                'original': info['original'],
                'source': imgurl,
            })
        result['state'] = 'SUCCESS' if len(_list) > 0 else 'ERROR'
        result['list'] = _list

    else:
        result['state'] = '请求地址出错'
    result = ast.literal_eval(str(result).replace("{}".format(request.host_url)[:-1], ''))
    # print(result)
    result = json.dumps(result)
    if 'callback' in request.args:
        callback = request.args.get('callback')
        if re.match(r'^[\w_]+$', callback):
            result = '%s(%s)' % (callback, result)
            mimetype = 'application/javascript'
        else:
            result = json.dumps({'state': 'callback参数不合法'})

    res = make_response(result)
    res.mimetype = mimetype
    res.headers['Access-Control-Allow-Origin'] = '*'
    res.headers['Access-Control-Allow-Headers'] = 'X-Requested-With,X_Requested_With'
    return res


# 接收改变用户信息的json数据
@home.route('/changeuser', methods=["GET", "POST"])
def changeuser():
    if request.method == 'POST':
        retype = request.form.get('retype')
        # print(retype)
        username = request.form.get('username')
        password = my_key(request.form.get('password'))
        email = request.form.get('email')
        # print(email)
        if retype == 'add':
            user = User.query.filter_by(username=username).first()
            if user:
                msg = '用户名已存在'
                return json.dumps({'msg': msg})
            else:
                user = User.query.filter_by(email=email).first()
                if user:
                    msg = '邮箱已存在'
                    return json.dumps({'msg': msg})
                else:
                    face = request.files.get('facefile')
                    if bool(face):
                        facename = uuid.uuid4().hex + '.' + face.filename.split('.')[-1]
                        face.save(app.config["static"] + 'upload/' + facename)
                        user = User(username=username, password=password, email=email, face=facename,
                                    addtime=now_date())
                    else:
                        user = User(username=username, password=password, email=email, addtime=now_date())
                    db.session.add(user)
                    db.session.commit()
                msg = '添加成功'
                return json.dumps({'msg': msg})
    else:
        return None


@home.route('/ueditor', methods=["GET", "POST"])
def ueditor():
    return render_template('home/ueditor.html')


@home.route('/addnew', methods=["GET", "POST"])
def addnew():
    new = request.get_data()
    new = json.loads(new)
    id = new['id']
    title = new['title']
    text = new['text'].replace("{}".format(request.host_url)[:-1], '')
    nowdate = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = "insert into new(id,title,text,createtime,altertime) values(default,'{}','{}','{}','{}')".format(title,
                                                                                                           text,
                                                                                                           nowdate,
                                                                                                           nowdate)
    db.session.execute(sql)
    db.session.commit()
    return '上传成功'


# 文章详情页面
@home.route('/onenew/<int:id>', methods=["GET", "POST"])
def onenew(id=None):
    data = {}
    if id == None:
        abort(404)
    else:
        new = New.query.outerjoin(User, User.id == New.uid).outerjoin(Type, Type.id == New.tid).filter(
            New.id == id
        ).first()
        # print(new)
        if bool(new):
            if new.clicknum == None:
                new.clicknum = 1
            else:
                new.clicknum += 1
            data['new'] = new
            previous = New.query.filter(New.id < id).order_by(New.id.desc()).first()
            if previous:
                data['previous'] = previous
            else:
                data['previous'] = None
            next = New.query.filter(New.id > id).first()
            if next:
                data['next'] = next
            else:
                data['next'] = None
            others = New.query.filter_by(tid=new.tid).order_by(New.createtime.desc()).limit(8).all()
            data['others'] = others
            db.session.add(new)
            db.session.commit()
            return render_template('home/new.html', data=data)
        else:
            abort(404)


# 主页
@home.route("/index", methods=["GET"])
@home.route("/", methods=["GET"])
def index():
    kw = request.args.get('kw', '')
    page = request.args.get('page', '1')
    try:
        page = int(page)
    except ValueError:
        abort(404)
    if kw:
        newdata = New.query.outerjoin(User, User.id == New.uid).outerjoin(
            Type, Type.id == New.tid).filter(New.title.like("%{}%".format(kw))).order_by(
            New.createtime.desc()
        ).paginate(page=page, per_page=10)
    else:
        newdata = New.query.outerjoin(User, User.id == New.uid).outerjoin(
            Type, Type.id == New.tid).order_by(
            New.createtime.desc()
        ).paginate(page=page, per_page=10)
    return render_template("home/index.html", pagedata=newdata, page=page, kw=kw)


@home.route('/deletenew', methods=["GET", "POST"])
def deletenew():
    id = request.get_data()
    id = json.loads(id)
    nid = id['id']
    new = New.query.get_or_404(nid)
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
    db.session.delete(new)
    db.session.commit()
    return '删除成功'


# 退出登录
@home.route('/logout', methods=["GET", "POST"])
@home_login_req
def logout():
    code = False
    if request.method == 'POST':
        ajdata = request.get_data(as_text=True)
        if ajdata == 'out':
            session.pop('uid')
            session.pop('uname')
            code = True
    return jsonify({'code': code})


# 个人信息
@home.route('/me', methods=["GET", "POST"])
@home_login_req
def me():
    if request.method == 'POST':
        ajdata = request.get_data(as_text=True)
        redata = {}
        if ajdata == 'me':
            user = User.query.filter_by(id=session.get('uid')).first()
            redata['face'] = user.face
            redata['userid'] = user.id
            redata['username'] = user.username
            redata['signature'] = user.signature
            redata['email'] = user.email
        return jsonify(redata)
    return render_template('home/me.html')


# 修改个人信息
@home.route('/changeme', methods=["GET", "POST"])
@home_login_req
def changeme():
    if request.method == 'POST':
        code = False
        msg = ''
        userid = request.form.get('userid')
        if userid != str(session.get('uid')):
            msg = '登录信息过期'
            return jsonify({'code': code, 'msg': msg})
        user = User.query.get_or_404(userid)
        username = request.form.get('username')
        if username != user.username:
            user1 = User.query.filter_by(username=username).first()
            if user1:
                msg = '这个名字有人用了，换个试试'
                return jsonify({'code': code, 'msg': msg})
            else:
                user.username = username
        email = request.form.get('email')
        if email != user.email:
            user2 = User.query.filter_by(email=email).first()
            if user2:
                msg = '这个邮箱被注册了'
                return jsonify({'code': code, 'msg': msg})
            else:
                user.email = email
        signature = request.form.get('signature')
        # print(signature)
        user.signature = signature
        face = request.files.get('facefile')
        if bool(face):
            oldname = user.face
            if oldname:
                oldfile = app.config["static"] + 'upload/' + oldname
                if os.path.isfile(oldfile):
                    os.remove(oldfile)
            newname = uuid.uuid4().hex + '.' + face.filename.split('.')[-1]
            face.save(app.config["static"] + 'upload/' + newname)
            user.face = newname
        db.session.add(user)
        db.session.commit()
        session['uname'] = username
        code = True
        msg = '修改成功'
        return jsonify({'code': code, 'msg': msg})


# 修改密码
@home.route('/changekw', methods=["GET", "POST"])
@home_login_req
def changekw():
    if request.method == 'POST':
        code = False
        ajdata = json.loads(request.get_data())
        old = ajdata['old']
        new = ajdata['new']
        user = User.query.filter_by(id=session.get('uid')).first()
        if user.password == my_key(old):
            user.password = my_key(new)
            db.session.add(user)
            db.session.commit()
            session.pop('uid')
            session.pop('uname')
            msg = '修改成功，重新登录'
            code = True
            return jsonify({'code': code, 'msg': msg})
        else:
            msg = '原有密码输入错误'
            return jsonify({'code': code, 'msg': msg})

    return render_template('home/changekw.html')


# 返回最新发表的文章数据
@home.route('/newnews', methods=["POST"])
def newnews():
    ajdata = request.get_data(as_text=True)
    num = int(ajdata)
    newdata = New.query.order_by(New.createtime.desc()).limit(num)
    redata = []
    for i in newdata:
        result = {}
        result['title'] = i.title
        result['id'] = i.id
        result['cover'] = i.cover
        redata.append(result)
    # print(redata)
    return jsonify(redata)


# 返回点击量最高的文章数据
@home.route('/click', methods=["POST"])
def click():
    ajdata = request.get_data(as_text=True)
    num = int(ajdata)
    newdata = New.query.order_by(New.clicknum.desc()).limit(num)
    redata = []
    for i in newdata:
        result = {}
        result['title'] = i.title
        result['id'] = i.id
        result['cover'] = i.cover
        result['time'] = str(i.createtime)
        redata.append(result)
    # print(redata)
    return jsonify(redata)


# 返回文章的所有类型
@home.route('/types', methods=["POST"])
def types():
    ajdata = request.get_data(as_text=True)
    redata = []
    if ajdata == 'all':
        typedata = Type.query.all()
        for i in typedata:
            result = {}
            result['name'] = i.name
            result['id'] = i.id
            redata.append(result)
        # print(redata)
    return jsonify(redata)


# 不同类型的文章
@home.route('/newtype', methods=['GET', 'POST'])
@home.route('/newtype/', methods=['GET', 'POST'])
@home.route('/newtype/<int:id>', methods=['POST', 'GET'])
def newtype(id=None):
    page = request.args.get('page', 1)
    try:
        page = int(page)
    except ValueError:
        abort(404)
    if id == None:
        typename = '所有类型'
        newdata = newdata = New.query.outerjoin(User, User.id == New.uid).outerjoin(
            Type, Type.id == New.tid).order_by(
            New.tid.desc()
        ).paginate(page=page, per_page=10)
    else:
        typedata = Type.query.get_or_404(id)
        typename = typedata.name
        newdata = newdata = New.query.outerjoin(User, User.id == New.uid).outerjoin(
            Type, Type.id == New.tid).filter(New.tid == id).order_by(
            New.createtime.desc()
        ).paginate(page=page, per_page=10)
    return render_template('home/newtype.html', pagedata=newdata, typename=typename, page=page)


# 用户分享文章
@home.route('/share', methods=['POST', 'GET'])
@home_login_req
def share():
    typedata = Type.query.all()
    if request.method == 'POST':
        typeid = request.form.get('type')
        userid = session.get('uid')
        # ajdata = json.loads(ajdata)
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
                uid=userid,
                tid=typeid
            )
        else:
            new = New(
                title=title,
                text=text,
                createtime=now_date(),
                uid=userid,
                tid=typeid
            )
        db.session.add(new)
        db.session.commit()
        return '发布成功'
    return render_template('home/share.html', typedata=typedata)


# 用户个人信息
@home.route('/usermsg/<int:id>', methods=['POST', 'GET'])
def usermsg(id=None):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1)
    try:
        page = int(page)
    except ValueError:
        abort(404)
    newdata = New.query.join(User, User.id == New.uid).join(
        Type, Type.id == New.tid).filter(New.uid == user.id).order_by(
        New.createtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template('home/usermsg.html', user=user, pagedata=newdata)


# 返回随机的图片
@home.route('/cgimg', methods=['POST'])
def cgimg():
    if request.method == 'POST':
        imgnum = int(request.get_data(as_text=True))
        imgs = os.listdir(app.config['static'] + 'cgimg')
        imglist = random.sample(imgs, imgnum)
    return jsonify(imglist)


# 返回随机的带图片的文章
@home.route('/cgnew', methods=['POST'])
def cgnew():
    redata = []
    if request.method == 'POST':
        newnum = int(request.get_data(as_text=True))
        sql = "select new.id,new.title,new.cover,type.name from new left join type on type.id=new.tid where new.id>=((select floor(rand()*(select max(id) from new)))+(select min(id) from new)) and cover!='null' limit {};".format(
            newnum)
        newdata = db.session.execute(sql)
        # print(newdata)
        for i in newdata:
            result = {}
            result['id'] = i.id
            result['title'] = i.title
            result['cover'] = i.cover
            result['name'] = i.name
            redata.append(result)
        # print(redata)
    return jsonify(redata)


# 检查消息中是否有@，确认@的用户是否存在，有则替换
def change_text(text):
    text = text.replace('<', '&lt;').replace('>', '&gt;')
    all_user = re.findall('@.*? ', text)
    all_user = list(set(all_user))
    for i in all_user:
        uname = i[1:-1]
        user = User.query.filter(User.username == uname).first()
        if user:
            text = text.replace(i, '<a href="/usermsg/{}">{}</a>'.format(user.id, i))
    return text


# 上传消息
@home.route('/getcom', methods=['POST'])
@home_login_req
def getcom():
    msg = '上传失败'
    if request.method == 'POST':
        ajdata = request.get_data()
        ajdata = json.loads(ajdata)
        if ajdata['type'] == 'f':
            nid = ajdata['nid']
            fart = Fatherart(
                text=change_text(ajdata['com']),
                viewtime=now_date(),
                uid=session.get('uid'),
                nid=nid
            )
            new = New.query.get_or_404(nid)
            if bool(new.comnum):
                new.comnum = new.comnum + 1
            else:
                new.comnum = 1
            db.session.add(fart)
            db.session.add(new)
            db.session.commit()
            msg = '发表成功'
        elif ajdata['type'] == 's':
            fid = ajdata['fid']
            nid = ajdata['nid']
            new = New.query.get_or_404(nid)
            fart = Fatherart.query.get_or_404(fid)
            sart = Sonart(
                text=change_text(ajdata['com']),
                viewtime=now_date(),
                uid=session.get('uid'),
                fid=fid
            )
            if bool(new.comnum):
                new.comnum = new.comnum + 1
            else:
                new.comnum = 1
            if bool(fart.viewcount):
                fart.viewcount = fart.viewcount + 1
            else:
                fart.viewcount = 1
            db.session.add(fart)
            db.session.add(new)
            db.session.add(sart)
            db.session.commit()
            msg = '发表成功'
    return msg


# 返回评论数据
@home.route('/comview', methods=['POST'])
def comview():
    redata = []
    hasnext = False
    if request.method == 'POST':
        ajdata = request.get_data()
        ajdata = json.loads(ajdata)
        nid = ajdata['nid']
        page = ajdata['page']
        try:
            page = int(page)
        except ValueError:
            return redata
        fdata = Fatherart.query.join(User, User.id == Fatherart.uid).filter(
            Fatherart.nid == nid
        ).order_by(
            Fatherart.viewtime
        ).paginate(page=1, per_page=10 * page)
        # print(fdata.total)
        if fdata.total > 10 * page:
            hasnext = True
        for i in fdata.items:
            result = {}
            result['fid'] = i.id
            result['uid'] = i.user.id
            result['fname'] = i.user.username
            result['ftext'] = i.text
            result['ftime'] = str(i.viewtime)
            if i.viewcount == None:
                result['fnum'] = 0
            else:
                result['fnum'] = i.viewcount
            sondata = []
            sdata = Sonart.query.join(User, User.id == Sonart.uid).filter(Sonart.fid == i.id).order_by(
                Sonart.viewtime
            ).all()
            for j in sdata:
                sresult = {}
                sresult['sid'] = j.user.id
                sresult['stext'] = j.text
                sresult['sname'] = j.user.username
                sresult['stime'] = str(j.viewtime)
                sondata.append(sresult)
            result['sondata'] = sondata
            redata.append(result)
        # print(redata)
    return jsonify({'msg': redata, 'hasnext': hasnext})
