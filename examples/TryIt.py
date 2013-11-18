# -*- coding: utf-8 -*-
from restlet.models import Model, request_action
from restlet.application import Application
from restlet.handler import RestletHandler


class User(Model):

    @request_action(methods=['POST', 'PUT'], withpk=True)
    def login(self, *args, **kwargs):
        pass

    class Meta:
        db_table = 'users'
        write_columns = None
        read_columns = None


class Group(Model):
    pass


class Permission(Model):
    pass


class MainHandler(RestletHandler):
    user = User
    group = Group
    permission = Permission

    def get(self, *args, **kwargs):
        self.write("Hello, world")


application = Application([
    (r"/", MainHandler),
])


if __name__ == "__main__":
    import tornado.ioloop
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()