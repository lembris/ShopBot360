from fastapi import HTTPException, status


class ShopBotError(Exception):
    """Base application error."""

    def __init__(self, message: str, code: str = "error"):
        self.message = message
        self.code = code
        super().__init__(message)


class UnauthorizedError(ShopBotError):
    pass


class ForbiddenError(ShopBotError):
    pass


class NotFoundError(ShopBotError):
    pass


class ValidationError(ShopBotError):
    pass


class InsufficientStockError(ShopBotError):
    pass


def to_http_exception(exc: ShopBotError) -> HTTPException:
    status_map = {
        UnauthorizedError: status.HTTP_401_UNAUTHORIZED,
        ForbiddenError: status.HTTP_403_FORBIDDEN,
        NotFoundError: status.HTTP_404_NOT_FOUND,
        ValidationError: status.HTTP_400_BAD_REQUEST,
        InsufficientStockError: status.HTTP_409_CONFLICT,
    }
    return HTTPException(
        status_code=status_map.get(type(exc), status.HTTP_400_BAD_REQUEST),
        detail={"code": exc.code, "message": exc.message},
    )
