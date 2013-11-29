RESTlet
======================

**A RESTful extension for tornado.**

*Note: It's under very basic development now, every thing can be changed in the next commit.*

Features
----------------------
1. XXX
1. XXXX
1. XXXX
1. XXXX
1. XXXX

Quick Start
----------------------

	# -*- coding: utf-8 -*-
	from restlet.application import RestletApplication
	from restlet.handler import RestletHandler
	from sqlalchemy.ext.declarative import declarative_base
	from sqlalchemy import Column, Integer, String, Sequence, MetaData, ForeignKey
	from sqlalchemy.orm import relationship, backref
	from sqlalchemy.orm.query import Query

	Base = declarative_base()

	class User(Base):
	    __tablename__ = 'users'
	    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
	    name = Column(String(50), nullable=False, unique=True)
	    fullname = Column(String(50), nullable=True)
	    password = Column(String(40), nullable=True)
	
	class UserHandler(RestletHandler):
	    """UserHandler to process User table."""
	
	    class Meta:
	        table = User
	
	    @encoder('password')
	    def password_encoder(self, passwd, inst=None):
	        import hashlib
	        return hashlib.new('md5', passwd).hexdigest()

	if __name__ == "__main__":
	    import tornado.ioloop
	    application = RestletApplication([UserHandler.route_to('/users'), ],
	                                     dburi='sqlite:///:memory:', loglevel='DEBUG', debug=True)
	    Base.metadata.create_all(application.db_engine)
	    application.listen(8888)
	    tornado.ioloop.IOLoop.instance().start()


Requirements
----------------------

- Tornaro >= 3.1.1
- SQLAlchemy >= 0.8
- Simplejson
- PyYAML
