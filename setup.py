# -*- coding:utf-8 -*-
from distutils.core import setup
from torexpress import __version__, __author__

setup(name='tornado-torexpress',
      version=__version__,
      description='Restlet, a RESTful extention on Tornado. %s ' % __author__,
      long_description=open("README.md").read(),
      author='Mingcai SHEN',
      author_email='archsh@gmail.com',
      packages=['torexpress'],
      package_dir={'torexpress': 'torexpress'},
      package_data={'torexpress': ['stuff']},
      license="Public domain",
      platforms=["any"],
      install_requires=[
          'tornado>=3.1.1',
          'SQLAlchemy>=0.8.2',
          'simplejson>=2.3.2',
          'PyYAML>=3.10',
      ],
      url='https://github.com/archsh/tornado-torexpress')
