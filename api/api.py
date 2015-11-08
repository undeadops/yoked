from flask import Flask, request, jsonify
from flask import abort, url_for

from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy_utils.types import JSONType
from flask import render_template
from config import BaseConfig
import logging
import json
import datetime


app = Flask(__name__)
app.config.from_object(BaseConfig)

db = SQLAlchemy(app)

file_handler = logging.FileHandler('yoked.log')
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)


# ------------------------------------------------
# Database house keeping, clean up open sessions
@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()

# ------------------------------------------------
# Database Models
# ------------------------------------------------
group_linking=db.Table('group_linking',
                       db.Column('group_id', db.Integer, db.ForeignKey('group.id'), nullable=False),
                       db.Column('user_id', db.Integer, db.ForeignKey('user.id'), nullable=False),
                       db.PrimaryKeyConstraint('group_id', 'user_id'))

group_instance=db.Table('group_instances',
                       db.Column('group_id', db.Integer, db.ForeignKey('group.id'), nullable=False),
                       db.Column('instance_id', db.Integer, db.ForeignKey('instance.id'), nullable=False),
                       db.PrimaryKeyConstraint('group_id', 'instance_id'))


class Instance(db.Model):
    __tablename__ = 'instance'

    id = db.Column(db.Integer, primary_key=True)
    instance_id = db.Column(db.String(32))
    instance_name = db.Column(db.String(256))
    instance_role = db.Column(db.String(64), default='Unknown')
    instance_net = db.Column(JSONType)
    date_created = db.Column(db.DateTime(), default=datetime.datetime.now())
    date_last = db.Column(db.DateTime())
    post_data = db.Column(JSONType)
    member_of = db.relationship('Group', secondary=group_instance, backref='instances')

    def __init__(self, name=None):
        self.instance_name = name
        self.date_created = datetime.datetime.now()

    def has_groups(self):
        if len(self.member_of) > 0:
            return True


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    username = db.Column(db.String(32))
    email = db.Column(db.String(164))
    shell_id = db.Column(db.Integer, db.ForeignKey('shell.id'))
    shell = db.relationship('Shell')
    access_id = db.Column(db.Integer, db.ForeignKey('access.id'))
    access = db.relationship('Access')
    ssh_pub_key = db.Column(db.UnicodeText)
    member_of = db.relationship('Group', secondary=group_linking, backref='users')

    def __repr__(self):
        return '<User %r>' % self.name


class Group(db.Model):
    __tablename__ = 'group'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))


class Role(db.Model):
    __tablename__ = 'role'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    description = db.Column(db.String(256))


class Access(db.Model):
    __tablename__ = 'access'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    description = db.Column(db.String(128))

    def __repr__(self):
        return "<Access(name=%s description='%s')>" % (self.name, self.description)


class Shell(db.Model):
    __tablename__ = 'shell'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(8))
    path = db.Column(db.String(32))

    def __repr__(self):
        return "<Shell(name=%s path=%s)>" % (self.name, self.path)

# -----------------------------------------------------------------
# Supporting Functions
# -----------------------------------------------------------------


def get_members(instance):
    """
    Return Users than are part of the groups instance is a member_of
    :param instance:
    :return dict(users):
    """
    mygroups = []
    myusers = {}

    for g in instance.member_of:
        mygroups.append(g.id)

    for g in mygroups:
        group = Group.query.get(g)
        for user in group.users:
            u = {
                'name': user.name,
                'username': user.username,
                'shell': user.shell.path,
                'email': user.email,
                'access': user.access.name,
                'ssh_pub_key': user.ssh_pub_key
            }
            myusers.update({user.username: u})

    return myusers


def json_user(myuser):
    u = {'id': myuser.id,
         'name': myuser.name,
         'username': myuser.username,
         'email': myuser.email,
         'shell': myuser.shell.path,
         'access': myuser.access.name,
         'ssh_pub_key': myuser.ssh_pub_key}
    return u


def json_group(group):
    users = []
    for u in group.users:
        d = {'id': u.id,
             'name': u.name,
             'username': u.username,
             'email': u.email,
             'shell': u.shell.path,
             'access': u.access.name,
             'ssh_pub_key': u.ssh_pub_key
             }
        users.append(d)
    g = {'name': group.name,
         'id': group.id,
         'users': users
         }
    return g


# ----------------------------------------------------------------
# API Endpoints
# ----------------------------------------------------------------

# TODO: Change up API application to use a blueprint to separate versions (like v1)
# TODO: Whats the Proper error codes to issue for status', fix error stats and make sure return values are proper
# TODO: Ensure replies are consistent across function endpoints

@app.route('/v1/status', methods=['POST'])
def status():
    data = json.loads(request.data)

    instance = Instance.query.filter_by(instance_name=data['system']['name']).first()
    if instance is None:
        i = Instance()
        i.instance_name = data['system']['name']
        i.instance_net = data['system']['net']
        i.date_last = datetime.datetime.now()
        i.post_data = data
        db.session.add(i)
    else:
        instance.instance_net = data['system']['net']
        instance.date_last = datetime.datetime.now()
        instance.post_data = data
    db.session.commit()

    # Check for Pending processes to run in DB/MessageQueue?
    # Return users that should be setup on system.
    instance = Instance.query.filter_by(instance_name = data['system']['name']).first()

    if instance.has_groups:
        users = get_members(instance)
    else:
        users = {}
    message = {'status': "OK",
               'users': users}
    resp = jsonify(message)
    resp.status_code = 201
    resp.headers['location'] = url_for('get_instances', instance_id=instance.id)
    return resp


@app.route('/v1/instance/<int:instance_id>', methods=['GET'])
def get_instances(instance_id):
    if request.method == 'GET':
        inst = Instance.query.get(instance_id)
        resp = jsonify()
        resp.status.code = 200
        resp.headers['location'] = url_for('get_instances', instance_id=inst.id)
        return resp


@app.route('/v1/instances', methods=['GET'])
def instances():
    results = Instance.query.all()
    myinsts = []
    for result in results:
        groups = []
        for g in result.member_of:
            groups.append({'id': g.id, 'name': g.name})
        i = {
            'id': result.id,
            'name': result.instance_name,
            'instance_id': result.instance_id,
            'net': result.instance_net,
            'date_created': result.date_created,
            'last_seen': result.date_last,
            'groups': groups
        }
        myinsts.append(i)
    resp = jsonify({"instances": myinsts})
    resp.status_code = 200
    resp.headers['location'] = url_for('instances')
    return resp


@app.route('/v1/groups', methods=['GET'])
def groups():
    groups = Group.query.all()
    active_groups = []
    for group in groups:
        g = json_group(group)
        active_groups.append(g)
    resp = jsonify({'groups': active_groups})
    resp.status_code = 200
    resp.headers['location'] = url_for('groups')
    return resp


@app.route('/v1/group', methods=['POST'])
def add_groups():
    if request.method == 'POST':
        if not request.json or not 'name' in request.json:
            abort(400)
        g = Group(name=request.json['name'])
        db.session.add(g)
        db.session.commit()
        g = Group.query.filter_by(name=request.json['name'])
        if g:
            mygroup = json_group(g)
            resp = jsonify({"groups": mygroup})
            resp.status_code = 201
            resp.headers['location'] = url_for('get_group', group_id=g.id)
            return resp
        else:
            resp = jsonify({"status": 501, "message": "There was an error creating the group"})
            resp.status_code = 501
            resp.headers['location'] = url_for('groups')
            return resp
    else:
        return abort(400)


@app.route('/v1/group/<int:group_id>', methods=['GET', 'DELETE'])
def get_group(group_id):
    if request.method == 'GET':
        g = Group.query.get(group_id)
        if g:
            group = json_group(g)
            return jsonify({"groups": group})
        else:
            return abort(404)
    if request.method == 'DELETE':
        if Group.query.filter_by(id=group_id).delete():
            db.session.commit()
            return jsonify({"Status": "OK"})
        else:
            return abort(404)


@app.route('/v1/users', methods=['GET'])
def list_users():
    user_results = User.query.all()
    users = []
    for u in user_results:
        user_groups = []
        for g in u.member_of:
            d = {'id': g.id,
                 'name': g.name}
            user_groups.append(d)
        users.append(json_user(u))
    return jsonify({'users': users})


@app.route('/v1/user', methods=['POST'])
def users_add():
    if request.json:
        shell = Shell.query.filter_by(name=request.json['shell']).first()
        access = Access.query.filter_by(name=request.json['access']).first()
        user = User()
        user.name = request.json['name']
        user.username = request.json['username']
        user.email = request.json['email']
        user.shell = shell
        user.access = access
        user.ssh_pub_key = request.json['ssh_pub_key']
        db.session.add(user)
        db.session.commit()
        u = User.query.filter_by(name=request.json['name']).first()
        resp = jsonify({"status": 201, "message": "Success!"})
        resp.status_code = 201
        resp.headers['location'] = url_for('users', user_id=u.id)
        return resp
    else:
        return abort(404)


@app.route('/v1/user/<int:user_id>', methods=['GET', 'DELETE', 'PUT'])
def users(user_id):
    if request.method == 'GET':
        u = User.query.get(user_id)
        if u:
            user = json_user(u)
            resp = jsonify({'status': 200, 'message': 'OK', 'users': user})
            resp.status_code = 200
            resp.headers['location'] = url_for('users', user_id=u.id)
            return resp
        else:
            return abort(404)
    elif request.method == 'DELETE':
        if User.query.filter_by(id=user_id).delete():
            db.session.commit()
            resp = jsonify({'status': 201, 'message': "User Deleted"})
            resp.status_code = 201
            resp.headers['location'] = url_for('list_users')
            return resp
        else:
            return abort(404)
    elif request.method == 'PUT':
        u = User.query.get(user_id)
        if u and request.json:
            if request.json['name']:
                u.name = request.json['name']
            if request.json['email']:
                u.email = request.json['email']
            if request.json['ssh_pub_key']:
                u.ssh_pub_key = request.json['ssh_pub_key']
            if request.json['shell']:
                s = Shell.query.filter_by(name=request.json['shell']).first()
                u.shell = s
            if request.json['access']:
                a = Access.query.filter_by(name=request.json['access']).first()
                u.access = a
            db.session.add(u)
            db.session.commit()
            resp = jsonify({"status": 201, "message": "User Updated"})
            resp.status_code = 201
            resp.headers['location'] = url_for('users', user_id=u.id)
            return resp
        else:
            return abort(400)


@app.route('/v1/roles', methods=['GET'])
def roles():
    return jsonify({'roles': Role.query.all()})


# -------------------------------------------------
# Render for HTML not API
# -------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0')
