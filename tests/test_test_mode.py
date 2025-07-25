"""
Test the test mode functionality
"""

import pytest
import pandas as pd
import numpy as np
from bojdata import BOJDataAPI
from bojdata.test_mode import (
    enable_test_mode, 
    disable_test_mode, 
    is_test_mode,
    MockDataGenerator
)


class TestTestModeToggle:
    """Test enabling/disabling test mode"""
    
    def test_enable_disable_test_mode(self):
        """Test toggling test mode on and off"""
        # Start with test mode off
        disable_test_mode()
        assert is_test_mode() == False
        
        # Enable test mode
        enable_test_mode()
        assert is_test_mode() == True
        
        # Disable again
        disable_test_mode()
        assert is_test_mode() == False
    
    def test_api_respects_test_mode_flag(self):
        """Test that API respects test mode setting"""
        enable_test_mode()
        api = BOJDataAPI()
        assert api.test_mode == True
        
        disable_test_mode()
        api = BOJDataAPI()
        assert api.test_mode == False
    
    def test_api_test_mode_parameter_overrides(self):
        """Test that explicit parameter overrides global setting"""
        # Global test mode off, but API in test mode
        disable_test_mode()
        api = BOJDataAPI(test_mode=True)
        assert api.test_mode == True
        
        # Global test mode on, but API not in test mode
        enable_test_mode()
        api = BOJDataAPI(test_mode=False)
        assert api.test_mode == False
        
        disable_test_mode()


class TestMockDataGeneration:
    """Test mock data generation"""
    
    def setup_method(self):
        """Create mock generator instance"""
        self.generator = MockDataGenerator()
    
    def test_generate_known_series(self):
        """Test generating data for known mock series"""
        series_codes = ["BS01'MABJMTA", "IR01", "FM01", "PR01'IUQCP001", "TEST_SERIES"]
        
        for code in series_codes:
            df = self.generator.generate_series(code)
            
            assert isinstance(df, pd.DataFrame)
            assert code in df.columns
            assert len(df) > 0
            assert df.index.name == "Date"
            assert pd.api.types.is_datetime64_any_dtype(df.index)
    
    def test_generate_with_date_range(self):
        """Test generating data with specific date range"""
        start = "2022-01-01"
        end = "2022-12-31"
        
        df = self.generator.generate_series("IR01", start_date=start, end_date=end)
        
        assert df.index[0] <= pd.Timestamp(end)
        assert df.index[-1] >= pd.Timestamp(start)
    
    def test_data_has_realistic_properties(self):
        """Test that generated data has realistic properties"""
        df = self.generator.generate_series("BS01'MABJMTA", periods=100)
        values = df.iloc[:, 0].values
        
        # Should have some variation
        assert values.std() > 0
        
        # Should have trend component
        # Check if later values tend to be higher (positive trend)
        first_half_mean = values[:50].mean()
        second_half_mean = values[50:].mean()
        assert second_half_mean > first_half_mean * 0.9  # Allow for some randomness
    
    def test_frequency_specific_generation(self):
        """Test that different frequencies generate appropriate data"""
        # Daily series
        daily_df = self.generator.generate_series("IR01", periods=30)
        assert len(daily_df) == 30
        
        # Monthly series  
        monthly_df = self.generator.generate_series("BS01'MABJMTA", 
                                                   start_date="2022-01-01",
                                                   end_date="2022-12-31")
        assert len(monthly_df) <= 12  # Should be monthly
        
        # Quarterly series
        quarterly_df = self.generator.generate_series("TK01",
                                                    start_date="2022-01-01", 
                                                    end_date="2022-12-31")
        assert len(quarterly_df) <= 4  # Should be quarterly
    
    def test_series_metadata_generation(self):
        """Test metadata generation for series"""
        # Known series
        meta = self.generator.get_series_metadata("BS01'MABJMTA")
        assert meta['id'] == "BS01'MABJMTA"
        assert meta['title'] == "Monetary Base (Average Amounts Outstanding)"
        assert meta['frequency'] == "Monthly"
        assert meta['category'] == "Money and Deposits"
        
        # Valid but unknown series
        meta = self.generator.get_series_metadata("IR99")
        assert meta['id'] == "IR99"
        assert "Mock" in meta['title']
        
        # Invalid series
        with pytest.raises(Exception):
            self.generator.get_series_metadata("INVALID")


class TestAPITestMode:
    """Test API functionality in test mode"""
    
    def setup_method(self):
        """Enable test mode"""
        enable_test_mode()
        self.api = BOJDataAPI(test_mode=True)
    
    def teardown_method(self):
        """Disable test mode"""
        disable_test_mode()
    
    def test_get_observations_returns_mock_data(self):
        """Test that get_observations returns mock data in test mode"""
        df = self.api.get_observations("BS01'MABJMTA")
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "BS01'MABJMTA" in df.columns
    
    def test_get_series_returns_mock_metadata(self):
        """Test that get_series returns mock metadata in test mode"""
        meta = self.api.get_series("IR01")
        
        assert meta['id'] == "IR01"
        assert 'title' in meta
        assert 'frequency' in meta
        assert meta['frequency'] == "Daily"
    
    def test_transformations_work_with_mock_data(self):
        """Test that data transformations work with mock data"""
        # Percent change
        df_pch = self.api.get_observations("BS01'MABJMTA", units='pch')
        assert len(df_pch) > 0
        
        # Year-over-year
        df_yoy = self.api.get_observations("PR01'IUQCP001", units='pc1')
        assert len(df_yoy) > 0
        
        # Log transformation
        df_log = self.api.get_observations("FM01", units='log')
        assert len(df_log) > 0
        assert np.all(df_log.iloc[:, 0] > 0)  # Log values should be positive
    
    def test_frequency_conversion_with_mock_data(self):
        """Test frequency conversion works with mock data"""
        # Convert daily to monthly
        df_monthly = self.api.get_observations("FM01", frequency='M')
        
        # Convert monthly to quarterly
        df_quarterly = self.api.get_observations("BS01'MABJMTA", frequency='Q')
        
        # Verify conversions worked
        assert len(df_monthly) > 0
        assert len(df_quarterly) > 0
    
    def test_test_mode_data_deterministic(self):
        """Test that test mode data is deterministic"""
        # Get data twice
        df1 = self.api.get_observations("TEST_SERIES", 
                                       start_date="2023-01-01",
                                       end_date="2023-12-31")
        df2 = self.api.get_observations("TEST_SERIES",
                                       start_date="2023-01-01", 
                                       end_date="2023-12-31")
        
        # Should be identical due to fixed seed
        pd.testing.assert_frame_equal(df1, df2)