from tornado.web import Application
import logging
from .cache import Dummy
_logger = logging.getLogger('tornado.torexpress')


class ExpressApplication(Application):
    """RestletApplication is based on tornado.web.Application, manages a collection of RestletHandlers to make up a
    RESTful web application.
    """

    def __init__(self, handlers=None, default_host="", transforms=None,
                 wsgi=False, **settings):
        super(ExpressApplication, self).__init__(handlers=handlers, default_host=default_host,
                                                 transforms=transforms, wsgi=wsgi, **settings)
        if settings.get('dburi'):
            from sqlalchemy.orm import sessionmaker
            from sqlalchemy import create_engine
            self.db_engine = create_engine(settings.get('dburi'), echo=settings.get('dblogging', False))
            self.session_maker = sessionmaker(bind=self.db_engine)
        else:
            self.db_engine = None
            self.session_maker = None
        if settings.get('cache'):
            self.cache = Dummy()
        else:
            self.cache = Dummy()

    def new_db_session(self, *args, **kwargs):
        """new_db_session: create a new db session with the default sessionmaker from application.
        """
        assert self.session_maker
        return self.session_maker(*args, **kwargs)