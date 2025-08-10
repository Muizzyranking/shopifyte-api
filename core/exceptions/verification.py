class EmailVerificationError(Exception):
    """Base exception for email verification errors"""

    pass


class TokenExpiredError(EmailVerificationError):
    """Raised when a token has expired"""

    pass


class UserNotFound(EmailVerificationError):
    """Raised when user is not found"""

    pass


class EmailMisMatch(EmailVerificationError):
    """Raised when email doesn't match token"""

    pass
