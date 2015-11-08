#!/usr/bin/env python

import time, sys, socket, json
import os
import requests
import logging
import subprocess
import pprint
import ConfigParser

class Oxen:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_dead = False
        self.system = {}
        # TODO: Use config file and override with environment vars for URL
        try:
            self.config = ConfigParser.ConfigParser()
            self.config.read('/etc/oxen.ini')
        except OSError, e:
            self.logger.critical("Unable to read config file: /etc/oxen.ini")
            self.logger.critical("Error: %s" % e)
        self.api_host = self.config.get('main', 'apihost')
        self.endpoint = 'http://%s/v1/status' % self.api_host



    def gather_users(self):
        """
        Gather Current Users added with yoked
        :return:[yoked-users]
        """
        users = []
        with open('/etc/passwd') as f:
            for line in f:
                (username, p, uid, gid, gecos, homedir, shell) = line.split(':')
                name = gecos.split(',')[0]
                if name.startswith('yoked-'):
                    #u = {
                    #    'username': username,
                    #    'name': name,
                    #    'homedir': homedir,
                    #    'shell': shell
                    #}
                    users.append(username)
        return users

    def gather_system(self):
        """
        Get System Information
        """
        try:
            import psutil
            PS = True
        except:
            self.logger.info('Could not Import psutil')
            self.logger.info('pip install psutil for Network Interface Output')
            PS = False

        interfaces = {}
        if PS:
            netaddr = psutil.net_if_addrs()
            for n, a in netaddr.iteritems():
                addresses = {}
                for i in a:
                    if i.family == 2:
                        addresses['ip4'] = i.address
                    if i.family == 10:
                        addresses['ip6'] = i.address
                    if i.family == 17:
                        addresses['mac'] = i.address
                interfaces[n] = addresses

        data = {'name': socket.getfqdn(),
                'net': interfaces}
        self.system = {'system': data}

    def gather(self):
        """
        Start Gathering Basic Stats about this host
        """
        self.gather_system()
        self.send_data()

    def del_user(self, user):
        """
        Delete User from the system
        :param user:
        :return:
        """
        username = user

        # Currently I'm not deleting home dirs
        # Just renaming it.  Eventually maybe a flag asking
        # which route to take.
        home_dir = '/home/' + username
        removed_home_dir = '/home/deleted-' + username
        sudoers_f = '/etc/sudoers.d/' + username
        # Remove SUDOERS
        if os.path.exists(sudoers_f):
            os.unlink(sudoers_f)
        # Kill open sessions
        subprocess.call(['pkill', '-9', '-u', username])
        subprocess.call(['mv', '-f', home_dir, removed_home_dir])
        subprocess.call(['userdel', username])

    def del_sudoers(self, user):
        """
        Delete users sudoers file
        :param user:
        :return:
        """
        username = user
        sudoers_f = '/etc/sudoers.d/' + username
        os.unlink(sudoers_f)

    def add_ssh_key(self, user):
        """
        Add SSH Key to newly created user
        :param user:
        :return:
        """
        # TODO: Make this work for Updating ssh keys as well, not just new users
        username = user['username']
        home_dir = '/home/' + username
        ssh_dir = home_dir + '/.ssh'
        if not os.path.exists(ssh_dir):
            subprocess.call(['mkdir', ssh_dir])
            subprocess.call(['chmod', '0700', ssh_dir])

        text = self.sshkeytext(user['ssh_pub_key'])
        authorized_keys = ssh_dir + '/authorized_keys'
        if not os.path.isfile(authorized_keys) or open(authorized_keys).read() != text:
            open(authorized_keys, "w").write(text)
            subprocess.call(['chown', '-R', username + ":" + username, home_dir])

    def sshkeytext(self, ssh_public_key):
        return "\n".join((
            "# Granted access via Yoked-Oxen",
            ssh_public_key, ""))

    def sudoerstext(self, username):
        return "\n".join((
            "# Granted Sudoers Access via Yoked-Oxen",
            "%s ALL=(ALL) NOPASSWD:ALL" % username, ""))

    def add_sudoers(self, user):
        """
        Add User to Sudoers if type == Admin
        :param user:
        :return:
        """
        username = user['username']
        sudoers_dir = '/etc/sudoers.d/'
        sudoers_f = sudoers_dir + username
        # TODO: Rework this to be more dynamic... Another API call possibly to pull down suders text
        if user['access'] == 'admin':
            if os.path.exists(sudoers_dir):
                text = self.sudoerstext(username)
                if not os.path.isfile(sudoers_f) or open(sudoers_f).read() != text:
                    open(sudoers_f, "w+").write(text)
                    subprocess.call(['chmod', '0440', sudoers_f])
                    subprocess.call(['chown', 'root:root', sudoers_f])

    def add_user(self, user):
        """
        Add User to the system
        :param user: dict for User Creation
        :return: True|False
        """
        username = user['username']
        name = user['name']
        email = user['email']
        shell = user['shell']
        access = user['access']
        ssh_pub_key = user['ssh_pub_key']

        # TODO: Config File option for changing base dir for $HOME
        home_dir = '/home/' + username
        gecos = 'yoked-' + email + ' ' + name

        if not os.path.isfile(shell):
            logging.info('Error: Requested Shell did not exist, switch to /bin/bash')
            shell = '/bin/bash'
        cmd = ['useradd', '-c' + gecos, '-m', '-s'+shell, '-d' + home_dir, username]
        logging.debug('Adding User [%s]' % cmd)
        try:
            subprocess.check_call(cmd)
        except subprocess.CalledProcessError:
            logging.info('ERROR: useradd Error... something something error code')
            pass
        except OSError:
            logging.info('ERROR: useradd command not found')
            pass
        current_users = self.gather_users()
        if username in current_users:
            self.add_ssh_key(user)
            self.add_sudoers(user)
            return True
        else:
            return False

    def process_users(self, users):
        """
        Process Incoming users from API
        """
        current_users = self.gather_users()
        active_users = []
        self.logger.debug('Processing Adding Users')
        for username, data in users.iteritems():
            active_users.append(username)
            if username not in current_users:
                self.logger.info("Adding User %s [%s] <%s>" % (data['name'], username, data['email']))
                if self.add_user(data):
                    self.logger.info("Successfully Added %s" % data['name'])
                else:
                    self.logger.info("Error: Was not able to create user: %s" % data['name'])
            elif username in current_users:
                self.logger.debug('Existing and Supplied user[%s]' % username)
                # Nothing needs to be done

        self.logger.debug('Processing Removing Users')
        for u in current_users:
            if u not in active_users:
                self.logger.info("Removing User %s" % u)
                self.del_user(u)

    def send_data(self):
        """
        Overly simple post currently, will add authentication/access keys
        in a future release
        """
        r = requests.post(self.endpoint, data=json.dumps(self.system))
        if r.status_code == 200 or r.status_code == 201:
            self.logger.debug('Sent Sysinfo successfully')
            data = r.json()
            self.process_users(data['users'])

    def run(self):
        self.logger.info('Oxen Starting up')
        while not self.is_dead:
            self.logger.debug('Starting gather()')
            self.gather()
            time.sleep(15)
        else:
            return False

def main():
    """
    Main Run
    :return:
    """
    # Setup Logging
    # TODO: logging as implemented, leaves much to be desired... work in progress
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        filename='/var/log/oxen.log',
                        level=logging.INFO)

    cattle = Oxen()
    try:
        cattle.run()
    except (KeyboardInterrupt, SystemExit):
        cattle.is_dead = True
        sys.exit(0)


if __name__ == '__main__':
    main()
