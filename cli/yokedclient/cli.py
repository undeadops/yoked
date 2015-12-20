#!/usr/bin/env python

__version__ = "0.1"

import sys
import argparse
import pprint
from . import commands

def main():
    """
    Main Interface into CLI
    """
    parser = argparse.ArgumentParser(description="Yoke Command Line Client - Manage Application from the cli")

    parser.add_argument('-u', '--list-users', help="Display list of users", action='store_true')
    subparsers = parser.add_subparsers(
        title='subcommands', description='valid subcommands',
        help='additional help')
    parser.add_argument('-C', '--config', help="Create Config File", action='store_true')
    parser_adduser = subparsers.add_parser('adduser')
    parser_adduser.required = False
    parser_adduser.set_defaults(which='adduser')
    parser_adduser.add_argument(
        '--username', required=True, help='Username of User')
    parser_adduser.add_argument(
        '--name', required=True, help='First and Last Name of User')
    parser_adduser.add_argument(
        '--email', required=True, help='Email address for User')
    parser_adduser.add_argument(
        '--shell', required=False, help='Users preferred shell', default='bash')
    parser_adduser.add_argument(
        '--admin', required=False, help='Make user and admin user', action='store_true', default=False)
    parser_adduser.add_argument(
        '--sshpubkey', required=True, help='SSH public key for User')
    parser_show = subparsers.add_parser('show')
    parser_show.required = False
    parser_show.set_defaults(which='show')
    parser_show.add_argument('what', choices=['groups','roles','systems','users'])
    parser_config = subparsers.add_parser('config')
    parser_config.required = False
    parser_config.set_defaults(which='config')
    results = parser.parse_args()

    # Run a test command
    command = commands.Commands()
    if results.which == 'adduser':
        command.add_user(results)
    elif results.which == 'show':
        if results.what == 'groups':
            command.list_groups()
        elif results.what == 'systems':
            command.list_systems()
        elif results.what == 'roles':
            command.list_roles()
        elif results.what == 'users':
            command.list_users()
    elif results.which == 'config':
        command.config_create()
