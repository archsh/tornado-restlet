# -*- coding: utf-8 -*-
from restlet.application import Application
from restlet.handler import RestletHandler, encoder, decoder, route
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Sequence
import logging

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    name = Column(String(50))
    fullname = Column(String(50))
    password = Column(String(40))
    key = Column(String(32))


class UserHandler(RestletHandler):
    """UserHandler to process User table."""

    class Meta:
        testing = True
        table = User
        allowed = ('GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS')
        denied = None  # Can be a tuple of HTTP METHODs
        changable = ('fullname', 'password')  # None will make all fields changable
        readonly = ('name', 'id')  # None means no field is read only
        invisible = ('password', )  # None means no fields is invisible
        encoders = None  # {'password': lambda x, obj: hashlib.new('md5', x).hexdigest()}
                             # or use decorator @encoder(*fields)
        decoders = None  # User a dict or decorator @decoder(*fields)
        generators = None  # User a dict or decorator @generator(*fields)
        extensible = None  # None means no fields is extensible or a tuple with fields.

    @encoder('password')
    def password_encoder(self, passwd, inst=None):
        import hashlib
        return hashlib.new('md5', passwd).hexdigest()

    @route(r'/(?P<uid>[0-9]+)/login', 'POST', 'PUT')
    @route(r'/login', 'POST', 'PUT')
    def do_login(self, *args, **kwargs):
        self.logger.info("OK, It's done!: %s, %s, %s", args, kwargs, self.request.arguments)
        self.write("OK, It's done!: %s, %s" % (args, kwargs))


if __name__ == "__main__":
    import tornado.ioloop
    logging.basicConfig(level=logging.DEBUG)
    application = Application([UserHandler.route_to('/users'), ],
                              dburi='sqlite:///:memory:', loglevel='DEBUG')
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()