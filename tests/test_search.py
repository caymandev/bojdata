"""
Tests for search module
"""

import pytest
from unittest.mock import Mock, patch

from bojdata.search import (
    search_for_series,
    extract_download_url,
    list_categories,
    get_series_metadata,
)
from bojdata.exceptions import BOJDataError


class TestSearchForSeries:
    """Tests for search_for_series function"""
    
    @patch("bojdata.search.requests.get")
    def test_search_basic(self, mock_get):
        """Test basic search functionality"""
        # Mock response
        response = Mock()
        response.raise_for_status = Mock()
        mock_get.return_value = response
        
        # Test - function returns URL, not content
        result = search_for_series("IR01")
        
        assert result is not None
        assert isinstance(result, str)
        assert "IR01" in result
        assert "stat-search.boj.or.jp" in result
    
    @patch("bojdata.search.requests.get")
    def test_search_success(self, mock_get):
        """Test successful search"""
        # Mock response
        response = Mock()
        response.raise_for_status = Mock()
        mock_get.return_value = response
        
        # Test - should return URL even for non-existent series
        result = search_for_series("NONEXISTENT")
        assert result is not None
        assert "NONEXISTENT" in result
    
    @patch("bojdata.search.requests.get")
    def test_search_connection_error(self, mock_get):
        """Test search with connection error"""
        mock_get.side_effect = Exception("Connection error")
        
        with pytest.raises(BOJDataError, match="Failed to search"):
            search_for_series("TEST")


class TestExtractDownloadUrl:
    """Tests for extract_download_url function"""
    
    @patch("bojdata.search.requests.get")
    def test_extract_url_success(self, mock_get):
        """Test successful URL extraction"""
        # Mock response with CSV link
        response = Mock()
        response.content = b'''
        <html>
        <body>
        <a href="/download/data.csv">Download CSV</a>
        </body>
        </html>
        '''
        response.raise_for_status = Mock()
        mock_get.return_value = response
        
        # Test
        url = extract_download_url("http://example.com/search")
        assert url == "https://www.stat-search.boj.or.jp/download/data.csv"
    
    @patch("bojdata.search.requests.get")
    def test_extract_url_no_csv(self, mock_get):
        """Test extraction when no CSV link found"""
        # Mock response without CSV link
        response = Mock()
        response.content = b'<html><body>No download available</body></html>'
        response.raise_for_status = Mock()
        mock_get.return_value = response
        
        # Test - should raise error when no CSV found
        with pytest.raises(BOJDataError, match="No CSV download link found"):
            extract_download_url("http://example.com/search")
    
    @patch("bojdata.search.requests.get")
    def test_extract_url_error(self, mock_get):
        """Test extraction with request error"""
        mock_get.side_effect = Exception("Request failed")
        
        with pytest.raises(BOJDataError, match="Failed to extract"):
            extract_download_url("http://example.com/search")


class TestListCategories:
    """Tests for list_categories function"""
    
    def test_list_categories(self):
        """Test listing categories"""
        categories = list_categories()
        
        assert isinstance(categories, list)
        assert len(categories) > 0
        assert "Interest Rates" in categories
        assert "Balance of Payments" in categories
        assert all(isinstance(cat, str) for cat in categories)


class TestGetSeriesMetadata:
    """Tests for get_series_metadata function"""
    
    def test_get_metadata(self):
        """Test getting series metadata"""
        metadata = get_series_metadata("TEST123")
        
        assert isinstance(metadata, dict)
        assert metadata["series_code"] == "TEST123"
        assert "name" in metadata
        assert "frequency" in metadata
        assert "unit" in metadata
        assert "start_date" in metadata
        assert "last_updated" in metadata