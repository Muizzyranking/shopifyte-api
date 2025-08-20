class UserNotFound(Exception):
    """Raised when user is not found"""

    def __init__(self, message="User not found."):
        self.message = message
        super().__init__(self.message)
