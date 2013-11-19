from tornado.web import RequestHandler
#from functools import update_wrapper, wraps


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
        attr_meta.table = attrs.pop('__table__', None)
        attr_meta.allowed = attrs.pop('__allowed__', None)
        if attr_meta.allowed is None:
            attr_meta.allowed = ('GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS')
        attr_meta.denied = attrs.pop('__denied__', None)
        attr_meta.changable = attrs.pop('__changable__', None)
        attr_meta.readonly = attrs.pop('__readonly__', None)
        attr_meta.invisible = attrs.pop('__invisible__', None)
        attr_meta.order_by = attrs.pop('__order_by__', None)
        attr_meta.encoders = attrs.pop('__encoders__', None)
        if attr_meta.encoders is None:
            attr_meta.encoders = {}
        attr_meta.decoders = attrs.pop('__decoders__', None)
        if attr_meta.decoders is None:
            attr_meta.decoders = {}
        attr_meta.extensible = attrs.pop('__extensible__', None)
        for k, v in attrs.items():
            if hasattr(v, '__call__'):
                if hasattr(v, '__encodes__'):
                    for f in v.__encodes__:
                        attr_meta.encoders[f] = v
                elif hasattr(v, '__decodes__'):
                    for f in v.__decodes__:
                        attr_meta.encoders[f] = v
        new_class = super_new(cls, name, bases, attrs)
        new_class.add_to_class('_meta', attr_meta)
        #print name, ':', dir(new_class)
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
    def url_regx(cls, prefix=None):
        pass