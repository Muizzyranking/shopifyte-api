class Unauthorized(Exception):
    """Exception raised for unauthorized access."""

    def __init__(self, message="Unauthorized"):
        self.message = message
        super().__init__(self.message)
