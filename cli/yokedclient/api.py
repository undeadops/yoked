import requests
import json
from .cli import __version__
from . import config

class API:
    def __init__(self):
        """
        Wrapper around Requests library for the yoke rest API
        """
        self.version = __version__
        self.requests = requests
        self.apihost = config.get('main', 'apihost')
        self.headers = {'user-agent': 'yoked-cli/%s' % self.version}

    def get_systems_list(self):
        endpoint = "%s/v1/instances" % self.apihost
        r = self.requests.get(endpoint, headers=self.headers)
        return r

    def post_add_user(self, payload):
        endpoint = "%s/v1/user" % self.apihost
        r = self.requests.post(endpoint, data=payload, headers=self.headers)
        return r
