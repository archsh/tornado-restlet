# -*- coding: utf-8 -*-


class Dummy(object):
    """
    DummyCache which implemented nothing.
    """
    def set(self, key, value):
        pass

    def get(self, key):
        return None

    def has_key(self, key):
        return False

    def remove(self, key):
        pass


class Memmory(object):
    pass


class Redis(object):
    pass


class Memcached(object):
    pass