# Changelog

All notable changes to bojdata will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- FRED-compatible data transformations (9 units: lin, chg, ch1, pch, pc1, pca, cch, cca, log)
- `BOJDataAPI` class providing FRED-style API methods
- `units` parameter to `read_boj()` for data transformations
- `aggregation_method` parameter for frequency conversion (avg, sum, eop)
- Enhanced search functionality with pagination, sorting, and filtering
- `filter_variable` and `filter_value` parameters for advanced search
- FRED-style error handling with HTTP status codes
- `InvalidParameterError` exception for better error messages
- Batch operations with `read_boj_batch()` for parallel downloads
- `get_observations_multi()` method for efficient multi-series retrieval
- Release calendar integration with `BOJReleaseCalendar` class
- Series metadata extraction with `SeriesMetadataExtractor`
- Tag system for series discovery and organization
- `search_by_tag()` and `get_series_tags()` methods
- Comprehensive API documentation and migration guide
- Support for both DataFrame and dictionary output formats
- iCal export for release calendar
- Related series discovery
- Bulk download functionality
- Comprehensive search across all categories
- Command-line interface
- Series catalog building
