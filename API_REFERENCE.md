# BOJData API Reference

## Core Functions

### `read_boj()`

Download data series from the Bank of Japan.

```python
bojdata.read_boj(
    series=None,
    start_date=None,
    end_date=None,
    frequency=None,
    units='lin'
)
```

**Parameters:**
- `series` (str or list): BOJ series code(s) to download
- `start_date` (str or pd.Timestamp): Start date for data
- `end_date` (str or pd.Timestamp): End date for data
- `frequency` (str): Frequency conversion ('D', 'M', 'Q', 'Y')
- `units` (str): Data transformation (see transformations below)

**Returns:** pandas.DataFrame

**Example:**
```python
# Single series with transformation
df = bojdata.read_boj("BS01'MABJMTA", units='pch')

# Multiple series with date range
df = bojdata.read_boj(
    series=["IR01", "FM01"],
    start_date="2020-01-01",
    end_date="2023-12-31"
)
```

### `search_series()`

Search for BOJ data series.

```python
bojdata.search_series(
    keyword,
    category=None,
    limit=50,
    offset=0,
    search_type='full_text',
    order_by='relevance'
)
```

**Parameters:**
- `keyword` (str): Search term
- `category` (str): Filter by category
- `limit` (int): Maximum results
- `offset` (int): Skip results for pagination
- `search_type` (str): 'full_text' or 'series_id'
- `order_by` (str): Sort order ('relevance', 'name', 'series_id')

**Returns:** pandas.DataFrame with columns: series_code, name, category, frequency

## FRED-Compatible API

### `BOJDataAPI` Class

A wrapper providing FRED-style methods for accessing BOJ data.

#### `get_series(series_id)`

Get metadata for a series.

**Parameters:**
- `series_id` (str): BOJ series identifier

**Returns:** dict with keys:
- `id`: Series identifier
- `title`: Series name/description
- `frequency`: Data frequency
- `units`: Original units
- `seasonal_adjustment`: SA status
- `category`: Data category

**Example:**
```python
api = BOJDataAPI()
meta = api.get_series("BS01'MABJMTA")
print(meta['title'])  # "Monetary Base (Average Amounts Outstanding)"
```

#### `get_observations(series_id, ...)`

Get series data with optional transformations.

**Parameters:**
- `series_id` (str): BOJ series identifier
- `start_date` (str/pd.Timestamp): Start date
- `end_date` (str/pd.Timestamp): End date
- `units` (str): Transformation to apply
- `frequency` (str): Frequency conversion
- `output_type` (str): 'pandas' or 'dict'

**Returns:** pandas.DataFrame or dict (FRED-style JSON)

**Example:**
```python
# Get year-over-year percent change
data = api.get_observations("CPI", units='pc1')

# Get FRED-style JSON response
json_data = api.get_observations(
    "IR01",
    start_date="2023-01-01",
    output_type='dict'
)
```

#### `search_series(search_text, ...)`

Search for series with FRED-compatible parameters.

**Parameters:**
- `search_text` (str): Search query
- `search_type` (str): 'full_text' or 'series_id'
- `limit` (int): Maximum results
- `offset` (int): Pagination offset
- `order_by` (str): Sort order

**Returns:** pandas.DataFrame

#### `get_categories(category_id=None)`

Get BOJ data categories.

**Parameters:**
- `category_id` (int): Specific category (None for top-level)

**Returns:** pandas.DataFrame with id, name, parent_id

## Data Transformations

All transformation codes are FRED-compatible:

| Code | Description | Formula |
|------|-------------|---------|
| `lin` | Levels (no transformation) | x |
| `chg` | Change from previous period | x(t) - x(t-1) |
| `ch1` | Change from year ago | x(t) - x(t-n) where n=12 for monthly |
| `pch` | Percent change | 100 * (x(t)/x(t-1) - 1) |
| `pc1` | Percent change from year ago | 100 * (x(t)/x(t-n) - 1) |
| `pca` | Compounded annual rate | 100 * ((1 + x(t)/x(t-1))^p - 1) |
| `cch` | Continuously compounded change | 100 * ln(x(t)/x(t-1)) |
| `cca` | Continuously compounded annual rate | 100 * p * ln(x(t)/x(t-1)) |
| `log` | Natural log | ln(x) |

Where p = periods per year (12 for monthly, 4 for quarterly)

## Error Handling

### Exception Classes

All exceptions include FRED-compatible HTTP status codes:

#### `BOJSeriesNotFoundError` (404)
```python
try:
    df = bojdata.read_boj("INVALID")
except BOJSeriesNotFoundError as e:
    print(e.series_id)  # "INVALID"
    print(e.code)       # 404
```

#### `InvalidParameterError` (400)
```python
try:
    df = bojdata.read_boj("IR01", units="bad_unit")
except InvalidParameterError as e:
    print(e.parameter_name)   # "units"
    print(e.parameter_value)  # "bad_unit"
    print(e.valid_values)     # ['lin', 'chg', 'ch1', ...]
```

#### `DataUnavailableError` (503)
Raised when BOJ server is unavailable.

#### `RateLimitError` (429)
For future use if rate limiting is implemented.

## Advanced Classes

### `BOJBulkDownloader`

Download and process all BOJ flat files.

```python
downloader = BOJBulkDownloader(data_dir="./boj_data")
downloader.download_all_flat_files()
downloader.extract_and_process_all()
db_path = downloader.build_unified_database(output_format="parquet")
```

### `BOJComprehensiveSearch`

Search across all 13 BOJ data categories.

```python
searcher = BOJComprehensiveSearch()
results = searcher.search_all_categories("inflation")
catalog = searcher.build_series_catalog()
```

## Command-Line Interface

```bash
# Download series
bojdata download IR01 FM01 --start 2020-01-01 --units pch

# Search
bojdata search "interest rate" --limit 20

# Bulk download
bojdata bulk --build-db

# Build catalog
bojdata catalog --output series.csv
```

## Examples

### Economic Analysis
```python
# Calculate inflation rate
cpi = bojdata.read_boj("PR01'IUQCP001", units='pc1')

# Get monetary base growth
mb_growth = bojdata.read_boj("BS01'MABJMTA", units='pch')

# Compare interest rates
rates = bojdata.read_boj(
    series=["IR01", "IR02", "IR03"],
    start_date="2020-01-01",
    units='lin'
)
```

### FRED Migration
```python
# Instead of:
# fred.get_series('JPNCPIALLMINMEI', units='pc1')

# Use:
cpi_yoy = bojdata.read_boj("PR01'IUQCP001", units='pc1')
```

### Data Export
```python
# Get data in different formats
api = BOJDataAPI()

# For analysis (DataFrame)
df = api.get_observations("FM01")

# For API/web service (JSON-style dict)
json_data = api.get_observations("FM01", output_type='dict')

# Save to file
df.to_csv("exchange_rates.csv")
df.to_excel("exchange_rates.xlsx")
```