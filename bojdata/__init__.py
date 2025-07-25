"""
bojdata - A Python package for accessing Bank of Japan statistical data

This package provides a comprehensive interface to download and work with ALL data from
the Bank of Japan's Time-Series Data Search portal, including:
- Individual series downloads
- Bulk data downloads
- Comprehensive search across all categories
- Unified database creation
"""

# Version handling - supports both setuptools_scm and static versioning
try:
    from ._version import version as __version__
except ImportError:
    __version__ = "0.0.1"

from .bulk_downloader import BOJBulkDownloader
from .comprehensive_search import BOJComprehensiveSearch
from .core import (
    get_boj_datasets,
    read_boj,
    search_series,
)
from .api import BOJDataAPI
from .batch import read_boj_batch
from .releases import BOJReleaseCalendar, get_releases
from .metadata import SeriesMetadataExtractor, get_series_metadata

__all__ = [
    # Core functions
    "get_boj_datasets",
    "read_boj",
    "search_series",
    # Advanced classes
    "BOJBulkDownloader",
    "BOJComprehensiveSearch",
    # FRED-compatible API
    "BOJDataAPI",
    # Batch operations
    "read_boj_batch",
    # Release calendar
    "BOJReleaseCalendar",
    "get_releases",
    # Metadata
    "SeriesMetadataExtractor",
    "get_series_metadata",
]