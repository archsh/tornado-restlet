# -*- coding: utf-8 -*-
from restlet.application import Application
from restlet.handler import RestletHandler, encoder, decoder
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Sequence

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    name = Column(String(50))
    fullname = Column(String(50))
    password = Column(String(12))


class UserHandler(RestletHandler):
    """UserHandler to process User table."""
    __table__ = User
    __allowed__ = ('GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS')
    __denied__ = None  # Can be a tuple of HTTP METHODs
    __changable__ = ('fullname', 'password')  # None will make all fields changable
    __readonly__ = ('name', 'id')  # None means no field is read only
    __invisible__ = ('password', )  # None means no fields is invisible
    __encoders__ = None  # {'password': lambda x, obj: hashlib.new('md5', x).hexdigest()}
                         # or use decorator @encoder(*fields)
    __decoders__ = None  # User a dict or decorator @decoder(*fields)
    __autovalues__ = None  # User a dict or decorator @autovalue(*fields)
    __extensible__ = None  # None means no fields is extensible or a tuple with fields.

    @encoder('password')
    def password_encoder(self, passwd, record=None):
        import hashlib
        return hashlib.new('md5', passwd).hexdigest()


if __name__ == "__main__":
    import tornado.ioloop
    application = Application([(r"/users", UserHandler)],
                              dburi='sqlite:///:memory:')
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()