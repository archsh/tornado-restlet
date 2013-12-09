from sqlalchemy.orm.query import Query
from . import exceptions
import types
import logging
_logger = logging.getLogger('tornado.restlet')


def restruct_ext_fields(cls, extend_fields):

    def _f_(s):
        ss = s.split('.', 1)
        _logger.debug('_f_: %s', ss)
        return ss[0], ss[1] if len(ss) == 2 else None

    if not extend_fields:
        return {}
    result = {}
    for x, y in map(_f_, extend_fields):
        _logger.debug('[1]restruct_ext_fields> %s: %s', x, y)
        if x not in cls.__mapper__.relationships.keys():
            continue
        if x not in result:
            result[x] = [y] if y else []
        elif y:
            result[x].append(y)
    _logger.debug('[2]restruct_ext_fields> %s: %s', cls, result)
    return result


def serialize_object(cls, inst, include_fields=None, extend_fields=None):
    """serialize_object: serialize a single object from model instance into a dictionary.
    """
    _logger.debug('Inst: %s | %s', inst, type(inst))
    if isinstance(inst, (list, tuple, types.GeneratorType)):
        return map(lambda x: serialize_object(cls, x, include_fields=include_fields, extend_fields=extend_fields),
                   inst)
    if not isinstance(inst, cls):
        return None
    _logger.debug('serialize_object> extend_fields: %s', extend_fields)
    include_fields = list(set(include_fields or cls.__table__.c.keys()) | set(cls.__table__.primary_key.columns.keys()))
    if not set(include_fields) <= set(cls.__table__.c.keys()):
        raise exceptions.BadRequest(message='Column(s) "%s" does not exists!' % ','.join(list(
            set(include_fields) - set(cls.__table__.c.keys())
        )))
    result = dict([(k, getattr(inst, k)) for k in include_fields])
    # TODO: Extend fields ....
    if extend_fields:
        _logger.debug('serialize_object: extend_fields=%s', extend_fields)
        for relkey, relext in restruct_ext_fields(cls, extend_fields).items():
            rinst = cls.__mapper__.relationships[relkey]
            _logger.debug('====> %s: %s', relkey, relext)
            #if rinst.direction.name in ('MANYTOONE', 'ONETOONE'):
            incs = filter(lambda x: x.find('.') < 0 and x in rinst.mapper.class_.__table__.c.keys(), relext)
            #[relext] if (relext and relext.find('.') < 0 and relext in rinst.mapper.class_.__table__.c.keys()) else None
            exts = filter(lambda x: x.find('.') > 0 or x in rinst.mapper.class_.__mapper__.relationships.keys(), relext)
            #[relext] if relext and incs is None else None
            _logger.debug('inc=%s, ext=%s', incs, exts)
            result[relkey] = serialize_object(rinst.mapper.class_, getattr(inst, relkey),
                                              include_fields=incs,
                                              extend_fields=exts)
    #for relkey, relobj in cls.__mapper__.relationships.items():
    #    pass
    return result


def serialize_query(cls, inst, include_fields=None, extend_fields=None):
    """serialize_query: serialize a query into a list of object dictionary."""
    if not isinstance(inst, Query):
        return None
    #include_fields = include_fields or cls.__table__.c.keys()
    #result = list(inst.values(*[getattr(cls, k) for k in include_fields]))
    # TODO: Extend fields ....
    return serialize_object(cls, inst.all(), include_fields=include_fields, extend_fields=extend_fields)


def serialize(cls, inst, include_fields=None, extend_fields=None):
    """serialize: serialize model object(s) into dictionary(s)."""
    if isinstance(inst, Query):
        inst = inst.all()
        #return serialize_query(cls, inst, include_fields=include_fields,
        #                       extend_fields=extend_fields)
    return serialize_object(cls, inst, include_fields=include_fields, extend_fields=extend_fields)


