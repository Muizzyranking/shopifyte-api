from core.exceptions import NotFound


class ShopNotFound(NotFound):
    def __init__(self, message="Shop not found."):
        super().__init__(message)
