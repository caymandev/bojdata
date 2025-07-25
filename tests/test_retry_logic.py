"""
Test retry logic and error handling improvements
"""

import pytest
import time
from unittest.mock import Mock, patch
import requests

from bojdata.retry import (
    exponential_backoff, 
    with_retry, 
    is_transient_error,
    create_resilient_session
)
from bojdata.exceptions import BOJConnectionError, DataUnavailableError, RateLimitError


class TestExponentialBackoff:
    """Test exponential backoff retry decorator"""
    
    def test_successful_on_first_try(self):
        """Test function succeeds on first try"""
        mock_func = Mock(return_value="success")
        decorated_func = exponential_backoff(max_retries=3)(mock_func)
        
        result = decorated_func()
        assert result == "success"
        assert mock_func.call_count == 1
    
    def test_retry_on_transient_error(self):
        """Test retry on transient network errors"""
        mock_func = Mock(side_effect=[
            requests.exceptions.ConnectionError("Network error"),
            requests.exceptions.ConnectionError("Network error"),
            "success"
        ])
        
        decorated_func = exponential_backoff(
            max_retries=3, 
            initial_delay=0.01,  # Fast for testing
            jitter=False
        )(mock_func)
        
        with patch('time.sleep') as mock_sleep:
            result = decorated_func()
            assert result == "success"
            assert mock_func.call_count == 3
            assert mock_sleep.call_count == 2  # Two retries
    
    def test_exponential_delay_calculation(self):
        """Test exponential delay increases correctly"""
        mock_func = Mock(side_effect=[
            BOJConnectionError("Error"),
            BOJConnectionError("Error"),
            BOJConnectionError("Error"),
            "success"
        ])
        
        decorated_func = exponential_backoff(
            max_retries=3,
            initial_delay=1.0,
            exponential_base=2.0,
            jitter=False
        )(mock_func)
        
        sleep_calls = []
        with patch('time.sleep', side_effect=lambda x: sleep_calls.append(x)):
            result = decorated_func()
            assert result == "success"
            
            # Check delays: 1, 2, 4
            assert len(sleep_calls) == 3
            assert sleep_calls[0] == 1.0
            assert sleep_calls[1] == 2.0
            assert sleep_calls[2] == 4.0
    
    def test_max_delay_respected(self):
        """Test that delays don't exceed max_delay"""
        mock_func = Mock(side_effect=[BOJConnectionError("Error")] * 5 + ["success"])
        
        decorated_func = exponential_backoff(
            max_retries=5,
            initial_delay=1.0,
            max_delay=3.0,
            exponential_base=2.0,
            jitter=False
        )(mock_func)
        
        sleep_calls = []
        with patch('time.sleep', side_effect=lambda x: sleep_calls.append(x)):
            result = decorated_func()
            assert result == "success"
            
            # Check that no delay exceeds max_delay
            assert all(delay <= 3.0 for delay in sleep_calls)
    
    def test_rate_limit_retry_after_header(self):
        """Test respecting Retry-After header for rate limits"""
        response_mock = Mock()
        response_mock.headers = {'Retry-After': '5'}
        
        error = requests.exceptions.HTTPError(response=response_mock)
        error.response = response_mock
        
        mock_func = Mock(side_effect=[error, "success"])
        
        decorated_func = exponential_backoff(max_retries=1)(mock_func)
        
        sleep_calls = []
        with patch('time.sleep', side_effect=lambda x: sleep_calls.append(x)):
            result = decorated_func()
            assert result == "success"
            assert sleep_calls[0] == 5.0  # Should use Retry-After value


class TestWithRetry:
    """Test simple retry wrapper"""
    
    def test_retry_on_specified_exceptions(self):
        """Test retry only on specified exceptions"""
        mock_func = Mock(side_effect=[
            BOJConnectionError("Error"),
            DataUnavailableError("Error"),
            "success"
        ])
        
        wrapped_func = with_retry(
            mock_func,
            max_retries=2,
            retry_exceptions=(BOJConnectionError, DataUnavailableError),
            delay=0.01
        )
        
        result = wrapped_func()
        assert result == "success"
        assert mock_func.call_count == 3
    
    def test_no_retry_on_other_exceptions(self):
        """Test no retry on non-specified exceptions"""
        mock_func = Mock(side_effect=ValueError("Not a network error"))
        
        wrapped_func = with_retry(
            mock_func,
            max_retries=3,
            retry_exceptions=(BOJConnectionError,),
            delay=0.01
        )
        
        with pytest.raises(ValueError):
            wrapped_func()
        assert mock_func.call_count == 1  # No retries


class TestTransientErrorDetection:
    """Test transient error detection"""
    
    def test_network_errors_are_transient(self):
        """Test that network errors are considered transient"""
        errors = [
            requests.exceptions.ConnectionError("Network error"),
            requests.exceptions.Timeout("Timeout"),
            requests.exceptions.RequestException("Generic request error"),
            BOJConnectionError("BOJ connection failed"),
            DataUnavailableError("Data temporarily unavailable"),
            RateLimitError("Rate limit exceeded"),
        ]
        
        for error in errors:
            assert is_transient_error(error) == True
    
    def test_http_5xx_errors_are_transient(self):
        """Test that 5xx HTTP errors are transient"""
        response = Mock()
        response.status_code = 503
        
        error = requests.exceptions.HTTPError(response=response)
        error.response = response
        
        assert is_transient_error(error) == True
    
    def test_rate_limit_429_is_transient(self):
        """Test that 429 rate limit is transient"""
        response = Mock()
        response.status_code = 429
        
        error = requests.exceptions.HTTPError(response=response)
        error.response = response
        
        assert is_transient_error(error) == True
    
    def test_client_errors_not_transient(self):
        """Test that 4xx errors (except 429, 408) are not transient"""
        response = Mock()
        response.status_code = 404
        
        error = requests.exceptions.HTTPError(response=response)
        error.response = response
        
        assert is_transient_error(error) == False
    
    def test_non_network_errors_not_transient(self):
        """Test that non-network errors are not transient"""
        errors = [
            ValueError("Value error"),
            KeyError("Key error"),
            Exception("Generic exception"),
        ]
        
        for error in errors:
            assert is_transient_error(error) == False


class TestResilientSession:
    """Test resilient session creation"""
    
    def test_session_has_retry_adapter(self):
        """Test that session has retry adapter configured"""
        session = create_resilient_session(max_retries=3)
        
        # Check that adapters are configured
        assert 'http://' in session.adapters
        assert 'https://' in session.adapters
        
        # Check adapter has retry configuration
        adapter = session.adapters['https://']
        assert hasattr(adapter, 'max_retries')
    
    @patch('requests.Session.request')
    def test_session_default_timeout(self, mock_request):
        """Test that session applies default timeout"""
        session = create_resilient_session(timeout=10.0)
        
        # Make a request
        session.get('https://example.com')
        
        # Check timeout was applied
        mock_request.assert_called()
        call_kwargs = mock_request.call_args[1]
        assert call_kwargs.get('timeout') == 10.0