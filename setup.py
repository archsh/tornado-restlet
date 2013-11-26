# -*- coding:utf-8 -*-
from distutils.core import setup
from restlet import __version__

setup(name='tornado-restlet',
      version=__version__,
      description='Restlet, a RESTful extention on Tornado.',
      long_description=open("README.md").read(),
      author='Mingcai SHEN',
      author_email='archsh@gmail.com',
      packages=['restlet'],
      package_dir={'restlet': 'restlet'},
      package_data={'restlet': ['stuff']},
      license="Public domain",
      platforms=["any"],
      install_requires=[
          'tornado>=3.1.1',
          'SQLAlchemy>=0.8.2',
          'simplejson>=2.3.2',
          'PyYAML>=3.10',
      ],
      url='https://github.com/archsh/tornado-restlet')
