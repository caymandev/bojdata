"""
Tests for core functionality
"""

import pandas as pd
import pytest
from unittest.mock import Mock, patch

from bojdata import read_boj, get_boj_datasets, search_series
from bojdata.exceptions import BOJDataError, SeriesNotFoundError


class TestReadBOJ:
    """Tests for read_boj function"""
    
    @patch("bojdata.core.pd.read_csv")
    @patch("bojdata.core.requests.get")
    def test_read_single_series(self, mock_get, mock_read_csv):
        """Test reading a single series"""
        # Mock search results page with CSV link
        search_response = Mock()
        search_response.content = b'''
        <html>
        <body>
        <a href="/ssi/mtshtml/nme_R000.1234.20240101.01.csv">Download CSV</a>
        </body>
        </html>
        '''
        search_response.raise_for_status = Mock()
        mock_get.return_value = search_response
        
        # Mock CSV data
        mock_df = pd.DataFrame({
            'Date': ['2023-12', '2023-11', '2023-10'],
            "BS01'MABJMTA": [650000, 645000, 640000]
        })
        mock_read_csv.return_value = mock_df
        
        # Test
        df = read_boj(series="BS01'MABJMTA")
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert "BS01'MABJMTA" in df.columns
        assert df.index.name == "Date"
    
    def test_read_no_series_error(self):
        """Test that error is raised when no series provided"""
        with pytest.raises(BOJDataError, match="'series' parameter is required"):
            read_boj()
    
    @patch("bojdata.utils.list_valid_series_codes")
    @patch("bojdata.core.create_resilient_session")
    def test_read_multiple_series(self, mock_session, mock_list_valid):
        """Test reading multiple series"""
        # Mock valid series codes
        mock_list_valid.return_value = pd.DataFrame({
            'series_code': ['IR01', 'FM01'],
            'name': ['Interest Rate', 'Foreign Exchange'],
            'category': ['Interest Rates', 'Financial Markets'],
            'frequency': ['Daily', 'Daily']
        })
        
        # Mock session
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        
        # Mock CSV response data
        csv_resp1 = Mock()
        csv_resp1.text = "Date,IR01\n2023-12,100\n2023-11,200"
        csv_resp1.raise_for_status = Mock()
        
        csv_resp2 = Mock()
        csv_resp2.text = "Date,FM01\n2023-12,101\n2023-11,201"
        csv_resp2.raise_for_status = Mock()
        
        # Mock responses for two series
        search_resp1 = Mock()
        search_resp1.content = b'<a href="/csv1.csv">CSV</a>'
        search_resp1.raise_for_status = Mock()
        
        search_resp2 = Mock()
        search_resp2.content = b'<a href="/csv2.csv">CSV</a>'
        search_resp2.raise_for_status = Mock()
        
        mock_session_instance.get.side_effect = [search_resp1, csv_resp1, search_resp2, csv_resp2]
        
        # Test
        df = read_boj(series=["IR01", "FM01"])
        
        assert isinstance(df, pd.DataFrame)
        assert len(df.columns) == 2
    
    @patch("bojdata.utils.list_valid_series_codes")
    @patch("bojdata.core.create_resilient_session")
    def test_date_filtering(self, mock_session, mock_list_valid):
        """Test date range filtering"""
        # Mock valid series codes
        mock_list_valid.return_value = pd.DataFrame({
            'series_code': ['IR01'],
            'name': ['Interest Rate'],
            'category': ['Interest Rates'],
            'frequency': ['Daily']
        })
        
        # Mock session
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        
        # Mock CSV response
        csv_resp = Mock()
        csv_resp.text = "Date,IR01\n2023-12-01,100\n2023-11-01,200\n2023-10-01,300\n2023-09-01,400"
        csv_resp.raise_for_status = Mock()
        
        # Mock response
        search_response = Mock()
        search_response.content = b'<a href="/test.csv">CSV</a>'
        search_response.raise_for_status = Mock()
        
        mock_session_instance.get.side_effect = [search_response, csv_resp]
        
        # Test with date range
        df = read_boj(
            series="IR01",
            start_date="2023-10-01",
            end_date="2023-11-30"
        )
        
        assert len(df) == 2
        assert df.index.min() >= pd.Timestamp("2023-10-01")
        assert df.index.max() <= pd.Timestamp("2023-11-30")


class TestGetBOJDatasets:
    """Tests for get_boj_datasets function"""
    
    @patch("bojdata.core.requests.get")
    def test_get_datasets(self, mock_get):
        """Test retrieving dataset list"""
        # Mock response
        response = Mock()
        response.content = b'''
        <html>
        <body>
        <div class="category">
            <h3>Interest Rates</h3>
            <a href="/data/ir01.csv">Overnight Call Rate</a>
            <a href="/data/ir02.zip">Term Interest Rates</a>
        </div>
        </body>
        </html>
        '''
        response.raise_for_status = Mock()
        mock_get.return_value = response
        
        # Test
        df = get_boj_datasets()
        
        assert isinstance(df, pd.DataFrame)
        assert "name" in df.columns
        assert "category" in df.columns
        assert "url" in df.columns
        assert len(df) >= 2


class TestSearchSeries:
    """Tests for search_series function"""
    
    def test_search_basic(self):
        """Test basic search functionality"""
        results = search_series("interest rate")
        
        assert isinstance(results, pd.DataFrame)
        assert "series_code" in results.columns
        assert "name" in results.columns
        assert "category" in results.columns
        assert "frequency" in results.columns
    
    def test_search_with_category(self):
        """Test search with category filter"""
        results = search_series("overnight", category="Interest Rates")
        
        assert isinstance(results, pd.DataFrame)
        if len(results) > 0:
            assert all(results["category"] == "Interest Rates")
    
    def test_search_limit(self):
        """Test search result limit"""
        results = search_series("rate", limit=2)
        
        assert len(results) <= 2


class TestPrivateFunctions:
    """Tests for private helper functions"""
    
    @patch("bojdata.utils.list_valid_series_codes")
    @patch("bojdata.core.create_resilient_session")
    def test_download_with_frequency_resample(self, mock_session, mock_list_valid):
        """Test downloading with frequency resampling"""
        from bojdata.core import _download_single_series
        
        # Mock valid series codes
        mock_list_valid.return_value = pd.DataFrame({
            'series_code': ['IR01'],
            'name': ['Interest Rate'],
            'category': ['Interest Rates'],
            'frequency': ['Daily']
        })
        
        # Mock session
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        
        # Mock CSV response with daily data
        dates = pd.date_range('2023-01-01', '2023-01-10', freq='D')
        csv_data = "Date,IR01\n"
        for i, date in enumerate(dates):
            csv_data += f"{date.strftime('%Y-%m-%d')},{i}\n"
        
        csv_resp = Mock()
        csv_resp.text = csv_data.strip()
        csv_resp.raise_for_status = Mock()
        
        # Mock response
        search_response = Mock()
        search_response.content = b'<a href="/data.csv">CSV</a>'
        search_response.raise_for_status = Mock()
        
        mock_session_instance.get.side_effect = [search_response, csv_resp]
        
        # Test with monthly frequency
        df = _download_single_series("IR01", frequency="M")
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1  # Should be aggregated to one month
    
    @patch("bojdata.utils.list_valid_series_codes")
    @patch("bojdata.core.create_resilient_session")
    def test_download_invalid_frequency(self, mock_session, mock_list_valid):
        """Test downloading with invalid frequency"""
        from bojdata.core import _download_single_series
        
        # Mock valid series codes
        mock_list_valid.return_value = pd.DataFrame({
            'series_code': ['IR01'],
            'name': ['Interest Rate'],
            'category': ['Interest Rates'],
            'frequency': ['Daily']
        })
        
        # Mock session
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        
        # Mock CSV response
        csv_resp = Mock()
        csv_resp.text = "Date,IR01\n2023-01-01,100"
        csv_resp.raise_for_status = Mock()
        
        # Mock response
        search_response = Mock()
        search_response.content = b'<a href="/data.csv">CSV</a>'
        search_response.raise_for_status = Mock()
        
        mock_session_instance.get.side_effect = [search_response, csv_resp]
        
        # Test with invalid frequency (should warn and return original)
        with pytest.warns(UserWarning, match="Invalid frequency"):
            df = _download_single_series("IR01", frequency="INVALID")
        
        assert len(df) == 1  # Original data unchanged
    
    @patch("bojdata.utils.list_valid_series_codes")
    @patch("bojdata.core.create_resilient_session")
    def test_download_no_csv_link(self, mock_session, mock_list_valid):
        """Test download when no CSV link found"""
        from bojdata.core import _download_single_series
        
        # Mock valid series codes
        mock_list_valid.return_value = pd.DataFrame({
            'series_code': ['IR01'],
            'name': ['Interest Rate'],
            'category': ['Interest Rates'],
            'frequency': ['Daily']
        })
        
        # Mock session
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        
        # Mock response without CSV link
        search_response = Mock()
        search_response.content = b'<html><body>No CSV here</body></html>'
        search_response.raise_for_status = Mock()
        mock_session_instance.get.return_value = search_response
        
        # Test
        with pytest.raises(SeriesNotFoundError, match="was not found in the BOJ database"):
            _download_single_series("IR01")
    
    def test_filter_date_range(self):
        """Test _filter_date_range function"""
        from bojdata.core import _filter_date_range
        
        # Create test dataframe
        dates = pd.date_range('2023-01-01', '2023-12-31', freq='ME')
        df = pd.DataFrame({'value': range(len(dates))}, index=dates)
        
        # Test filtering
        result = _filter_date_range(
            df,
            pd.Timestamp('2023-03-01'),
            pd.Timestamp('2023-06-30')
        )
        
        assert len(result) == 4  # March through June
        assert result.index.min() >= pd.Timestamp('2023-03-01')
        assert result.index.max() <= pd.Timestamp('2023-06-30')
    
    def test_resample_data(self):
        """Test _resample_data function"""
        from bojdata.core import _resample_data
        
        # Create daily data
        dates = pd.date_range('2023-01-01', '2023-01-31', freq='D')
        df = pd.DataFrame({'value': range(len(dates))}, index=dates)
        
        # Test quarterly resampling
        result = _resample_data(df, 'Q')
        assert len(result) == 1  # One quarter
        
        # Test yearly resampling
        result = _resample_data(df, 'Y')
        assert len(result) == 1  # One year