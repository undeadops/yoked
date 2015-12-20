from os.path import expanduser,isfile
import sys
import json
import pprint
import ConfigParser
from . import api
from . import config

class Commands(object):
  def __init__(self):
      self.config = config
      self.api = api.API()

  def list_users(self):
      users = self.api.get_user_list()
      print "Username | Name | Status"
      for user in users:
          print "%s | %s | %s" % (user['username'],user['name'],user['status'])

  def add_user(self, args):
      username = args.username
      email = args.email
      name = args.name
      shell = 'bash' if args.shell is None else args.shell
      is_admin = False if args.admin is None else True

      if isfile(args.sshpubkey):
          try:
              sshkey = open(args.sshpubkey).read()
          except:
              print "Unexpected error:", sys.exc_info()[0]
              print "Error opening %s: %s" % (args.sshpubkey)
              sys.exit(2)
      else:
          sshkey = args.sshpubkey

      if is_admin:
          access = 'admin'
      else:
          access = 'user'

      payload = { "name": name,
                "username": username,
                "email": email,
                "shell": shell,
                "access": access,
                "sshkey": sshkey }
      result = self.api.post_add_user(payload)
      if result.status_code == '201':
          print "Successfully added %s to sytem" % username

  def list_groups(self):
      print "List Groups...."

  def list_roles(self):
      print "list roles..."

  def list_systems(self):
      result = self.api.get_systems_list()
      if result.status_code == '200':
          systems = result.json()
          for inst in systems['instances']:
              print "%s\t\t%s" % (inst['name'], inst['groups'])
      else:
          print "There was an error retriving Systems List (%s)" % r.status_code
          sys.exit(2)

  def run(self):
      print "Hello!"

  def config_create(self):
    cfg = ConfigParser.ConfigParser()
    apihost = raw_input("Yoked API Server (eg: http://localhost): ")
    # TODO: Proper handling would include validation of URL/Host Input
    cfg.add_section('main')
    cfg.set('main', 'apihost', apihost)
    with open(expanduser("~/.oxen"), 'wb') as fh:
        cfg.write(fh)
