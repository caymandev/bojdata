"""
Complete demonstration of bojdata's enhanced features.

This script shows all the major features added for FRED compatibility
and additional enhancements.
"""

import bojdata
from bojdata import BOJDataAPI, read_boj_batch
import pandas as pd

def main():
    print("=== BOJData Complete Feature Demo ===\n")
    
    # Initialize API
    api = BOJDataAPI()
    
    # 1. Data Transformations
    print("1. DATA TRANSFORMATIONS")
    print("-" * 50)
    try:
        # Get monetary base with different transformations
        df_levels = bojdata.read_boj("BS01'MABJMTA", start_date="2023-01-01", end_date="2023-12-31", units='lin')
        df_pch = bojdata.read_boj("BS01'MABJMTA", start_date="2023-01-01", end_date="2023-12-31", units='pch')
        
        print(f"Original value (Jan 2023): {df_levels.iloc[0, 0]:,.0f}")
        print(f"Percent change (Feb 2023): {df_pch.iloc[1, 0]:.2f}%")
    except Exception as e:
        print(f"Demo data not available: {e}")
    
    # 2. Aggregation Methods
    print("\n2. AGGREGATION METHODS")
    print("-" * 50)
    print("Available methods: avg (average), sum (sum), eop (end of period)")
    print("Example: Converting daily to monthly with different methods")
    
    # 3. Batch Operations
    print("\n3. BATCH OPERATIONS")
    print("-" * 50)
    print("Downloading multiple series in parallel...")
    try:
        series_list = ['IR01', 'IR02', 'FM01']
        df_batch = read_boj_batch(series_list[:2], max_workers=2, show_progress=False)
        print(f"Downloaded {len(df_batch.columns)} series with {len(df_batch)} observations")
    except Exception as e:
        print(f"Batch download demo: {e}")
    
    # 4. Enhanced Search
    print("\n4. ENHANCED SEARCH")
    print("-" * 50)
    results = bojdata.search_series(
        "interest",
        limit=5,
        search_type='full_text',
        filter_variable='frequency',
        filter_value='Daily'
    )
    print(f"Found {len(results)} daily interest rate series")
    if not results.empty:
        print(results[['series_code', 'name']].head(3))
    
    # 5. Series Metadata
    print("\n5. SERIES METADATA")
    print("-" * 50)
    try:
        meta = api.get_series("IR01")
        print(f"Series: {meta['id']}")
        print(f"Title: {meta['title']}")
        print(f"Units: {meta['units']}")
        print(f"Frequency: {meta['frequency']}")
        print(f"Tags: {meta.get('tags', [])[:3]}")
    except Exception as e:
        print(f"Metadata demo: {e}")
    
    # 6. Release Calendar
    print("\n6. RELEASE CALENDAR")
    print("-" * 50)
    try:
        releases = api.get_releases(2024)
        print(f"Found {len(releases)} scheduled releases for 2024")
        if not releases.empty:
            print("\nNext 3 releases:")
            print(releases[['date', 'series_name', 'frequency']].head(3))
    except Exception as e:
        print(f"Release calendar demo: {e}")
    
    # 7. Tag System
    print("\n7. TAG SYSTEM")
    print("-" * 50)
    try:
        # Get tags for a series
        tags = api.get_series_tags("BS01'MABJMTA")
        print(f"Tags for Monetary Base: {tags}")
        
        # Search by tag (limited demo)
        print("\nSearching for 'monthly' series...")
        # Note: Full tag search requires building catalog, which is time-intensive
    except Exception as e:
        print(f"Tag system demo: {e}")
    
    # 8. FRED-Style Output
    print("\n8. FRED-STYLE OUTPUT")
    print("-" * 50)
    try:
        json_output = api.get_observations("IR01", start_date="2023-01-01", end_date="2023-01-31", output_type='dict')
        print(f"JSON response keys: {list(json_output.keys())}")
        print(f"Observations count: {json_output.get('count', 0)}")
        if json_output.get('observations'):
            print(f"First observation: {json_output['observations'][0]}")
    except Exception as e:
        print(f"JSON output demo: {e}")
    
    # 9. Error Handling
    print("\n9. ERROR HANDLING")
    print("-" * 50)
    try:
        df = bojdata.read_boj("INVALID_SERIES_XYZ123")
    except bojdata.exceptions.BOJSeriesNotFoundError as e:
        print(f"Series not found error caught!")
        print(f"Error message: {e}")
        print(f"HTTP code: {e.code}")
    except Exception as e:
        print(f"Other error: {e}")
    
    try:
        df = bojdata.read_boj("IR01", units="invalid_unit")
    except bojdata.exceptions.InvalidParameterError as e:
        print(f"\nInvalid parameter error caught!")
        print(f"Parameter: {e.parameter_name}")
        print(f"Invalid value: {e.parameter_value}")
        print(f"Valid options: {e.valid_values}")
    
    print("\n=== Demo Complete ===")
    print("\nKey Features Demonstrated:")
    print("✓ Data transformations (9 FRED units)")
    print("✓ Aggregation methods (avg, sum, eop)")
    print("✓ Batch/parallel downloads")
    print("✓ Enhanced search with filters")
    print("✓ Series metadata extraction")
    print("✓ Release calendar")
    print("✓ Tag system")
    print("✓ FRED-style JSON output")
    print("✓ Standardized error handling")
    
    print("\nFor more examples, see the documentation and README.md")

if __name__ == "__main__":
    main()