from setuptools import setup

setup(name='yokedclient',
      version='0.1',
      description='SSH Key Managment Configuration Tool',
      url='https://github.com/metarx/yoked',
      author='Mitch Anderson',
      author_email='mitch@metauser.net',
      license='MIT',
      packages=['yokedclient'],
      zip_safe=False,
      entry_points = {
          'console_scripts': ['yokedctl=yokedclient.cli:main'],
          }
      )
