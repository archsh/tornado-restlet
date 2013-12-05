# -*- coding: utf-8 -*-
import logging
import datetime
from restlet.application import RestletApplication
from restlet.handler import RestletHandler, encoder, decoder, route
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Sequence, MetaData, ForeignKey, Text, SmallInteger, Boolean, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.query import Query


Base = declarative_base()


class Group(Base):
    __tablename__ = 'groups'
    id = Column(Integer, Sequence('group_id_seq'), primary_key=True)
    name = Column(String(50))
    users = relationship('User', backref="group")


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    fullname = Column(String(50), nullable=True)
    password = Column(String(40), nullable=True)
    key = Column(String(32), nullable=True, doc='Another key')
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=True)


class UserHandler(RestletHandler):
    """UserHandler to process User table."""
    def __init__(self, *args, **kwargs):
        super(UserHandler, self).__init__(*args, **kwargs)
        self.t1 = datetime.datetime.now()
        self.t2 = None

    def on_finish(self):
        self.t2 = datetime.datetime.now()
        self.logger.info('Total Spent: %s', self.t2 - self.t1)

    class Meta:
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
    application = RestletApplication([UserHandler.route_to('/users'), ],
                                     dburi='sqlite:///:memory:', loglevel='DEBUG', debug=True)
    Base.metadata.create_all(application.db_engine)
    session = application.new_db_session()
    group = Group(name='Group 1')
    session.add(group)
    session.add(User(name='u1', fullname='User 1', password='password 1', key='key 1', group=group))
    session.add(User(name='u2', fullname='User 2', password='password 2', key='key 2', group=group))
    session.add(User(name='u3', fullname='User 3', password='password 3', key='key 3', group=group))
    session.add(User(name='u4', fullname='User 4', password='password 4', key='key 4', group=group))
    session.commit()

    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()