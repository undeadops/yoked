#!/usr/bin/env python

__version__ = "0.1"

import sys
from .commands import Commands
import argparse
import pprint

def main():
    """
    Main Interface into CLI
    """
    parser = argparse.ArgumentParser()

    parser.add_argument('-u', '--list-users', help="Display list of users", action='store_true')
    parser.add_argument('-g', '--list-groups', help="Display list of groups", action='store_true')
    parser.add_argument('-s', '--list-systems', help="Display Systems managed by Yoked", action='store_true')
    parser.add_argument('-r', '--list-roles', help="Display Roles associated to systems", action='store_true')
    results = parser.parse_args()

    # Run a test command
    command = Commands()
    if results.list_users:
        command.list_users()
    elif results.list_groups:
        command.list_groups()
    elif results.list_systems:
        command.list_systems()
    elif results.list_roles:
        command.list_roles()
