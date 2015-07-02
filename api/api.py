from flask import Flask, request, jsonify

from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy_utils.types import JSONType
from flask import render_template
import logging
import json
import datetime
# import pprint

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///yoked.db'

db = SQLAlchemy(app)

file_handler = logging.FileHandler('yoked.log')
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

# ------------------------------------------------
# Database Models
# ------------------------------------------------
group_linking=db.Table('group_linking',
                       db.Column('group_id', db.Integer,db.ForeignKey('group.id'), nullable=False),
                       db.Column('user_id', db.Integer,db.ForeignKey('user.id'), nullable=False),
                       db.PrimaryKeyConstraint('group_id', 'user_id') )

group_instance=db.Table('group_instances',
                       db.Column('group_id', db.Integer,db.ForeignKey('group.id'), nullable=False),
                       db.Column('instance_id', db.Integer,db.ForeignKey('instance.id'), nullable=False),
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
    groups = []
    users = {}

    for g in instance.member_of:
        groups.append(g.id)

    for g in groups:
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
            users.update({ user.username: u })

    return users


# ----------------------------------------------------------------
# API Endpoints
# ----------------------------------------------------------------

# TODO: Change up API application to use a blueprint to separate versions (like v1)

@app.route('/v1/status', methods=['POST'])
def status():
    data = json.loads(request.data)

    instance = Instance.query.filter_by(instance_name = data['system']['name']).first()
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
    message = { 'status': "OK",
                'users': users }
    resp = jsonify(message)
    resp.status_code = 201
    return resp


@app.route('/v1/instances', methods=['GET'])
def instances():
    results = Instance.query.all()
    instances = []
    for result in results:
        groups = []
        for g in result.member_of:
            groups.append({ 'id': g.id, 'name': g.name })
        i = {
            'id': result.id,
            'name': result.instance_name,
            'instance_id': result.instance_id,
            'net': result.instance_net,
            'date_created': result.date_created,
            'last_seen': result.date_last,
            'groups': groups
        }
        instances.append(i)
    return jsonify({'Instances': instances })


@app.route('/v1/groups', methods=['GET', 'POST', 'PUT'])
def groups():
    if request.method == 'GET':
        results = Group.query.all()
        groups = []
        for result in results:
            users = []
            for u in result.users:
                d = {'id': u.id,
                     'name': u.name,
                     'username': u.username,
                     'email': u.email,
                     'shell': u.shell.path,
                     'access': u.access.name,
                     'ssh_pub_key': u.ssh_pub_key
                }
                users.append(d)
            group = {'name': result.name,
                     'users': users
                    }
            groups.append(group)
        return jsonify({'groups': groups })


@app.route('/v1/users', methods=['GET', 'POST', 'PUT'])
def api_users():
    if request.method == 'GET':
        results = User.query.all()
        users = []
        for result in results:
            groups = []
            for g in result.member_of:
                d = {'id': g.id,
                     'name': g.name }
                groups.append(d)
            user = {'name': result.name,
                    'username': result.username,
                    'email': result.email,
                    'shell': result.shell.path,
                    'access': result.access.name,
                    'ssh_pub_key': result.ssh_pub_key,
                    'groups': groups
            }
            users.append(user)
        return jsonify({'users': users })


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
    app.run(debug=True, host='0.0.0.0')
