"""
Main test suite for bojdata package
"""

import pytest
import pandas as pd
from datetime import datetime

import bojdata
from bojdata import BOJBulkDownloader, BOJComprehensiveSearch
from bojdata.exceptions import BOJDataError


class TestCore:
    """Test core functionality"""
    
    def test_read_boj_single_series(self):
        """Test reading a single series"""
        df = bojdata.read_boj(series="BS01'MABJMTA")
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert df.index.name == "Date"
    
    def test_read_boj_with_dates(self):
        """Test reading with date range"""
        df = bojdata.read_boj(
            series="BS01'MABJMTA",
            start_date="2024-01-01",
            end_date="2024-12-31"
        )
        assert len(df) <= 12  # Monthly data
        assert df.index[0] >= pd.Timestamp("2024-01-01")
    
    def test_read_boj_no_series_error(self):
        """Test error when no series provided"""
        with pytest.raises(BOJDataError, match="'series' parameter is required"):
            bojdata.read_boj()
    
    def test_search_series(self):
        """Test series search"""
        results = bojdata.search_series("interest rate")
        assert isinstance(results, pd.DataFrame)
        assert "series_code" in results.columns
        assert "name" in results.columns
    
    def test_get_boj_datasets(self):
        """Test getting dataset list"""
        datasets = bojdata.get_boj_datasets()
        assert isinstance(datasets, pd.DataFrame)
        assert len(datasets) > 0
        assert "name" in datasets.columns


class TestBulkDownloader:
    """Test bulk downloader functionality"""
    
    def test_initialization(self, tmp_path):
        """Test bulk downloader initialization"""
        downloader = BOJBulkDownloader(tmp_path)
        assert downloader.data_dir == tmp_path
        assert downloader.raw_dir.exists()
        assert downloader.processed_dir.exists()
        assert downloader.metadata_dir.exists()
    
    def test_flat_files_constant(self, tmp_path):
        """Test FLAT_FILES configuration"""
        downloader = BOJBulkDownloader(tmp_path)
        assert isinstance(downloader.FLAT_FILES, dict)
        assert "prices" in downloader.FLAT_FILES
        assert "tankan" in downloader.FLAT_FILES
        assert "flow_of_funds" in downloader.FLAT_FILES


class TestComprehensiveSearch:
    """Test comprehensive search functionality"""
    
    def test_initialization(self):
        """Test searcher initialization"""
        searcher = BOJComprehensiveSearch()
        assert hasattr(searcher, "session")
        assert hasattr(searcher, "CATEGORIES")
        assert len(searcher.CATEGORIES) > 0
    
    def test_search_all_categories(self):
        """Test searching across categories"""
        searcher = BOJComprehensiveSearch()
        results = searcher.search_all_categories("exchange", limit=5)
        assert isinstance(results, pd.DataFrame)
    
    def test_get_category_tree(self):
        """Test getting category tree"""
        searcher = BOJComprehensiveSearch()
        tree = searcher.get_category_tree()
        assert isinstance(tree, dict)
        assert len(tree) > 0


class TestPackage:
    """Test package-level functionality"""
    
    def test_version(self):
        """Test version attribute"""
        assert hasattr(bojdata, "__version__")
        assert isinstance(bojdata.__version__, str)
        assert "." in bojdata.__version__
    
    def test_all_exports(self):
        """Test __all__ exports"""
        assert hasattr(bojdata, "__all__")
        assert "read_boj" in bojdata.__all__
        assert "search_series" in bojdata.__all__
        assert "get_boj_datasets" in bojdata.__all__
        assert "BOJBulkDownloader" in bojdata.__all__
        assert "BOJComprehensiveSearch" in bojdata.__all__