# -*- coding: utf-8 -*-


def request_action(*args, **kwargs):
    pass


def Options(meta, **kwargs):

    class Meta:
        pass

    if not meta:
        meta = Meta()
    meta.fields = list()
    for k, v in kwargs.items():
        #if not isinstance(v, fields.Field):
        #    continue
        #v.name = k
        #if hasattr(v, 'primary_key') and v.primary_key and not isinstance(v, fields.OneToOneField):
        #    if hasattr(meta, 'pk') and meta.pk:
        #        raise exceptions.TypeError('Primary key already defined: "%s".' % meta.pk.name)
        #    meta.pk = v
        meta.fields.append(v)
    #if not hasattr(meta, 'pk') or not meta.pk:
    #    raise exceptions.TypeError('Primary key required.')

    return meta


###----
class ModelBase(type):
    """
    Metaclass for all models.
    """

    def __new__(cls, name, bases, attrs):
        super_new = super(ModelBase, cls).__new__
        #print 'attrs:',attrs
        parents = [b for b in bases if isinstance(b, ModelBase)]
        if not parents:
            # If this isn't a subclass of Model, don't do anything special.
            return super_new(cls, name, bases, attrs)

        # Create the class.
        module = attrs.pop('__module__')
        new_class = super_new(cls, name, bases, {'__module__': module})

        attr_meta = attrs.pop('Meta', None)
        if not attr_meta:
            meta = getattr(new_class, 'Meta', None)
        else:
            meta = attr_meta
            #base_meta = getattr(new_class, '_meta', None)
        #for k, v in attrs.items():
        #    if isinstance(v, fields.Field):
        #        v.contrib_to_class(new_class)
        new_class.add_to_class('_meta', Options(meta, **attrs))
        #for f in new_class._meta.fields:
        #    setattr(new_class,f.name,f)
        #if getattr(new_class, '_default_manager', None):
        #    new_class.add_to_class('objects', getattr(new_class, '_default_manager'))
        #else:
        #    new_class.add_to_class('objects', BaseManager(new_class))

        return new_class

    #@classmethod
    def add_to_class(cls, name, value):
        if hasattr(value, 'contribute_to_class'):
            value.contribute_to_class(cls, name)
        else:
            setattr(cls, name, value)


class Model(object):
    __metaclass__ = ModelBase
    _deferred = False

    def __init__(self, **kwargs):
        for f in self._meta.fields:
            val = f.fromString(kwargs.pop(f.name, None))
            setattr(self, f.name, val)
            if getattr(f, 'primary_key', False):
                setattr(self, 'pk', val)
        if kwargs:
            for k, v in kwargs.items():
                setattr(self, k, v)

    def save(self, **kwargs):
        pass

    def serialize(self):
        ret = {}
        for f in self._meta.fields:
            ret[f.name] = getattr(self, f.name)
        return ret