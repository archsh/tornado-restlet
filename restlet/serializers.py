from sqlalchemy.orm.query import Query


def serialize_object(inst, include_fields=None, exclude_fields=None, extend_fields=None):
    """serialize_object: serialize a single object from model instance into a dictionary.
    """
    pass


def serialize_query(inst, include_fields=None, exclude_fields=None, extend_fields=None):
    """serialize_query: serialize a query into a list of object dictionary."""
    assert isinstance(inst, Query)
    inst.values()


def serialize(inst, include_fields=None, exclude_fields=None, extend_fields=None):
    """serialize: serialize model object(s) into dictionary(s)."""
    if isinstance(inst, Query):
        return serialize_query(inst, include_fields=include_fields,
                               exclude_fields=exclude_fields,
                               extend_fields=extend_fields)
    else:
        return serialize_object(inst, include_fields=include_fields,
                                exclude_fields=exclude_fields,
                                extend_fields=extend_fields)