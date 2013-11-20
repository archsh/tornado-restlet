import re
import sys
from tornado.web import RequestHandler, HTTPError
from tornado import escape
from tornado import httputil
from tornado.log import access_log, app_log, gen_log
#from tornado.escape import utf8, _unicode
#from tornado.util import bytes_type, unicode_type


def encoder(*fields):
    """Decorator for Handler function which will register the decorated function as the encoder of field(s).
    eg:
    class UserHandler(RestletHandler):
        ...
        @encoder('password'):
        def password_hashed(self, passwd, record=None):
            import hashlib
            return hashlib.new('md5',passwd).hexdigest()

    """
    assert fields

    def wrap(f):
        f.__encodes__ = fields
        return f
    return wrap


def decoder(*fields):
    """Decorator for Handler function which will register the decorated function as the decoder of field(s).
    eg:
    class UserHandler(RestletHandler):
        ...
        @decoder('password'):
        def password_hashed(self, passwd, record=None):
            import hashlib
            return hashlib.new('md5',passwd).hexdigest()
    """
    assert fields

    def wrap(f):
        f.__decodes__ = fields
        return f
    return wrap


def generator(*fields):
    """Decorator for Handler function which will register the decorated function as the generator of field(s).
    eg:
    class UserHandler(RestletHandler):
        ...
        @generator('num'):
        def generate_num(self, num, record=None):
            import random
            return random.randint()
    """
    assert fields

    def wrap(f):
        f.__generates__ = fields
        return f
    return wrap


def route(pattern, *methods, **kwargs):
    """Decorator for route a specific path pattern to a method of RestletHandler instance.
    methods can be giving if is only for specified HTTP method(s).
    eg:
    class UserHandler(RestletHandler):
        ...
        @route(r'/login', 'POST','PUT'):
        def do_login(self,*args, **kwrags):
            ...
            ...

    """
    assert pattern

    def wrap(f):
        f.__route__ = (pattern, methods, kwargs)
        return f
    return wrap


class URLSpec(object):
    """Specifies mappings between URLs and handlers."""
    def __init__(self, pattern, request_handler, methods=None, kwargs=None):
        """Parameters:

        * ``pattern``: Regular expression to be matched.  Any groups
          in the regex will be passed in to the handler's get/post/etc
          methods as arguments.

        * ``request_handler``: A method of `RestletHandler` subclass to be invoked.

        * ``methods``: A tuple/list of methods which supported for this handler.

        * ``kwargs`` (optional): A dictionary of additional arguments
          to be passed to the handler's constructor.

        * ``name`` (optional): A name for this handler.  Used by
          `Application.reverse_url`.
        """
        if not pattern.endswith('$'):
            pattern += '$'
        self.regex = re.compile(pattern)
        assert len(self.regex.groupindex) in (0, self.regex.groups), \
            ("groups in url regexes must either be all named or all "
             "positional: %r" % self.regex.pattern)
        self.request_handler = request_handler
        self.kwargs = kwargs or {}
        self.methods = methods
        self._path, self._group_count = self._find_groups()

    def __repr__(self):
        return '%s(%r, %s, kwargs=%r, methods=%r)' % \
            (self.__class__.__name__, self.regex.pattern,
             self.request_handler, self.kwargs, self.methods)

    def _find_groups(self):
        """Returns a tuple (reverse string, group count) for a url.

        For example: Given the url pattern /([0-9]{4})/([a-z-]+)/, this method
        would return ('/%s/%s/', 2).
        """
        pattern = self.regex.pattern
        if pattern.startswith('^'):
            pattern = pattern[1:]
        if pattern.endswith('$'):
            pattern = pattern[:-1]

        if self.regex.groups != pattern.count('('):
            # The pattern is too complicated for our simplistic matching,
            # so we can't support reversing it.
            return None, None

        pieces = []
        for fragment in pattern.split('('):
            if ')' in fragment:
                paren_loc = fragment.index(')')
                if paren_loc >= 0:
                    pieces.append('%s' + fragment[paren_loc + 1:])
            else:
                pieces.append(fragment)

        return ''.join(pieces), self.regex.groups


class HandlerBase(type):
    """
    Metaclass for all models.
    """
    def __new__(cls, name, bases, attrs):
        class Meta:
            pass
        super_new = super(HandlerBase, cls).__new__
        attr_meta = attrs.pop('Meta', None)
        if attr_meta is None:
            attr_meta = Meta()
        for k in ('table', 'allowed', 'denied', 'changable', 'readonly', 'invisible', 'order_by', 'encoders',
                  'encoders', 'decoders', 'generators', 'extensible', 'routes'):
            if not hasattr(attr_meta, k):
                setattr(attr_meta, k, None)
        if attr_meta.allowed is None:
            attr_meta.allowed = ('GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS')
        if attr_meta.encoders is None:
            attr_meta.encoders = {}
        if attr_meta.decoders is None:
            attr_meta.decoders = {}
        if attr_meta.generators is None:
            attr_meta.generators = {}
        attr_meta.routes = list()
        for k, v in attrs.items():  # collecting decorated functions.
            if not hasattr(v, '__call__'):
                continue
            if hasattr(v, '__encodes__'):
                for f in v.__encodes__:
                    attr_meta.encoders[f] = v
            elif hasattr(v, '__decodes__'):
                for f in v.__decodes__:
                    attr_meta.encoders[f] = v
            elif hasattr(v, '__generates__'):
                for f in v.__generates__:
                    attr_meta.generators[f] = v
            elif hasattr(v, '__route__'):
                attr_meta.routes.append(
                    URLSpec(v.__route__[0], v, v.__route__[1], v.__route__[2])
                )
        new_class = super_new(cls, name, bases, attrs)
        new_class.add_to_class('_meta', attr_meta)
        if attr_meta.table is not None:
            setattr(attr_meta.table, '__handler__', new_class)
        print name, ':', attr_meta.__dict__
        return new_class

    def add_to_class(cls, name, value):
        if hasattr(value, 'contribute_to_class'):
            value.contribute_to_class(cls, name)
        else:
            setattr(cls, name, value)


class RestletHandler(RequestHandler):
    """RestletHandler is based on tornado.web.RequestHandler
        For example:
        class UserHandler(RestletHandler):
            'UserHandler to process User table.'

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
        def password_encoder(self, passwd, record=None):
            import hashlib
            return hashlib.new('md5', passwd).hexdigest()
    """
    __metaclass__ = HandlerBase

    def __init__(self, *args, **kwargs):
        super(RestletHandler, self).__init__(*args, **kwargs)

    def get(self, *args, **kwargs):
        self.write('%s :> %s' % (self._meta.table, 'GET'))

    def post(self, *args, **kwargs):
        self.write('%s :> %s' % (self._meta.table, 'POST'))

    def put(self, *args, **kwargs):
        self.write('%s :> %s' % (self._meta.table, 'PUT'))

    def delete(self, *args, **kwargs):
        self.write('%s :> %s' % (self._meta.table, 'DELETE'))

    def head(self, *args, **kwargs):
        self.write('%s :> %s' % (self._meta.table, 'HEAD'))

    def options(self, *args, **kwargs):
        self.write('%s :> %s' % (self._meta.table, 'OPTIONS'))

    @classmethod
    def route_to(cls, path=None):
        if not path:
            pattern = r'/(?P<relpath>.*)'
        else:
            pattern = path + r'(?P<relpath>.*)'
        return pattern, cls

    def _handle_request_exception(self, e):
        self.log_exception(*sys.exc_info())
        if self._finished:
            # Extra errors after the request has been finished should
            # be logged, but there is no reason to continue to try and
            # send a response.
            return
        if isinstance(e, HTTPError):
            if e.status_code not in httputil.responses and not e.reason:
                gen_log.error("Bad HTTP status code: %d", e.status_code)
                self.send_error(500, exc_info=sys.exc_info())
            else:
                self.send_error(e.status_code, exc_info=sys.exc_info())
        else:
            self.send_error(500, exc_info=sys.exc_info())

    def _execute(self, transforms, *args, **kwargs):
        """Executes this request with the given output transforms."""
        self._transforms = transforms
        try:
            if self.request.method not in self.SUPPORTED_METHODS:
                raise HTTPError(405)
            self.path_args = [self.decode_argument(arg) for arg in args]
            self.path_kwargs = dict((k, self.decode_argument(v, name=k))
                                    for (k, v) in kwargs.items())
            # If XSRF cookies are turned on, reject form submissions without
            # the proper cookie
            if self.request.method not in ("GET", "HEAD", "OPTIONS") and \
                    self.application.settings.get("xsrf_cookies"):
                self.check_xsrf_cookie()
            self._when_complete(self.prepare(), self._execute_method)
        except Exception as e:
            self._handle_request_exception(e)

    def _execute_method(self):
        if not self._finished:
            if self._meta.routes and self.path_kwargs.get('relpath', None):
                method = None
                for spec in self._meta.routes:
                    match = spec.regex.match(self.path_kwargs.get('relpath'))
                    if match:
                        if spec.methods and self.request.method not in spec.methods:
                            raise HTTPError(405)
                        method = spec.request_handler
                        if spec.regex.groups:
                            # None-safe wrapper around url_unescape to handle
                            # unmatched optional groups correctly
                            def unquote(s):
                                if s is None:
                                    return s
                                return escape.url_unescape(s, encoding=None,
                                                           plus=False)
                            if spec.regex.groupindex:
                                self.path_kwargs = dict(
                                    (str(k), unquote(v))
                                    for (k, v) in match.groupdict().items())
                            else:
                                self.path_args = [unquote(s) for s in match.groups()]
                        break
                ### else:
                if not method:
                    raise HTTPError(404)
                self._when_complete(method(self, *self.path_args, **self.path_kwargs),
                                    self._execute_finish)
            else:
                method = getattr(self, self.request.method.lower())
                self._when_complete(method(*self.path_args, **self.path_kwargs),
                                    self._execute_finish)