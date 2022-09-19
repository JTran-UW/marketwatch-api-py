from ctypes import ArgumentError


class FieldNotFoundError(BaseException):
    pass

class TickerNotFoundError(BaseException):
    pass

class TransactionError(BaseException):
    pass

class GameNotFoundError(BaseException):
    pass

class UserNotFoundError(BaseException):
    pass
