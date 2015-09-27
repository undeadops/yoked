#!/usr/bin/env python

__version__ = "0.1"

import sys
from .commands import Commands

def main():
    """
    Main Interface into CLI
    """
    # Run a test command
    command = Commands()
    command.run()
