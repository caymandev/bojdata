"""
Test API improvements including parameter fixes and new methods
"""

import pytest
import pandas as pd
from bojdata import BOJDataAPI
from bojdata.test_mode import enable_test_mode, disable_test_mode


class TestAPIParameterConsistency:
    """Test that API parameters are consistent"""
    
    def setup_method(self):
        """Enable test mode for API tests"""
        enable_test_mode()
        self.api = BOJDataAPI(test_mode=True)
    
    def teardown_method(self):
        """Disable test mode"""
        disable_test_mode()
    
    def test_search_series_limit_parameter(self):
        """Test that search_series accepts 'limit' parameter"""
        # This should not raise an error about 'max_results'
        results = self.api.search_series("interest rate", limit=5)
        assert isinstance(results, pd.DataFrame)
    
    def test_comprehensive_search_limit_parameter(self):
        """Test that comprehensive search uses correct parameter"""
        # This tests the internal call - should not raise parameter error
        results = self.api.search_series("monetary", search_type='full_text', limit=10)
        assert isinstance(results, pd.DataFrame)


class TestSeriesDiscoveryMethods:
    """Test new series discovery methods"""
    
    def setup_method(self):
        """Setup API instance"""
        self.api = BOJDataAPI()
    
    def test_list_valid_series_codes(self):
        """Test list_valid_series_codes method"""
        valid_codes = self.api.list_valid_series_codes()
        
        assert isinstance(valid_codes, pd.DataFrame)
        assert len(valid_codes) > 0
        assert 'series_code' in valid_codes.columns
        assert 'name' in valid_codes.columns
        assert 'category' in valid_codes.columns
        assert 'frequency' in valid_codes.columns
        
        # Check some known codes are present
        codes_list = valid_codes['series_code'].tolist()
        assert "BS01'MABJMTA" in codes_list
        assert "IR01" in codes_list
        assert "FM01" in codes_list
    
    def test_validate_series_code_method(self):
        """Test validate_series_code method"""
        assert self.api.validate_series_code("BS01'MABJMTA") == True
        assert self.api.validate_series_code("IR01") == True
        assert self.api.validate_series_code("INVALID") == False
        assert self.api.validate_series_code("interest rate") == False
    
    def test_search_series_fuzzy(self):
        """Test fuzzy search functionality"""
        # Test with exact match
        results = self.api.search_series_fuzzy("monetary base")
        assert len(results) > 0
        assert "BS01'MABJMTA" in results['series_code'].values
        
        # Test with typo
        results = self.api.search_series_fuzzy("intrest rate")  # Typo in 'interest'
        assert len(results) > 0
        assert any("IR" in code for code in results['series_code'].values)
        
        # Test with partial term
        results = self.api.search_series_fuzzy("exchange")
        assert len(results) > 0
        assert "FM01" in results['series_code'].values


class TestGetSeriesConsistency:
    """Test that get_series works consistently with read_boj"""
    
    def setup_method(self):
        """Enable test mode"""
        enable_test_mode()
        self.api = BOJDataAPI(test_mode=True)
    
    def teardown_method(self):
        """Disable test mode"""
        disable_test_mode()
    
    def test_get_series_with_valid_code(self):
        """Test get_series with valid BOJ codes"""
        # Test with simple code
        meta = self.api.get_series("IR01")
        assert meta['id'] == "IR01"
        assert 'title' in meta
        assert 'frequency' in meta
        
        # Test with complex code
        meta = self.api.get_series("BS01'MABJMTA")
        assert meta['id'] == "BS01'MABJMTA"
    
    def test_get_series_with_invalid_code(self):
        """Test get_series with invalid code provides helpful error"""
        with pytest.raises(Exception) as exc_info:
            self.api.get_series("interest rate")
        
        error_msg = str(exc_info.value)
        # Should either suggest a specific series or mention search_series
        assert ("Did you mean" in error_msg and "IR" in error_msg) or "search_series" in error_msg
    
    def test_get_series_suggests_fuzzy_match(self):
        """Test that get_series suggests similar codes"""
        with pytest.raises(Exception) as exc_info:
            self.api.get_series("MONETARY")
        
        error_msg = str(exc_info.value)
        # Should suggest BS01'MABJMTA or similar
        assert "BS01" in error_msg or "monetary" in error_msg.lower()


class TestFREDCompatibility:
    """Test FRED series mapping functionality"""
    
    def setup_method(self):
        """Enable test mode"""
        enable_test_mode()
        self.api = BOJDataAPI(test_mode=True)
    
    def teardown_method(self):
        """Disable test mode"""
        disable_test_mode()
    
    def test_fred_series_mapping(self):
        """Test FRED to BOJ series mapping"""
        # Test with FRED series code
        meta = self.api.get_series_fred_compatible("DEXJPUS")
        # Should map to FM01
        assert meta['id'] in ["FM01", "DEXJPUS"]  # Might return either
    
    def test_fred_series_not_found_helpful_error(self):
        """Test helpful error for unmapped FRED series"""
        with pytest.raises(Exception) as exc_info:
            self.api.get_series_fred_compatible("DGS10")  # US 10-year treasury
        
        error_msg = str(exc_info.value)
        # Should suggest BOJ alternative
        assert "FM08" in error_msg or "JGB" in error_msg.lower() or "bond" in error_msg.lower()