import argparse

class Commands(object):
  def __init__(self):
      self.parser = argparse.ArgumentParser()

      self.parser.add_argument('list-users', help="Display list of users")
      self.parser.add_argument('list-groups', help="Display list of groups")
      self.parser.add_argument('list-systems', help="Display Systems managed by Yoked")
      self.parser.add_argument('list-roles', help="Display Roles associated to systems")
      self.parser.parse_args()

  def run(self):
    print "Hello!"
