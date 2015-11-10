from os.path import expanduser
import ConfigParser
import sys

class Commands(object):
  def __init__(self):
      self.config = ConfigParser.ConfigParser()
      try:
          self.config.read(expanduser("~/.oxen"))
          self.apihost = self.config.get('main', 'apihost')
      except OSError, e:
          print "Error: ~/.oxen Config file does not exist"
          print "Create Config File before proceding"
          sys.exit(2)


  def list_users(self):
      print "Listing users..."

  def list_groups(self):
      print "List Groups...."

  def list_roles(self):
      print "list roles..."

  def list_systems(self):
      print "listing systems"

  def run(self):
      print "Hello!"

  def config_create(self):
    cfg = ConfigParser.ConfigParser()
    apihost = input("Yoked API Server (eg: http://localhost): ")
    # TODO: Proper handling would include validation of URL/Host
    cfg.add_section('main')
    cfg.set('main', 'apihost', apihost)
    with open(expanduser("~/.oxen"), 'wb') as fh:
        cfg.write(fh)
    
