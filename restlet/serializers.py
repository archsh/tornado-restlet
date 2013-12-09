from sqlalchemy.orm.query import Query


def serialize_object(cls, inst, include_fields=None, extend_fields=None):
    """serialize_object: serialize a single object from model instance into a dictionary.
    """
    if not isinstance(inst, cls):
        return None
    include_fields = include_fields or cls.__table__.c.keys()
    result = dict([(k, getattr(inst, k)) for k in include_fields])
    # TODO: Extend fields ....
    return result


def serialize_query(cls, inst, include_fields=None, extend_fields=None):
    """serialize_query: serialize a query into a list of object dictionary."""
    if not isinstance(inst, Query):
        return None
    include_fields = include_fields or cls.__table__.c.keys()
    result = list(inst.values(*[getattr(cls, k) for k in include_fields]))
    # TODO: Extend fields ....
    return result


def serialize(cls, inst, include_fields=None, extend_fields=None):
    """serialize: serialize model object(s) into dictionary(s)."""
    if isinstance(inst, Query):
        return serialize_query(cls, inst, include_fields=include_fields,
                               extend_fields=extend_fields)
    else:
        return serialize_object(cls, inst, include_fields=include_fields,
                                extend_fields=extend_fields)


