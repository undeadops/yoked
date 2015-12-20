
import re
from setuptools import setup


version = re.search(
    r'__version__\s*=\s*"(.*)"',
    open('yokedclient/cli.py').read()
    ).group(1)


with open("README.rst", "rb") as f:
    long_descr = f.read().decode("utf-8")


setup(name='yoked-client',
      version=version,
      description='SSH Key Managment Configuration Tool',
      long_description=long_descr,
      url='https://github.com/metarx/yoked',
      author='Mitch Anderson',
      author_email='mitch@metauser.net',
      license='MIT',
      packages=['yokedclient'],
      zip_safe=False,
      install_requires=[
          'requests==2.8.1',
      ],
      entry_points = {
          'console_scripts': ['yokedctl = yokedclient.cli:main'],
          }
      )
