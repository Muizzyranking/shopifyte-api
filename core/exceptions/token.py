class TokenExpired(Exception):
    """Exception raised when a token has expired."""

    def __init__(self, message="Token has expired."):
        self.message = message
        super().__init__(self.message)


class InvalidToken(Exception):
    """Exception raised when a token is invalid."""

    def __init__(self, message="Invalid token."):
        self.message = message
        super().__init__(self.message)
