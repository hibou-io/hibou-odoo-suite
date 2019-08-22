class BaseException(Exception):
    """
    Base Exception which implements message attr on exceptions
    Required for: Python 3
    """
    def __init__(self, message=None, *args, **kwargs):
        self.message = message
        super(BaseException, self).__init__(
            self.message, *args, **kwargs
        )

    def __str__(self):
        return self.message or self.__class__.__name__


class WalmartException(BaseException):
    pass


class WalmartAuthenticationError(WalmartException):
    pass
