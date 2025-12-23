"""Custom exceptions for Yambot library"""


class YambotError(Exception):
    """Base exception for Yambot library"""
    pass


class APIError(YambotError):
    """Exception raised when API returns an error"""
    
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f'API Error {status_code}: {message}')


class RateLimitError(APIError):
    """Exception raised when rate limit is exceeded"""
    
    def __init__(self, message: str = 'Rate limit exceeded'):
        super().__init__(429, message)


class ValidationError(YambotError):
    """Exception raised when input validation fails"""
    pass


class AuthenticationError(APIError):
    """Exception raised when authentication fails"""
    
    def __init__(self, message: str = 'Authentication failed'):
        super().__init__(401, message)

