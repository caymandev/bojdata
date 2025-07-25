"""
Test bulk download improvements including progress indicators
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import pandas as pd

from bojdata.bulk_downloader import BOJBulkDownloader


class TestBulkDownloadImprovements:
    """Test bulk download functionality improvements"""
    
    def setup_method(self):
        """Create temporary directory for tests"""
        self.temp_dir = tempfile.mkdtemp()
        self.downloader = BOJBulkDownloader(self.temp_dir)
    
    def teardown_method(self):
        """Clean up temporary directory"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('bojdata.bulk_downloader.requests.get')
    def test_download_with_progress_bar(self, mock_get):
        """Test that download shows progress bar"""
        # Mock response with content-length header
        mock_response = MagicMock()
        mock_response.headers = {'content-length': '1000'}
        mock_response.iter_content = lambda chunk_size: [b'x' * 100 for _ in range(10)]
        mock_response.raise_for_status = Mock()
        mock_response.content = b'<html><a href="test.zip">Download</a></html>'
        mock_response.text = '<html><a href="test.zip">Download</a></html>'
        
        mock_get.return_value = mock_response
        
        # Test with progress bar enabled
        with patch('bojdata.bulk_downloader.tqdm') as mock_tqdm:
            self.downloader.download_flat_file('prices', show_progress=True)
            # Verify tqdm was called for progress bar
            mock_tqdm.assert_called()
    
    @patch('bojdata.bulk_downloader.requests.get')
    def test_download_without_progress_bar(self, mock_get):
        """Test download without progress bar"""
        # Mock response
        mock_response = MagicMock()
        mock_response.headers = {}
        mock_response.iter_content = lambda chunk_size: [b'x' * 100]
        mock_response.raise_for_status = Mock()
        mock_response.content = b'<html><a href="test.zip">Download</a></html>'
        
        mock_get.return_value = mock_response
        
        # Test with progress bar disabled
        with patch('builtins.print') as mock_print:
            self.downloader.download_flat_file('prices', show_progress=False)
            # Should print download message
            mock_print.assert_called()
            assert any('Downloading' in str(call) for call in mock_print.call_args_list)
    
    def test_download_all_with_error_reporting(self):
        """Test that download_all reports failures properly"""
        # Mock download to fail for some files
        def mock_download(file_type, force=False, show_progress=True):
            if file_type == 'tankan':
                raise Exception("Network error")
            return Path(f"/tmp/{file_type}.zip")
        
        self.downloader.download_flat_file = mock_download
        
        with patch('builtins.print') as mock_print:
            results = self.downloader.download_all_flat_files(show_progress=False)
            
            # Should report failures
            print_calls = [str(call) for call in mock_print.call_args_list]
            assert any('Failed downloads' in call for call in print_calls)
            assert any('tankan' in call for call in print_calls)
    
    def test_get_all_available_series_returns_valid_codes(self):
        """Test that get_all_available_series returns known codes"""
        series_df = self.downloader.get_all_available_series()
        
        assert isinstance(series_df, pd.DataFrame)
        assert len(series_df) > 0
        assert 'series_code' in series_df.columns
        
        # Check some known codes are present
        codes = series_df['series_code'].tolist()
        assert "BS01'MABJMTA" in codes
        assert "IR01" in codes


class TestProgressIndicators:
    """Test progress indicator functionality"""
    
    @patch('bojdata.bulk_downloader.requests.get')
    def test_tqdm_progress_with_content_length(self, mock_get):
        """Test tqdm progress bar with known file size"""
        temp_dir = tempfile.mkdtemp()
        downloader = BOJBulkDownloader(temp_dir)
        
        # Mock response with content-length
        mock_response = MagicMock()
        mock_response.headers = {'content-length': '1024'}
        mock_response.iter_content = lambda chunk_size: [b'x' * 256 for _ in range(4)]
        mock_response.raise_for_status = Mock()
        mock_response.content = b'<html><a href="test.zip">Download</a></html>'
        
        mock_get.return_value = mock_response
        
        # Capture tqdm calls
        with patch('bojdata.bulk_downloader.tqdm') as mock_tqdm_class:
            mock_tqdm_instance = MagicMock()
            mock_tqdm_class.return_value.__enter__.return_value = mock_tqdm_instance
            
            downloader.download_flat_file('prices', show_progress=True)
            
            # Verify tqdm was initialized with correct total
            mock_tqdm_class.assert_called_with(
                total=1024,
                unit='B',
                unit_scale=True,
                desc='prices_m_en.zip'
            )
            
            # Verify progress updates
            assert mock_tqdm_instance.update.call_count == 4
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)