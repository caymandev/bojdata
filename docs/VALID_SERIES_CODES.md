# BOJ Data Series Codes Reference

This document provides a comprehensive list of valid Bank of Japan (BOJ) series codes that can be used with the bojdata package.

## Series Code Format

BOJ series codes follow specific patterns:

1. **Basic Format**: `PREFIX + NUMBER` (e.g., `IR01`, `FM02`, `BS01`)
2. **Extended Format**: `PREFIX + NUMBER + ' + SUFFIX` (e.g., `BS01'MABJMTA`, `PR01'IUQCP001`)

Valid prefixes include:
- `IR` - Interest Rates
- `FM` - Financial Markets
- `BS` - Balance Sheet (Monetary Base)
- `MD` - Money and Deposits
- `PR` - Prices
- `BP` - Balance of Payments
- `TK` - TANKAN Survey
- `PS` - Payment and Settlement
- `LN` - Loans
- `CP` - Corporate Prices
- `SP` - Service Prices
- `ST` - Statistics
- `FF` - Flow of Funds
- `BIS` - BIS Statistics

## Valid Series Codes by Category

### Interest Rates

| Series Code | Description | Frequency |
|------------|-------------|-----------|
| `IR01` | Uncollateralized Overnight Call Rate | Daily |
| `IR02` | Basic Loan Rate | Monthly |
| `IR03` | Average Interest Rates on Deposits | Monthly |
| `IR04` | Average Contract Interest Rates on Loans and Discounts | Monthly |

### Financial Markets

| Series Code | Description | Frequency |
|------------|-------------|-----------|
| `FM01` | Foreign Exchange Rates (USD/JPY) | Daily |
| `FM02` | Stock Market Indices (TOPIX) | Daily |
| `FM03` | Stock Market Indices (Nikkei 225) | Daily |
| `FM08` | Yields on Government Bonds | Daily |

### Money and Deposits

| Series Code | Description | Frequency |
|------------|-------------|-----------|
| `BS01'MABJMTA` | Monetary Base (Average Amounts Outstanding) | Monthly |
| `BS01'MABJ_MABJ` | Monetary Base (End of Period) | Monthly |
| `MD01` | Money Stock M1 | Monthly |
| `MD02` | Money Stock M2 | Monthly |
| `MD03` | Money Stock M3 | Monthly |

### Prices

| Series Code | Description | Frequency |
|------------|-------------|-----------|
| `PR01'IUQCP001` | Consumer Price Index | Monthly |
| `CP01` | Corporate Goods Price Index | Monthly |
| `SP01` | Services Producer Price Index | Monthly |

### Balance of Payments

| Series Code | Description | Frequency |
|------------|-------------|-----------|
| `BP01'CJAA` | Current Account | Monthly |
| `BP02` | Trade Balance | Monthly |
| `BP03` | Financial Account | Monthly |

### TANKAN Survey

| Series Code | Description | Frequency |
|------------|-------------|-----------|
| `TK01` | Business Conditions DI (Large Manufacturers) | Quarterly |
| `TK02` | Business Conditions DI (Large Non-manufacturers) | Quarterly |
| `TK03` | Business Conditions DI (Medium-sized Enterprises) | Quarterly |
| `TK04` | Business Conditions DI (Small Enterprises) | Quarterly |

### Flow of Funds

| Series Code | Description | Frequency |
|------------|-------------|-----------|
| `FF01` | Flow of Funds - Financial Assets and Liabilities | Quarterly |
| `FF02` | Flow of Funds - By Sector | Quarterly |

### Other Series

| Series Code | Description | Frequency |
|------------|-------------|-----------|
| `ST01` | Economic Statistics | Various |
| `PS01` | Payment and Settlement Statistics | Monthly |
| `LN01` | Loans by Deposit-taking Institutions | Monthly |

## Usage Examples

### Basic Usage

```python
from bojdata import read_boj, BOJDataAPI

# Using read_boj function
df = read_boj("BS01'MABJMTA")  # Monetary Base

# Using API wrapper
api = BOJDataAPI()
df = api.get_observations("IR01")  # Overnight Call Rate
```

### Multiple Series

```python
# Download multiple series at once
df = read_boj(["IR01", "IR02", "FM01"])

# With date range
df = read_boj(
    series=["BS01'MABJMTA", "MD01", "MD02"],
    start_date="2020-01-01",
    end_date="2023-12-31"
)
```

### Data Transformations

```python
# Percent change
df = read_boj("PR01'IUQCP001", units='pch')

# Year-over-year change
df = read_boj("BS01'MABJMTA", units='pc1')

# Convert to quarterly averages
df = read_boj("FM01", frequency='Q', aggregation_method='avg')
```

## Discovering Series Codes

The package provides several methods to discover valid series codes:

```python
from bojdata import BOJDataAPI

api = BOJDataAPI()

# List all known valid series codes
valid_codes = api.list_valid_series_codes()
print(valid_codes[valid_codes['category'] == 'Interest Rates'])

# Validate a series code
is_valid = api.validate_series_code("BS01'MABJMTA")  # True
is_valid = api.validate_series_code("INVALID")  # False

# Fuzzy search for series
results = api.search_series_fuzzy("monetary base")
results = api.search_series_fuzzy("interest")  # Finds interest rate series

# Search by keyword
results = api.search_series("exchange rate")
```

## Common Issues and Solutions

### Issue: Series Code Not Found

If you get a "Series not found" error, the package will provide helpful hints:

```python
# This will fail with a helpful error message
df = read_boj("interest rate")
# Error: Invalid series code 'interest rate'. Try IR01 or IR02 for interest rate data

# This will suggest the correct format
df = read_boj("BS01MABJMTA")  # Missing quote
# Error: Did you mean 'BS01'? BOJ codes use format like BS01'MABJMTA
```

### Issue: Unknown Series Code

If you're unsure about the correct series code:

```python
# Use fuzzy search
api = BOJDataAPI()
matches = api.search_series_fuzzy("exchange")
print(matches)  # Will show FM01 - Foreign Exchange Rates

# Or browse by category
all_codes = api.list_valid_series_codes()
financial = all_codes[all_codes['category'] == 'Financial Markets']
print(financial)
```

## Notes

1. Not all series codes listed here may have data for all historical periods
2. Some series may require specific date ranges
3. The BOJ may add new series or modify existing ones over time
4. For the most up-to-date information, visit the [BOJ Time-Series Data Search](https://www.stat-search.boj.or.jp/)

## See Also

- [BOJ Time-Series Data Search](https://www.stat-search.boj.or.jp/)
- [bojdata Package Documentation](../README.md)
- [Data Transformations Guide](./TRANSFORMATIONS.md)