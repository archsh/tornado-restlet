# -*- coding: utf-8 -*-
class ExpressError(Exception):
    _error_ = 500
    _message_ = None

    def __init__(self, status=None, message=None, *args, **kwargs):
        super(ExpressError, self).__init__(*args, **kwargs)
        self.status = status
        self.message = message or self._message_

    @property
    def error(self):
        return self._error_


class BadRequest(ExpressError):
    _error_ = 400


class Unauthorized(ExpressError):
    _error_ = 401


class Forbidden(ExpressError):
    _error_ = 403


class NotFound(ExpressError):
    _error_ = 404


class MethodNotAllowed(ExpressError):
    _error_ = 405


class NotImplemented(ExpressError):
    _error_ = 501


class InvalidExpression(ExpressError):
    _error_ = 400
    _message_ = 'Invalid Expression.'


class InvalidData(ExpressError):
    _error_ = 400
    _message_ = 'Invalid Data.'