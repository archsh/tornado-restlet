# -*- coding: utf-8 -*-
"""
predicates for access control.
"""
import logging
logger = logging.getLogger('tornado.torexpress')


class BaseAuthenticator(object):
    """
    BaseAuthenticator: the very basic authenticator for ExpressHandler which can be called inside ExpressHandler.
    """
    def __init__(self, **kwargs):
        self._init_kwargs_ = kwargs

    def __call__(self, handler, *args, **kwargs):
        #logger.debug('BaseAuthenticator> handler=%s, request=%s', handler, request)
        #logger.debug('BaseAuthenticator> args=%s, kwargs=%s', args, kwargs)
        #logger.debug('BaseAuthenticator> init_kwargs=%s', self._init_kwargs_)
        self.do_auth(handler, *args, **kwargs)

    def do_auth(self, handler, *args, **kwargs):
        """
        Do the authentication here. And this is the only one method the subclasses should be overide.
        Params:
        @param handler: an instance of ExpressHandler (or subclass).
        @param args: args from caller function.
        @param kwargs: kwargs from caller function.
        Also, self._init_kwargs_ is available for the kwargs when initialize the authenticator.
        """
        logger.debug('%s >>> bite me!', self.__class__.__name__)


def require_auth(*authenticators):
    """
    Decorator to indicates if an handler function needs to check with one or more authenticators.
    """
    def deco_wrapper(f):
        def wrapper(self, *args, **kwargs):
            for auth_f in authenticators:
                auth_f(self, *args, **kwargs)
            return f(self, *args, **kwargs)
        return wrapper
    return deco_wrapper
