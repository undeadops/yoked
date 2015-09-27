yoked command line client
========================

Yoked provides ssh public key management for cloud environments.  Its client
polls the yoked server api for a list of approved users and their public ssh keys
and installs those onto itself.  Adjust client polling interval for rapid add/remove
of user accounts and ssh keys.  Only meant to manage end-user access not system
or application accounts, use configuration management for that.  Configuring
sshd to only accept ssh keys highly recommended.

Usage
-----

Client connects to API server to manage SSH keys and user accounts.  Group users
and systems, and associating as needed for defined access.


Installation sets up yokedctl command
**************************************

Installation right from the source tree::

    $ python setup.py install

Or via pip::

    $ pip install yoked-client


Credits
**************************************

Many thanks to Jan-Philip Gehrcke and https://github.com/jgehrcke/python-cmdline-bootstrap
for getting me started on this client.
