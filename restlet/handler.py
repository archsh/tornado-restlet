from tornado.web import RequestHandler
from . import models


def Options(meta, **kwargs):
    class Meta:
        pass
    if not meta:
        meta = Meta()
    meta.models = list()
    for k, v in kwargs.items():
        if not isinstance(v, models.Model):
            continue
        meta.models.append((k, v))
    return meta


class HandlerBase(type):
    """
    Metaclass for all models.
    """
    def __new__(cls, name, bases, attrs):
        super_new = super(HandlerBase, cls).__new__
        module = attrs.pop('__module__')
        new_class = super_new(cls, name, bases, {'__module__': module})

        attr_meta = attrs.pop('Meta', None)
        if not attr_meta:
            meta = getattr(new_class, 'Meta', None)
        else:
            meta = attr_meta
        #for k, v in attrs.items():
        #    if isinstance(v, models.Model):
        #        v.contrib_to_class(new_class)
        new_class.add_to_class('_meta', Options(meta, **attrs))
        return new_class

    def add_to_class(cls, name, value):
        if hasattr(value, 'contribute_to_class'):
            value.contribute_to_class(cls, name)
        else:
            setattr(cls, name, value)


class RestletHandler(RequestHandler):
    """RestletHandler is based on tornado.web.RequestHandler
    """
    __metaclass__ = HandlerBase

    def __init__(self):
        pass

    def _get(self, *args, **kwargs):
        pass

    def _post(self, *args, **kwargs):
        pass

    def _put(self, *args, **kwargs):
        pass

    def _delete(self, *args, **kwargs):
        pass

    def _head(self, *args, **kwargs):
        pass

    def _options(self, *args, **kwargs):
        pass

    @classmethod
    def url_regx(cls, prefix=None):
        pass