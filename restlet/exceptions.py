# -*- coding: utf-8 -*-
class RestletError(Exception):
    _error_ = 500

    def __init__(self, status=None, message=None, *args, **kwargs):
        super(RestletError, self).__init__(*args, **kwargs)
        self.status = status
        self.message = message

    @property
    def error(self):
        return self._error_


class BadRequest(RestletError):
    _error_ = 400


class Unauthorized(RestletError):
    _error_ = 401


class Forbidden(RestletError):
    _error_ = 403


class NotFound(RestletError):
    _error_ = 404


class MethodNotAllowed(RestletError):
    _error_ = 405


class NotImplemented(RestletError):
    _error_ = 501