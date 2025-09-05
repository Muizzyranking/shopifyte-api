class BaseException(Exception):
    """Base exception class for custom exceptions."""

    def __init__(self, message="An error occurred"):
        self.message = message
        super().__init__(self.message)


class Unauthorized(BaseException):
    """Exception raised for unauthorized access."""

    def __init__(self, message="Unauthorized"):
        super().__init__(message)


class EmailSendError(BaseException):
    """Exception raised when there is an error sending an email."""

    def __init__(self, message="Error sending email"):
        super().__init__(message)


class TokenExpired(BaseException):
    """Exception raised when a token has expired."""

    def __init__(self, message="Token has expired."):
        super().__init__(message)


class InvalidToken(BaseException):
    """Exception raised when a token is invalid."""

    def __init__(self, message="Invalid token."):
        super().__init__(message)


class NotFound(BaseException):
    """Exception raised when a resource is not found."""

    def __init__(self, message="Resource not found"):
        super().__init__(message)
