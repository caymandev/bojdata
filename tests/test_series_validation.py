"""
Test series code validation and error handling improvements
"""

import pytest
from bojdata.utils import validate_series_code, get_series_code_hint
from bojdata.exceptions import SeriesNotFoundError


class TestSeriesCodeValidation:
    """Test series code format validation"""
    
    def test_valid_series_codes(self):
        """Test that valid series codes are accepted"""
        valid_codes = [
            "IR01",
            "FM01",
            "BS01'MABJMTA",
            "PR01'IUQCP001",
            "BP01'CJAA",
            "MD02",
            "TK01",
        ]
        
        for code in valid_codes:
            assert validate_series_code(code) == True, f"Code {code} should be valid"
    
    def test_invalid_series_codes(self):
        """Test that invalid series codes are rejected"""
        invalid_codes = [
            "interest rate",  # Natural language
            "INVALID",  # No numbers
            "123456",  # No letters
            "XX99",  # Invalid prefix
            "",  # Empty
            "I",  # Too short
            "IR01'MAUCALLO",  # This specific code from the issue
        ]
        
        for code in invalid_codes:
            assert validate_series_code(code) == False, f"Code {code} should be invalid"
    
    def test_case_insensitive_validation(self):
        """Test that validation is case-insensitive"""
        assert validate_series_code("ir01") == True
        assert validate_series_code("BS01'MABJMTA") == True
        assert validate_series_code("bs01'mabjmta") == True


class TestSeriesCodeHints:
    """Test helpful error messages"""
    
    def test_common_mistake_hints(self):
        """Test hints for common mistakes"""
        assert "IR01" in get_series_code_hint("interest")
        assert "FM01" in get_series_code_hint("exchange")
        assert "BS01'MABJMTA" in get_series_code_hint("monetary")
        assert "PR01'IUQCP001" in get_series_code_hint("price")
        assert "TK01" in get_series_code_hint("tankan")
    
    def test_missing_quote_hint(self):
        """Test hint for missing quote in series code"""
        hint = get_series_code_hint("BS01MABJMTA")
        assert "BS01'" in hint
        assert "format like" in hint
    
    def test_generic_hints(self):
        """Test generic hints for unrecognized patterns"""
        # No numbers
        hint = get_series_code_hint("ABCDEF")
        assert "need numbers" in hint
        
        # No letters
        hint = get_series_code_hint("123456")
        assert "need letters" in hint
        
        # Completely unrecognized
        hint = get_series_code_hint("XYZ123")
        assert "search_series" in hint or "list_valid_series_codes" in hint


class TestErrorMessageImprovements:
    """Test improved error messages in exceptions"""
    
    def test_series_not_found_with_hint(self):
        """Test SeriesNotFoundError accepts hint messages"""
        # Test with simple series ID
        error1 = SeriesNotFoundError("IR99")
        assert "IR99" in str(error1)
        assert "not found" in str(error1)
        
        # Test with formatted message including hint
        error2 = SeriesNotFoundError("Series 'interest rate' not found. Try IR01 or IR02")
        assert "interest rate" in str(error2)
        assert "Try IR01" in str(error2)
        assert error2.series_id == "interest rate"
    
    def test_error_preserves_series_id(self):
        """Test that SeriesNotFoundError extracts series_id correctly"""
        error = SeriesNotFoundError("The series 'BS01' was not found. Did you mean 'BS01\\'MABJMTA'?")
        assert error.series_id == "BS01"