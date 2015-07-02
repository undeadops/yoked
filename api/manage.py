# manage.py
from flask.ext.script import Manager
from api import app
from api import db
from api import Access
from api import Shell

from os.path import isfile
from os import unlink

manager = Manager(app)


@manager.command
def reset_db():
    if isfile('yoked.db'):
        unlink('yoked.db')
    if isfile('yoked.log'):
        unlink('yoked.log')
    db.create_all()
    # Now Setup some basic values in the DB
    access_admin = Access(name='admin',
                          description='Full Admin Access')
    access_user = Access(name='user',
                         description='Regular User Access')
    db.session.add(access_admin)
    db.session.commit()
    db.session.add(access_user)
    db.session.commit()

    shell_zsh = Shell(name='zsh',
                      path='/usr/bin/zsh')
    shell_bash = Shell(name='bash',
                       path='/bin/bash')
    db.session.add(shell_zsh)
    db.session.commit()
    db.session.add(shell_bash)
    db.session.commit()

if __name__ == '__main__':
    manager.run()
