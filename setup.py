# -*- coding:utf-8 -*-
from distutils.core import setup
from restlet import __version__

setup(name='Tornado-RESTlet',
      version=__version__,
      description='RESTlet, a RESTful extention on Tornado.',
      long_description=open("README.md").read(),
      author='Mingcai SHEN',
      author_email='archsh@gmail.com',
      packages=['restlet'],
      package_dir={'restlet': 'restlet'},
      package_data={'restlet': ['stuff']},
      license="Public domain",
      platforms=["any"],
      install_requires=[
          'tornado',
          'SQLAlchemy'
      ],
      url='https://github.com/archsh/tornado-restlet')
