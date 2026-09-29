class AppError(Exception):
    status_code = 500
    error_code = "APP_ERROR"
    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail
class NotFoundError(AppError):
    status_code = 404
    error_code = "NOT_FOUND"
class UnauthorizedError(AppError):
    status_code = 401
    error_code = "UNAUTHORIZED"
class ConflictError(AppError):
    status_code = 409
    error_code = "CONFLICT"
class ValidationError(AppError):
    status_code = 422
    error_code = "VALIDATION_ERROR"
class ForbiddenError(AppError):
    status_code = 403
    error_code = "FORBIDDEN"
