# -*- coding: utf-8 -*-
from restlet.models import Model, request_action
from restlet.application import Application
from restlet.handler import RestletHandler
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Sequence

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    name = Column(String(50))
    fullname = Column(String(50))
    password = Column(String(12))


class Group(Model):
    pass


class Permission(Model):
    pass


class MainHandler(RestletHandler):
    user = User
    group = Group
    permission = Permission

    def get(self, *args, **kwargs):
        user = User()
        user.mro()
        self.write("Hello, world")


application = Application([
    (r"/", MainHandler),
])


if __name__ == "__main__":
    import tornado.ioloop
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()