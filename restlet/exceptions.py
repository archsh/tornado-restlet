# -*- coding: utf-8 -*-
class RestletError(Exception):
    def __init__(self, error=500, status=None, message=None, *args, **kwargs):
        super(RestletError, self).__init__(*args, **kwargs)
        self.error = error
        self.status = status
        self.message = message


class BadRequest(RestletError):
    pass


class Unauthorized(RestletError):
    pass


class Throttled(RestletError):
    pass