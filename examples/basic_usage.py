"""
Basic usage examples for bojdata package
"""

import bojdata
import pandas as pd


def example_single_series():
    """Download a single data series"""
    print("Example 1: Download single series")
    print("-" * 50)
    
    # Download monetary base data
    df = bojdata.read_boj(series="BS01'MABJMTA")
    
    print(f"Downloaded {len(df)} observations")
    print(f"Date range: {df.index.min()} to {df.index.max()}")
    print("\nFirst 5 rows:")
    print(df.head())
    print("\n")


def example_multiple_series():
    """Download multiple series at once"""
    print("Example 2: Download multiple series")
    print("-" * 50)
    
    # Download interest rate series
    series_codes = ["IR01", "IR02", "IR03"]
    df = bojdata.read_boj(series=series_codes)
    
    print(f"Downloaded {len(df.columns)} series")
    print(f"Series: {', '.join(df.columns)}")
    print("\nFirst 5 rows:")
    print(df.head())
    print("\n")


def example_date_filtering():
    """Download data with date filtering"""
    print("Example 3: Date filtering")
    print("-" * 50)
    
    # Download data for specific date range
    df = bojdata.read_boj(
        series="FM01",
        start_date="2022-01-01",
        end_date="2023-12-31"
    )
    
    print(f"Downloaded {len(df)} observations")
    print(f"Date range: {df.index.min()} to {df.index.max()}")
    print("\n")


def example_search_series():
    """Search for available series"""
    print("Example 4: Search for series")
    print("-" * 50)
    
    # Search for interest rate related series
    results = bojdata.search_series("interest rate")
    
    print(f"Found {len(results)} series matching 'interest rate'")
    print("\nSearch results:")
    print(results)
    print("\n")


def example_get_datasets():
    """Get list of available datasets"""
    print("Example 5: List available datasets")
    print("-" * 50)
    
    # Get all available datasets
    datasets = bojdata.get_boj_datasets()
    
    print(f"Found {len(datasets)} datasets")
    print("\nFirst 10 datasets:")
    print(datasets.head(10))
    print("\n")


def example_frequency_conversion():
    """Convert data frequency"""
    print("Example 6: Frequency conversion")
    print("-" * 50)
    
    # Download daily data and convert to monthly
    df = bojdata.read_boj(
        series="FM01",
        start_date="2023-01-01",
        end_date="2023-12-31",
        frequency="M"  # Convert to monthly
    )
    
    print(f"Converted to monthly frequency: {len(df)} observations")
    print("\nMonthly data:")
    print(df)
    print("\n")


def example_error_handling():
    """Demonstrate error handling"""
    print("Example 7: Error handling")
    print("-" * 50)
    
    try:
        # Try to download invalid series
        df = bojdata.read_boj(series="INVALID_SERIES_CODE")
    except bojdata.exceptions.BOJDataError as e:
        print(f"Error caught: {e}")
    
    print("\n")


if __name__ == "__main__":
    print("BOJData Usage Examples")
    print("=" * 50)
    print()
    
    # Run examples
    examples = [
        example_search_series,
        example_get_datasets,
        # These would actually download data:
        # example_single_series,
        # example_multiple_series,
        # example_date_filtering,
        # example_frequency_conversion,
        example_error_handling,
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"Example failed: {e}")
            print()
    
    print("Examples completed!")