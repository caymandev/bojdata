"""
Custom exceptions for bojdata package with FRED-style error handling.
"""


class BOJDataError(Exception):
    """Base exception for bojdata package"""
    def __init__(self, message, code=None):
        super().__init__(message)
        self.message = message
        self.code = code or 400
        
    def to_dict(self):
        """Convert exception to FRED-style error response."""
        return {
            'error_code': self.code,
            'error_message': self.message
        }


class BOJConnectionError(BOJDataError):
    """Raised when connection to BOJ website fails"""
    def __init__(self, message="Failed to connect to BOJ server"):
        super().__init__(message, code=503)


class BOJSeriesNotFoundError(BOJDataError):
    """Raised when requested series cannot be found"""
    def __init__(self, series_id):
        message = f"The series '{series_id}' was not found in the BOJ database"
        super().__init__(message, code=404)
        self.series_id = series_id


class BOJDataParsingError(BOJDataError):
    """Raised when data cannot be parsed correctly"""
    def __init__(self, message="Failed to parse BOJ data"):
        super().__init__(message, code=422)


class SeriesNotFoundError(BOJSeriesNotFoundError):
    """Alias for FRED compatibility"""
    pass


class InvalidParameterError(BOJDataError):
    """Raised when invalid parameters are provided"""
    def __init__(self, parameter_name, parameter_value, valid_values=None):
        if valid_values:
            message = (f"Invalid value '{parameter_value}' for parameter '{parameter_name}'. "
                      f"Valid values are: {', '.join(valid_values)}")
        else:
            message = f"Invalid value '{parameter_value}' for parameter '{parameter_name}'"
        super().__init__(message, code=400)
        self.parameter_name = parameter_name
        self.parameter_value = parameter_value
        self.valid_values = valid_values


class DataUnavailableError(BOJDataError):
    """Raised when data is temporarily unavailable"""
    def __init__(self, message="Data temporarily unavailable"):
        super().__init__(message, code=503)


class RateLimitError(BOJDataError):
    """Raised when rate limit is exceeded"""
    def __init__(self, message="Rate limit exceeded. Please try again later"):
        super().__init__(message, code=429)


class AuthenticationError(BOJDataError):
    """Raised when authentication fails (for future API key support)"""
    def __init__(self, message="Authentication failed"):
        super().__init__(message, code=401)