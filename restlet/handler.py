import re
import sys
import types
import logging
from sqlalchemy import Column
from sqlalchemy.orm.query import Query
from tornado.web import RequestHandler, HTTPError
from tornado import escape
from tornado import httputil
from tornado.log import access_log, app_log, gen_log
#from tornado.escape import utf8, _unicode
#from tornado.util import bytes_type, unicode_type
from . import exceptions
from .serializers import serialize
try:
    import simplejson as json
except:
    import json
try:
    import yaml
except:
    yaml = None


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
        if hasattr(f, '__encodes__'):
            f.__encodes__.extends(fields)
        else:
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
        if hasattr(f, '__decodes__'):
            f.__decodes__.extends(fields)
        else:
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
        if hasattr(f, '__generates__'):
            f.__generates__.extends(fields)
        else:
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
        if hasattr(f, '__route__'):
            f.__route__.append((pattern, methods, kwargs))
        else:
            f.__route__ = [(pattern, methods, kwargs)]
        return f
    return wrap


def request_handler(view):
    def f(self, *args, **kwargs):
        self.logger.debug('Headers: %s', self.request.headers)
        result = view(self, *args, **kwargs)

        if isinstance(result, (dict, list, tuple, types.GeneratorType)):
            if isinstance(result, types.GeneratorType):
                result = list(result)
            if 'yaml' in self.request.query:
                self.set_header('Content-Type', 'application/x-yaml')
                result = yaml.dump(result)
            else:
                self.set_header('Content-Type', 'application/json')
                result = json.dumps(result)
            self.write(result)
        elif isinstance(result, (str, unicode, bytearray)):
            self.write(result)
        else:
            self.logger.info('Result type is: %s', type(result))
            raise exceptions.RestletError()

    return f


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
        if not pattern.startswith('/') and not pattern.startswith('^'):
            pattern = r'^/' + pattern
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


def revert_list_of_qs(qs):
    if not isinstance(qs, dict):
        return
    for k, v in qs.items():
        if isinstance(v, list) and len(v) == 1 and isinstance(v[0], (str, unicode)):
            qs[k] = v[0]


def make_pk_regex(pk_clmns):
    if isinstance(pk_clmns, Column):
        if pk_clmns.type.__class__.__name__ in ('INT', 'BIGINT', 'SMALLINT', 'INTEGER', 'Integer',
                                                'SmallInteger', 'BigInteger',):
            return pk_clmns.name, r'(?P<%s>[0-9]+)' % pk_clmns.name
        elif pk_clmns.type.__class__.__name__ in ('CHAR', 'VARCHAR', 'NCHAR', 'NVARCHAR', 'String', 'Unicode'):
            return pk_clmns.name, r'(?P<%s>[0-9A-Za-z_-]+)' % pk_clmns.name
        else:
            return None, None
    elif isinstance(pk_clmns, (list, tuple)):
        return make_pk_regex(pk_clmns[0])
    else:
        return None, None


class HandlerBase(type):
    """
    Metaclass for all models.
    """
    def __new__(cls, name, bases, attrs):
        class Meta:
            pass
        super_new = super(HandlerBase, cls).__new__
        attr_meta = attrs.pop('Meta', None)
        attr_meta = attr_meta or Meta()
        for k in ('table', 'pk_regex', 'allowed', 'denied', 'changable', 'readonly', 'invisible', 'order_by',
                  'encoders', 'encoders', 'decoders', 'generators', 'extensible', 'routes'):
            if not hasattr(attr_meta, k):
                setattr(attr_meta, k, None)
        if attr_meta.pk_regex is None and attr_meta.table:
            attr_meta.pk_regex = make_pk_regex(attr_meta.table.__table__.primary_key.columns.values())
            attr_meta.pk_spec = URLSpec(attr_meta.pk_regex[1], None) if attr_meta.pk_regex[1] else None
        attr_meta.allowed = attr_meta.allowed or ('GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS')
        attr_meta.encoders = attr_meta.encoders or {}
        attr_meta.decoders = attr_meta.decoders or {}
        attr_meta.generators = attr_meta.generators or {}
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
                attr_meta.routes.extend([URLSpec(x[0], v, x[1], x[2]) for x in v.__route__])
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
        self.logger = self.application.logger if hasattr(self.application, 'logger') \
            else logging.getLogger('tornado.restlet')
        self.logger.info('Request: %s', dir(self.request))
        ## Here we re-construct the request.query and request.arguments
        ## the request.query is not a string of url query any more, it's converted to a disctionary;
        ## and request.arguments will only take the request.body parsed values, not including values in query;
        ## This helps to seperate the query of database and update request.
        ## It's a waiste to re-construct query and arguments here again because the httpserver has already did it, but
        ## we'll think about it later.
        if self.request.method in ('POST', 'PUT', 'PATCH'):
            content_type = self.request.headers.get('Content-Type', '')
            self.request.arguments = {}
            try:
                if content_type.startswith('application/json'):
                    # JSON
                    self.request.arguments = json.loads(self.request.body)
                elif content_type.startswith('application/x-yaml'):
                    # YAML
                    self.request.arguments = yaml.load(self.request.body)
                else:
                    httputil.parse_body_arguments(content_type,
                                                  self.request.body,
                                                  self.request.arguments,
                                                  self.request.files)
                    revert_list_of_qs(self.request.arguments)
            except Exception, e:
                self.logger.warning('Decoding request body failed according to content type (%s): %s', content_type, e)
        if self.request.query:
            self.request.query = escape.parse_qs_bytes(self.request.query, keep_blank_values=True)
            revert_list_of_qs(self.request.query)

    def log(self, level, msg, *args, **kwargs):
        self.logger.log(level, msg, *args, **kwargs)

    @request_handler
    def get(self, *args, **kwargs):
        self.logger.info('[%s] GET> args(%s), kwargs(%s)', self.__class__.__name__, args, kwargs)
        self.logger.info('Request::headers> %s', self.request.headers)
        self.logger.info('Request::path> %s', self.request.path)
        self.logger.info('Request::uri> %s', self.request.uri)
        self.logger.info('Request::query> %s', self.request.query)
        self.logger.info('Request::arguments> %s', self.request.arguments)
        return self._read(pk=kwargs.get(self._meta.pk_regex[0], None))

    @request_handler
    def post(self, *args, **kwargs):
        self.logger.info('[%s] POST>', self.__class__.__name__)
        self.logger.info('Request::headers> %s', self.request.headers)
        self.logger.info('Request::path> %s', self.request.path)
        self.logger.info('Request::uri> %s', self.request.uri)
        self.logger.info('Request::query> %s', self.request.query)
        self.logger.info('Request::arguments> %s', self.request.arguments)
        self.write('%s :> %s' % (self._meta.table, 'POST'))

    @request_handler
    def put(self, *args, **kwargs):
        self.logger.info('[%s] PUT>', self.__class__.__name__)
        self.logger.info('Request::headers> %s', self.request.headers)
        self.logger.info('Request::path> %s', self.request.path)
        self.logger.info('Request::uri> %s', self.request.uri)
        self.logger.info('Request::query> %s', self.request.query)
        self.logger.info('Request::arguments> %s', self.request.arguments)
        self.write('%s :> %s' % (self._meta.table, 'PUT'))

    @request_handler
    def delete(self, *args, **kwargs):
        self.logger.info('[%s] DELETE>', self.__class__.__name__)
        self.logger.info('Request::headers> %s', self.request.headers)
        self.logger.info('Request::path> %s', self.request.path)
        self.logger.info('Request::uri> %s', self.request.uri)
        self.logger.info('Request::query> %s', self.request.query)
        self.logger.info('Request::arguments> %s', self.request.arguments)
        self.write('%s :> %s' % (self._meta.table, 'DELETE'))

    @request_handler
    def head(self, *args, **kwargs):
        self.logger.info('[%s] HEAD>', self.__class__.__name__)
        self.logger.info('Request::headers> %s', self.request.headers)
        self.logger.info('Request::path> %s', self.request.path)
        self.logger.info('Request::uri> %s', self.request.uri)
        self.logger.info('Request::query> %s', self.request.query)
        self.logger.info('Request::arguments> %s', self.request.arguments)
        self.write('%s :> %s' % (self._meta.table, 'HEAD'))

    @request_handler
    def options(self, *args, **kwargs):
        self.set_header('Allowed', ','.join(self._meta.allowed))
        return {'Allowed': self._meta.allowed,
                'Model': self._meta.table.__name__,
                'Fields': self._meta.table.__table__.c.keys()}

    @classmethod
    def route_to(cls, path=None):
        if not path:
            pattern = r'/(?P<relpath>.*)'
        else:
            pattern = path + r'(?P<relpath>.*)'
        return pattern, cls

    @property
    def db_session(self):
        """Return the db session(SQLAlchemy), will created a new session if it is neccesary.
            None will present if the application does not have the new_db_session method implemented.
        """
        if hasattr(self, '_db_session_'):
            return self._db_session_
        else:
            if hasattr(self.application, 'new_db_session') and hasattr(self.application.new_db_session, '__call__'):
                sess = self.application.new_db_session()
            else:
                sess = None
            setattr(self, '_db_session_', sess)
            return self._db_session_

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
        elif isinstance(e, exceptions.RestletError):
            self.send_error(e.error, exc_info=sys.exc_info())
        else:
            self.send_error(500, exc_info=sys.exc_info())

    def _execute(self, transforms, *args, **kwargs):
        """Executes this request with the given output transforms."""
        self._transforms = transforms
        try:
            if self.request.method not in self.SUPPORTED_METHODS:
                raise exceptions.MethodNotAllowed()
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
        def unquote(s):
        # None-safe wrapper around url_unescape to handle
        # unmatched optional groups correctly
            if s is None:
                return s
            return escape.url_unescape(s, encoding=None,
                                       plus=False)
        if not self._finished:
            if self._meta.routes and self.path_kwargs.get('relpath', None):
                method = None
                for spec in self._meta.routes:
                    match = spec.regex.match(self.path_kwargs.get('relpath'))
                    if match:
                        if spec.methods and self.request.method not in spec.methods:
                            raise exceptions.MethodNotAllowed()
                        method = spec.request_handler
                        if spec.regex.groups:
                            if spec.regex.groupindex:
                                self.path_kwargs = dict(
                                    (str(k), unquote(v))
                                    for (k, v) in match.groupdict().items())
                            else:
                                self.path_args = [unquote(s) for s in match.groups()]
                        break
                ### else:
                if not method:
                    match = self._meta.pk_spec.regex.match(self.path_kwargs.get('relpath')) if self._meta.pk_spec \
                        else None
                    if match:
                        if spec.regex.groups:
                            if spec.regex.groupindex:
                                self.path_kwargs = dict(
                                    (str(k), unquote(v))
                                    for (k, v) in match.groupdict().items())
                            else:
                                self.path_args = [unquote(s) for s in match.groups()]
                        method = getattr(self, self.request.method.lower())
                        self._when_complete(method(*self.path_args, **self.path_kwargs),
                                            self._execute_finish)
                    else:
                        raise exceptions.NotFound()
                else:
                    self._when_complete(method(self, *self.path_args, **self.path_kwargs),
                                        self._execute_finish)
            else:
                method = getattr(self, self.request.method.lower())
                self._when_complete(method(*self.path_args, **self.path_kwargs),
                                    self._execute_finish)

    def _serialize(self, inst, include_fields=None, exclude_fields=None, extend_fields=None, order_by=None, limit=None):
        """_serialize generate a dictionary from a queryset instance `inst` according to the meta controled by handler
        and the following arguments:
        `include_fields`: a list of field names want to included in output;
        `exclude_fields`: a list of field names will not included in output;
        `extend_fields`: a list of foreignkey field names and m2m or related attributes with other relationships;
        `order_by`: a list of field names for ordering the output;
        `limit`: an integer to limit the number of records to output, 50 by default;
        Return dictionary will like:
        {
            'ref': '$(HTTP_REQUEST_URI)',
            '__total': $(NUM_OF_MACHED_RECORDS),
            '__count': $(NUM_OF_RETURNED_RECORDS),
            '__limit': $(LIMIT_NUM),
            '__begin': $(OFFSET),
            '__model': '$(NAME_OF_MODEL)',
            'objects': [$(LIST_OF_RECORDS)], ## For multiple records mode
            'object': {$(RECORD)}, ## For one record mode
        }
        """
        result = {
            'ref': self.request.uri,
            '__model': self._meta.table.__name__,
        }

        meta = self._meta
        include_fields = []
        exclude_fields = []
        extend_fields = []
        order_by = []
        limit = 50 if limit is None else limit
        if isinstance(inst, Query):
            result.update({
                '__total': inst.count(),
                '__count': inst.count(),
                '__limit': limit or 50,
                '__begin': 0,
            })
            result['objects'] = list(inst.values(*[getattr(self._meta.table, x) \
                                              for x in self._meta.table.__table__.c.keys()]))
        else:
            result['object'] = dict([(k, getattr(inst, k)) for k in self._meta.table.__table__.c.keys()])
        return result

    def _read(self, pk=None, query=None, include_fields=None, exclude_fields=None,
              extend_fields=None, order_by=None, limit=None):
        if pk:
            try:
                inst = self.db_session.query(self._meta.table).filter_by(**{self._meta.pk_regex[0]: pk}).one()
            except Exception, e:
                #self.logger.exception(e)
                raise exceptions.NotFound()
        else:
            inst = self.db_session.query(self._meta.table)
        self.logger.debug('Inst: %s', type(inst))
        return self._serialize(inst)

    def _create(self, arguments):
        pass

    def _update(self, inst, arguments, query=None):
        pass

    def _delete(self, query=None):
        pass
