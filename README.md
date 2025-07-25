# bojdata

A comprehensive Python package for accessing ALL Bank of Japan (BOJ) statistical data.

## Overview

`bojdata` provides a complete interface to download and work with ALL data from the Bank of Japan's Time-Series Data Search portal. It handles the complexities of navigating the BOJ website, bulk downloading, and data processing to give you access to the entire BOJ statistical database.

## Features

### Core Features
- Download individual time series by code
- Search for available data series with enhanced parameters
- Automatic data cleaning and formatting
- Date range filtering
- Frequency conversion (daily, monthly, quarterly, yearly)
- Support for multiple series download

### FRED-Compatible Features (NEW)
- **Data Transformations**: All 9 FRED units (percent change, YoY, log, etc.)
- **FRED API Wrapper**: Familiar API for users migrating from FRED
- **Enhanced Search**: Full-text and series ID search with pagination and filters
- **Standardized Errors**: FRED-style error codes and messages
- **Multiple Output Formats**: Pandas DataFrames or FRED-style JSON
- **Batch Operations**: Parallel downloads for multiple series
- **Release Calendar**: Track when data series are updated
- **Series Metadata**: Detailed information about each series
- **Tag System**: Search and organize series by tags
- **Aggregation Methods**: Choose how to aggregate data (avg, sum, eop)

### Advanced Features
- **Bulk Download**: Download ALL available BOJ data at once
- **Comprehensive Search**: Search across all 13 data categories
- **Series Discovery**: Automatically discover all available series codes
- **Unified Database**: Build a searchable database of all BOJ data
- **Command-Line Interface**: Easy CLI access to all functionality
- **Category Navigation**: Browse data by category and subcategory
- **Flat File Support**: Download and process BOJ's flat file archives

## Installation

```bash
pip install bojdata
```

### Development Installation

```bash
git clone https://github.com/caymandev/bojdata.git
cd bojdata
pip install -e .[dev]
```

## Quick Start

### Basic Usage

```python
import bojdata

# Download a single series - Monetary Base
df = bojdata.read_boj(series="BS01'MABJMTA")

# Download multiple series
df = bojdata.read_boj(series=["IR01", "FM01", "BS01'MABJMTA"])

# Search for series
results = bojdata.search_series("interest rate")

# Download with data transformations (NEW)
df_pct_change = bojdata.read_boj(series="BS01'MABJMTA", units='pch')  # Percent change
df_yoy = bojdata.read_boj(series="PR01'IUQCP001", units='pc1')  # Year-over-year % change
```

### FRED-Compatible API (NEW)

```python
from bojdata import BOJDataAPI

api = BOJDataAPI()

# Get series metadata (like FRED)
metadata = api.get_series("BS01'MABJMTA")
print(f"Title: {metadata['title']}")  # 'Monetary Base (Average Amounts Outstanding)'
print(f"Frequency: {metadata['frequency']}")  # 'Monthly'

# Get observations with transformations
data = api.get_observations(
    "BS01'MABJMTA",
    start_date="2020-01-01",
    end_date="2023-12-31",
    units='pc1',  # Year-over-year percent change
    frequency='Q'  # Convert to quarterly
)

# Enhanced search with FRED parameters
results = api.search_series(
    "interest rate",
    search_type='full_text',
    limit=20,
    order_by='relevance'
)

# Get FRED-style JSON output
json_data = api.get_observations("IR01", output_type='dict')
```

### Advanced Usage - Access ALL BOJ Data

```python
from bojdata import BOJBulkDownloader, BOJComprehensiveSearch

# Download ALL available data
downloader = BOJBulkDownloader("./boj_data")
downloader.download_all_flat_files()
downloader.extract_and_process_all()

# Build a unified database
db_path = downloader.build_unified_database(output_format="sqlite")

# Search across ALL categories
searcher = BOJComprehensiveSearch()
results = searcher.search_all_categories("inflation")

# Discover all available series
catalog = searcher.build_series_catalog()
```

### Command-Line Interface

```bash
# Download specific series
bojdata download IR01 FM01 --output ./data

# Bulk download everything
bojdata bulk --build-db --db-format sqlite

# Search across all data
bojdata search "exchange rate" --limit 50

# Build complete series catalog
bojdata catalog --output all_series.csv
```

## Examples

### Download Monetary Base Data

```python
import bojdata

# Download monetary base average amounts outstanding
monetary_base = bojdata.read_boj(series="BS01'MABJMTA")
print(monetary_base.head())
```

### Download Multiple Interest Rate Series

```python
# Download overnight call rate and other interest rates
rates = bojdata.read_boj(series=["IR01", "IR02", "IR03"])
print(rates.columns)
```

### Convert Frequency

```python
# Download daily data and convert to monthly
daily_data = bojdata.read_boj(series="FM01", frequency="M")
```

### Data Transformations (NEW)

```python
# Available transformation units (FRED-compatible):
# 'lin' - Levels (no transformation) [default]
# 'chg' - Change from previous period
# 'ch1' - Change from year ago
# 'pch' - Percent change
# 'pc1' - Percent change from year ago
# 'pca' - Compounded annual rate
# 'cch' - Continuously compounded change
# 'cca' - Continuously compounded annual rate
# 'log' - Natural log

# Examples of transformations
df_levels = bojdata.read_boj("BS01'MABJMTA", units='lin')     # Original values
df_pct_chg = bojdata.read_boj("BS01'MABJMTA", units='pch')    # Period % change
df_yoy_chg = bojdata.read_boj("BS01'MABJMTA", units='pc1')    # YoY % change
df_log = bojdata.read_boj("BS01'MABJMTA", units='log')        # Natural log

# Combine with frequency conversion
df_quarterly_yoy = bojdata.read_boj(
    series="FM01",
    frequency="Q",     # Convert to quarterly
    units='pc1'        # Then calculate YoY change
)

# Different aggregation methods
# For flow data (e.g., trade balance), use sum aggregation
df_sum = bojdata.read_boj("BP02", frequency="Q", aggregation_method="sum")

# For stock data (e.g., monetary base), use end-of-period
df_eop = bojdata.read_boj("BS01'MABJMTA", frequency="Q", aggregation_method="eop")
```

### Batch Operations (NEW)

```python
from bojdata import read_boj_batch

# Download multiple series in parallel
series_list = ['IR01', 'IR02', 'IR03', 'FM01', 'FM02', 'BS01\'MABJMTA', 'MD01']
df = read_boj_batch(series_list, max_workers=5, units='pch')

# Using the API
api = BOJDataAPI()
df = api.get_observations_multi(
    ['IR01', 'FM01', 'BS01\'MABJMTA'],
    start_date='2020-01-01',
    units='pc1'
)
```

### Release Calendar (NEW)

```python
# Get release calendar
releases = api.get_releases(2024)
print(releases[['date', 'series_name', 'frequency']])

# Find when TANKAN is released
tankan_dates = api.get_release_dates('TANKAN')

# Export to calendar
from bojdata import BOJReleaseCalendar
calendar = BOJReleaseCalendar()
calendar.to_ical(2024, 'boj_releases.ics')
```

### Series Metadata & Tags (NEW)

```python
# Get detailed metadata
meta = api.get_series("BS01'MABJMTA")
print(f"Description: {meta['notes']}")
print(f"Units: {meta['units']}")
print(f"Tags: {meta['tags']}")
print(f"Related series: {meta['related_series']}")

# Search by tags
inflation_series = api.search_by_tag('inflation')
monthly_series = api.search_by_tag('monthly')

# Get all tags for a series
tags = api.get_series_tags("PR01'IUQCP001")
```

## For FRED Users

If you're familiar with the FRED API, bojdata now provides a compatible interface:

### Migration Examples

```python
# FRED Python                          # BOJData Equivalent
from fredapi import Fred               from bojdata import BOJDataAPI
fred = Fred(api_key='...')            api = BOJDataAPI()  # No API key needed!

# Get series info
fred.get_series_info('DGS10')        api.get_series('FM08')  # JGB 10-year yields

# Get observations
fred.get_series('DGS10')              api.get_observations('FM08')

# With transformations
fred.get_series('DGS10',              api.get_observations('FM08',
    units='pch')                          units='pch')

# Search
fred.search('text:interest rate')     api.search_series('interest rate')
```

### Key Differences

| Feature | FRED | BOJData |
|---------|------|---------|
| API Key | Required | Not needed |
| Data Source | Multiple sources | Bank of Japan only |
| Geographic Scope | Mainly US data | Japanese data |
| Vintage Data | Available | Not available |
| Rate Limits | Yes | No (but be respectful) |

## Discovering Valid Series Codes

### List All Valid Series Codes

```python
from bojdata import BOJDataAPI

api = BOJDataAPI()

# Get all known valid series codes
valid_codes = api.list_valid_series_codes()
print(valid_codes.head())

# Filter by category
interest_rates = valid_codes[valid_codes['category'] == 'Interest Rates']
print(interest_rates)
```

### Validate Series Codes

```python
# Check if a series code is valid
api.validate_series_code("BS01'MABJMTA")  # True
api.validate_series_code("INVALID")  # False

# Get helpful hints for invalid codes
from bojdata import read_boj

try:
    df = read_boj("interest rate")  # This will fail
except Exception as e:
    print(e)  # "Invalid series code 'interest rate'. Try IR01 or IR02 for interest rate data"
```

### Fuzzy Search for Series

```python
# Find series even with typos or partial names
results = api.search_series_fuzzy("monetary")  # Finds monetary base series
results = api.search_series_fuzzy("exchage")  # Finds exchange rate despite typo
results = api.search_series_fuzzy("tankan")  # Finds TANKAN survey series
```

For a complete list of valid series codes, see [docs/VALID_SERIES_CODES.md](docs/VALID_SERIES_CODES.md).

## Available Data

### Data Categories (13 Total)

1. **Interest Rates on Deposits and Loans**
   - Deposit rates, loan rates, interest rate spreads
   
2. **Financial Markets**
   - Stock indices, exchange rates, bond yields, money market rates
   
3. **Payment and Settlement**
   - BOJ-NET, Zengin System, electronic payments
   
4. **Money and Deposits**
   - Monetary base, money stock (M1, M2, M3), deposit aggregates
   
5. **Loans**
   - Bank lending by sector, loan growth, credit conditions
   
6. **Balance Sheets**
   - BOJ accounts, financial institution balance sheets
   
7. **Flow of Funds**
   - Sectoral accounts, financial flows, asset holdings
   
8. **Other Bank of Japan Statistics**
   - Research series, special surveys, historical data
   
9. **TANKAN (Business Survey)**
   - Business conditions, economic outlook, capital expenditure
   
10. **Prices**
    - CPI, PPI, CGPI, service price indices
    
11. **Public Finance**
    - Government debt, fiscal balance, bond issuance
    
12. **Balance of Payments**
    - Current account, trade statistics, international investment
    
13. **Others**
    - Regional statistics, miscellaneous indicators

### Flat File Downloads

Pre-packaged data files updated regularly:
- `prices_m_en.zip` - Monthly price data
- `fof_q_en.zip` - Quarterly flow of funds
- `tankan_q_en.zip` - Quarterly TANKAN survey
- `bp_m_en.zip` - Monthly balance of payments
- `bis_q_en.zip` - Quarterly BIS statistics

## Error Handling

The package provides FRED-compatible exceptions with HTTP error codes:

```python
from bojdata.exceptions import (
    BOJSeriesNotFoundError,
    InvalidParameterError,
    DataUnavailableError
)

# Series not found (404)
try:
    df = bojdata.read_boj(series="INVALID_CODE")
except BOJSeriesNotFoundError as e:
    print(f"Error: {e}")
    print(f"HTTP Code: {e.code}")  # 404

# Invalid parameter (400)
try:
    df = bojdata.read_boj(series="IR01", units="invalid_unit")
except InvalidParameterError as e:
    print(f"Error: {e}")
    print(f"Invalid parameter: {e.parameter_name}")
    print(f"Valid options: {e.valid_values}")

# Get error as dictionary (for API responses)
try:
    api = BOJDataAPI()
    api.get_series("INVALID")
except BOJSeriesNotFoundError as e:
    error_dict = e.to_dict()  # {'error_code': 404, 'error_message': '...'}
```

## Requirements

- Python 3.9+
- pandas
- requests
- beautifulsoup4
- numpy
- lxml

## License

MIT License - see LICENSE file for details.

## Development

### Running Tests

```bash
# Run tests with pytest
pytest

# Run tests with coverage
pytest --cov=bojdata

# Run tests for all Python versions
tox
```

### Code Quality

```bash
# Format code
black bojdata tests

# Sort imports
isort bojdata tests

# Lint code
flake8 bojdata tests

# Type check
mypy bojdata
```

### Releasing New Versions

This project uses `bump2version` and GitHub Actions for versioning and releases:

1. Update version:
   ```bash
   bump2version patch  # for bug fixes
   bump2version minor  # for new features
   bump2version major  # for breaking changes
   ```

2. Push to GitHub:
   ```bash
   git push origin main
   git push --tags
   ```

3. GitHub Actions will automatically:
   - Run tests on multiple Python versions
   - Publish to Test PyPI
   - Publish to PyPI (on tag push)
   - Create a GitHub release

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see LICENSE file for details.

## Disclaimer

This package is not affiliated with or endorsed by the Bank of Japan. Please refer to the BOJ website for official data and terms of use.