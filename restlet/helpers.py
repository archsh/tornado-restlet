# -*- coding: utf-8 -*-
import decimal
import datetime
from sqlalchemy import Column, Integer, Float, Numeric, SmallInteger, BigInteger
from sqlalchemy import DateTime, Date, Time
from sqlalchemy import Text, String, Unicode
from sqlalchemy import LargeBinary, Boolean  # , _Binary, NullType


__FIELD_PROCESSORS__ = {
    Integer: {
        'accept': (int, long),
        'support': (str, unicode),
        'convertor': int,
    },
    SmallInteger: {
        'accept': (int, long),
        'support': (str, unicode),
        'convertor': int,
    },
    BigInteger: {
        'accept': (int, long),
        'support': (str, unicode),
        'convertor': int,
    },
    Float: {
        'accept': (float, ),
        'support': (str, unicode, decimal.Decimal),
        'convertor': float,
    },
    Numeric: {
        'accept': (decimal.Decimal, ),
        'support': (str, unicode, float, int, long),
        'convertor': decimal.Decimal,
    },
    Date: {
        'accept': (datetime.date, ),
        'support': (str, unicode),
        'convertor': lambda x: datetime.datetime.strptime(x, '%Y-%m-%d').date(),
    },
    Time: {
        'accept': (datetime.time, ),
        'support': (str, unicode),
        'convertor': lambda x: datetime.datetime.strptime(x, '%H:%M:%S').time(),
    },
    DateTime: {
        'accept': (datetime.datetime, ),
        'support': (str, unicode),
        'convertor': lambda x: datetime.datetime.strptime(x, '%Y-%m-%dT%H:%M:%S'),
    },
    Boolean: {
        'accept': (bool, ),
        'support': (str, unicode),
        'convertor': lambda x: True if x and x.lower() == 'true' else False,
    }

}


def simple_field_processor(column):
    """simple_field_processor create a new function converts post values for SQLAlchemy columns.
    """
    assert column and isinstance(column, Column)
    _accept_types = None
    _support_types = None
    _converter = None
    for k, v in __FIELD_PROCESSORS__.items():
        if isinstance(column.type, k):
            _accept_types = v['accept']
            _support_types = v['support']
            _converter = v['convertor']
            break
    if not _accept_types or not _support_types or not _converter:
        return None

    def pf(value, record=None):
        if isinstance(value, _accept_types):
            return value
        elif isinstance(value, _support_types):
            return _converter(value)
        return value

    return pf