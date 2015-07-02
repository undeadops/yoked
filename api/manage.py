# manage.py
from flask.ext.script import Manager
from api import app
from api import db

from os.path import isfile
from os import unlink

manager = Manager(app)

@manager.command
def reset_db():
    if isfile('yoked.db'):
        unlink('yoked.db')
    db.create_all()


if __name__ == '__main__':
    manager.run()