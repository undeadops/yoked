from os.path import expanduser
import ConfigParser

config = ConfigParser.ConfigParser()
try:
    config.read(['.oxen', expanduser("~/.oxen")])
    #apihost = config.get('main', 'apihost')
except OSError, e:
    print "Error: ~/.oxen Config file does not exist"
    print "Create Config File before proceding"
    sys.exit(2)
