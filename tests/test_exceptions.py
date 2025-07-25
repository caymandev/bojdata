"""
Tests for custom exceptions
"""

import pytest

from bojdata.exceptions import (
    BOJDataError,
    BOJConnectionError,
    BOJSeriesNotFoundError,
    BOJDataParsingError,
)


class TestExceptions:
    """Test custom exception classes"""
    
    def test_base_exception(self):
        """Test base BOJDataError"""
        with pytest.raises(BOJDataError) as exc_info:
            raise BOJDataError("Test error")
        
        assert str(exc_info.value) == "Test error"
        assert isinstance(exc_info.value, Exception)
    
    def test_connection_error(self):
        """Test BOJConnectionError"""
        with pytest.raises(BOJConnectionError) as exc_info:
            raise BOJConnectionError("Connection failed")
        
        assert str(exc_info.value) == "Connection failed"
        assert isinstance(exc_info.value, BOJDataError)
    
    def test_series_not_found_error(self):
        """Test BOJSeriesNotFoundError"""
        with pytest.raises(BOJSeriesNotFoundError) as exc_info:
            raise BOJSeriesNotFoundError("Series XYZ not found")
        
        assert "XYZ" in str(exc_info.value)
        assert isinstance(exc_info.value, BOJDataError)
    
    def test_parsing_error(self):
        """Test BOJDataParsingError"""
        with pytest.raises(BOJDataParsingError) as exc_info:
            raise BOJDataParsingError("Failed to parse CSV")
        
        assert "parse" in str(exc_info.value)
        assert isinstance(exc_info.value, BOJDataError)
    
    def test_exception_inheritance(self):
        """Test that all exceptions inherit from BOJDataError"""
        exceptions = [
            BOJConnectionError,
            BOJSeriesNotFoundError,
            BOJDataParsingError,
        ]
        
        for exc_class in exceptions:
            exc = exc_class("test")
            assert isinstance(exc, BOJDataError)
            assert isinstance(exc, Exception)