"""
Retry logic and resilience utilities for bojdata package
"""

import time
from functools import wraps
from typing import Callable, Optional, Tuple, Type, Union

import requests

from .exceptions import BOJConnectionError, DataUnavailableError, RateLimitError


def exponential_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
) -> Callable:
    """
    Decorator for exponential backoff retry logic.
    
    Parameters
    ----------
    max_retries : int, default 3
        Maximum number of retry attempts
    initial_delay : float, default 1.0
        Initial delay in seconds
    max_delay : float, default 60.0
        Maximum delay in seconds
    exponential_base : float, default 2.0
        Base for exponential backoff
    jitter : bool, default True
        Add random jitter to delays
    
    Returns
    -------
    Callable
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (requests.exceptions.RequestException, 
                        BOJConnectionError, 
                        DataUnavailableError,
                        RateLimitError) as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        # Last attempt failed
                        raise
                    
                    # Calculate delay
                    delay = min(initial_delay * (exponential_base ** attempt), max_delay)
                    
                    # Add jitter if requested
                    if jitter:
                        import random
                        delay *= (0.5 + random.random())
                    
                    # Check if it's a rate limit error with retry-after header
                    if isinstance(e, requests.exceptions.RequestException) and hasattr(e, 'response') and e.response is not None:
                        retry_after = e.response.headers.get('Retry-After')
                        if retry_after:
                            try:
                                delay = float(retry_after)
                            except ValueError:
                                pass
                    
                    print(f"Request failed (attempt {attempt + 1}/{max_retries + 1}). "
                          f"Retrying in {delay:.1f} seconds...")
                    
                    time.sleep(delay)
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


def with_retry(
    func: Callable,
    max_retries: int = 3,
    retry_exceptions: Tuple[Type[Exception], ...] = (
        requests.exceptions.RequestException,
        BOJConnectionError,
        DataUnavailableError,
    ),
    delay: float = 1.0,
) -> Callable:
    """
    Simple retry wrapper for functions.
    
    Parameters
    ----------
    func : Callable
        Function to wrap
    max_retries : int, default 3
        Maximum number of retries
    retry_exceptions : tuple of Exception types
        Exceptions to retry on
    delay : float, default 1.0
        Delay between retries in seconds
        
    Returns
    -------
    Callable
        Wrapped function with retry logic
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except retry_exceptions as e:
                if attempt == max_retries:
                    raise
                print(f"Attempt {attempt + 1} failed: {e}. Retrying...")
                time.sleep(delay)
        
    return wrapper


def is_transient_error(exception: Exception) -> bool:
    """
    Check if an error is transient and should be retried.
    
    Parameters
    ----------
    exception : Exception
        Exception to check
        
    Returns
    -------
    bool
        True if error is transient
    """
    # Network errors
    if isinstance(exception, requests.exceptions.RequestException):
        if isinstance(exception, requests.exceptions.HTTPError):
            # Retry on 5xx errors and specific 4xx errors
            if hasattr(exception, 'response') and exception.response is not None:
                status = exception.response.status_code
                return status >= 500 or status in [429, 408]  # Server errors, rate limit, timeout
        else:
            # Connection errors, timeouts, etc.
            return True
    
    # BOJ-specific errors
    if isinstance(exception, (BOJConnectionError, DataUnavailableError, RateLimitError)):
        return True
    
    return False


def create_resilient_session(
    max_retries: int = 3,
    backoff_factor: float = 0.3,
    status_forcelist: Optional[Tuple[int, ...]] = None,
    timeout: float = 30.0,
) -> requests.Session:
    """
    Create a requests session with built-in retry logic.
    
    Parameters
    ----------
    max_retries : int, default 3
        Maximum number of retries
    backoff_factor : float, default 0.3
        Backoff factor for retries
    status_forcelist : tuple of int, optional
        HTTP status codes to retry on
    timeout : float, default 30.0
        Request timeout in seconds
        
    Returns
    -------
    requests.Session
        Configured session with retry logic
    """
    from requests.adapters import HTTPAdapter
    from requests.packages.urllib3.util.retry import Retry
    
    if status_forcelist is None:
        status_forcelist = (408, 429, 500, 502, 503, 504)
    
    session = requests.Session()
    
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=["GET", "POST"],
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Set default timeout
    session.request = lambda method, url, **kwargs: requests.Session.request(
        session, method, url, timeout=kwargs.pop('timeout', timeout), **kwargs
    )
    
    return session