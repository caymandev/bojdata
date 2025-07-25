#!/usr/bin/env python3
"""Comprehensive examples of bojdata package usage"""

import bojdata
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

print("=== COMPREHENSIVE BOJDATA INTEGRATION EXAMPLES ===\n")

# 1. SEARCHING FOR DATA SERIES
print("1. SEARCHING FOR DATA SERIES")
print("-" * 40)

# Search for various economic indicators
search_queries = {
    "GDP": "gross domestic product",
    "Inflation": "inflation",
    "Interest": "interest",
    "Money Supply": "money supply",
    "Exchange": "exchange"
}

found_series = {}
for category, query in search_queries.items():
    print(f"\nSearching for {category} data...")
    try:
        results = bojdata.search_series(query, limit=3)
        if not results.empty:
            print(f"Found {len(results)} series:")
            for idx, row in results.iterrows():
                print(f"  - {row.get('series_id', 'N/A')}: {row.get('title', 'N/A')}")
            found_series[category] = results
    except Exception as e:
        print(f"  Error: {e}")

# 2. DOWNLOADING SINGLE SERIES
print("\n\n2. DOWNLOADING SINGLE SERIES")
print("-" * 40)

# Download monetary base data
try:
    print("\nDownloading Monetary Base data...")
    monetary_base = bojdata.read_boj(
        series="BS01'MABJMTA",
        start_date="2015-01-01",
        end_date=datetime.now().strftime("%Y-%m-%d")
    )
    
    if not monetary_base.empty:
        print(f"✓ Downloaded {len(monetary_base)} data points")
        print(f"  Date range: {monetary_base.index[0]} to {monetary_base.index[-1]}")
        print(f"  Latest value: {monetary_base.iloc[-1, 0]:,.0f}")
        
        # Calculate year-over-year growth
        if len(monetary_base) > 12:
            yoy_growth = ((monetary_base.iloc[-1, 0] / monetary_base.iloc[-13, 0]) - 1) * 100
            print(f"  YoY growth: {yoy_growth:.2f}%")
except Exception as e:
    print(f"✗ Error: {e}")

# 3. BATCH DOWNLOADING MULTIPLE SERIES
print("\n\n3. BATCH DOWNLOADING MULTIPLE SERIES")
print("-" * 40)

# Define series to download
series_to_download = [
    "BS01'MABJMTA",  # Monetary Base
    "BS01'MABJ_MABJ", # Alternative monetary base series
    "IR01",  # Interest rate
    "FM01"   # Exchange rate
]

try:
    print(f"\nBatch downloading {len(series_to_download)} series...")
    batch_data = bojdata.read_boj_batch(
        series_list=series_to_download,
        start_date="2020-01-01",
        end_date=datetime.now().strftime("%Y-%m-%d"),
        show_progress=True
    )
    
    if not batch_data.empty:
        print(f"✓ Downloaded data with shape: {batch_data.shape}")
        print("\nColumns downloaded:")
        for col in batch_data.columns:
            non_null = batch_data[col].notna().sum()
            print(f"  - {col}: {non_null} non-null values")
except Exception as e:
    print(f"✗ Error: {e}")

# 4. DATA TRANSFORMATIONS
print("\n\n4. DATA TRANSFORMATIONS")
print("-" * 40)

if 'monetary_base' in locals() and not monetary_base.empty:
    print("\nApplying transformations to Monetary Base data...")
    
    # Calculate various transformations
    series = monetary_base.iloc[:, 0]
    
    # Percent change
    pct_change = series.pct_change() * 100
    print(f"  Latest month-over-month change: {pct_change.iloc[-1]:.2f}%")
    
    # Moving averages
    ma_3 = series.rolling(window=3).mean()
    ma_12 = series.rolling(window=12).mean()
    
    # Trend calculation
    x = np.arange(len(series))
    trend = np.polyfit(x, series.values, 1)
    print(f"  Overall trend (slope): {trend[0]:,.2f} per month")
    
    # Volatility (standard deviation of returns)
    returns_vol = pct_change.std()
    print(f"  Volatility (std of returns): {returns_vol:.2f}%")

# 5. ADVANCED ANALYSIS
print("\n\n5. ADVANCED ANALYSIS")
print("-" * 40)

if 'batch_data' in locals() and not batch_data.empty:
    print("\nPerforming correlation analysis...")
    
    # Calculate correlation matrix
    corr_matrix = batch_data.corr()
    
    if not corr_matrix.empty:
        print("\nCorrelation Matrix:")
        print(corr_matrix.round(3))

# 6. METADATA AND RELEASE INFORMATION
print("\n\n6. METADATA AND RELEASE INFORMATION")
print("-" * 40)

# Get available datasets
try:
    print("\nFetching available BOJ datasets...")
    datasets = bojdata.get_boj_datasets()
    if not datasets.empty:
        print(f"✓ Found {len(datasets)} datasets")
        print("\nSample datasets:")
        for idx in range(min(5, len(datasets))):
            print(f"  - {datasets.iloc[idx].get('name', 'N/A')}")
except Exception as e:
    print(f"✗ Error: {e}")

# Get release calendar
try:
    print("\nFetching release calendar for current year...")
    releases = bojdata.get_releases(year=datetime.now().year)
    if not releases.empty:
        print(f"✓ Found {len(releases)} releases")
        # Show upcoming releases
        today = pd.Timestamp.now()
        upcoming = releases[releases.get('release_date', releases.index) > today]
        if not upcoming.empty:
            print(f"\nUpcoming releases: {len(upcoming)}")
except Exception as e:
    print(f"✗ Error: {e}")

# 7. ERROR HANDLING AND EDGE CASES
print("\n\n7. ERROR HANDLING AND EDGE CASES")
print("-" * 40)

# Test with invalid series ID
try:
    print("\nTesting with invalid series ID...")
    invalid_data = bojdata.read_boj(series="INVALID_SERIES_ID")
except Exception as e:
    print(f"✓ Handled error correctly: {type(e).__name__}")

# Test with future dates
try:
    print("\nTesting with future date range...")
    future_data = bojdata.read_boj(
        series="BS01'MABJMTA",
        start_date="2030-01-01",
        end_date="2035-01-01"
    )
    if future_data.empty:
        print("✓ Correctly returned empty DataFrame for future dates")
except Exception as e:
    print(f"✓ Handled error correctly: {type(e).__name__}")

# 8. EXPORT FUNCTIONALITY
print("\n\n8. EXPORT FUNCTIONALITY")
print("-" * 40)

# Create a comprehensive report
if 'monetary_base' in locals() and not monetary_base.empty:
    print("\nCreating comprehensive analysis report...")
    
    report_data = {
        'Date': monetary_base.index,
        'Monetary_Base': monetary_base.iloc[:, 0],
        'MoM_Change_%': monetary_base.iloc[:, 0].pct_change() * 100,
        'YoY_Change_%': monetary_base.iloc[:, 0].pct_change(12) * 100,
        'MA_3M': monetary_base.iloc[:, 0].rolling(3).mean(),
        'MA_12M': monetary_base.iloc[:, 0].rolling(12).mean()
    }
    
    report_df = pd.DataFrame(report_data)
    report_df.to_csv('boj_comprehensive_report.csv', index=False)
    print("✓ Saved comprehensive report to: boj_comprehensive_report.csv")
    
    # Save summary statistics
    summary = {
        'Metric': ['Mean', 'Std Dev', 'Min', 'Max', 'Latest', 'YoY Change %'],
        'Value': [
            monetary_base.iloc[:, 0].mean(),
            monetary_base.iloc[:, 0].std(),
            monetary_base.iloc[:, 0].min(),
            monetary_base.iloc[:, 0].max(),
            monetary_base.iloc[-1, 0],
            ((monetary_base.iloc[-1, 0] / monetary_base.iloc[-13, 0]) - 1) * 100 if len(monetary_base) > 12 else np.nan
        ]
    }
    
    summary_df = pd.DataFrame(summary)
    summary_df.to_csv('boj_analysis_summary.csv', index=False)
    print("✓ Saved analysis summary to: boj_analysis_summary.csv")

print("\n\n=== COMPREHENSIVE INTEGRATION COMPLETE ===")
print("\nThe bojdata package provides a FRED-like interface for Bank of Japan data.")
print("Key features demonstrated:")
print("  - Series search and discovery")
print("  - Single and batch data downloads")
print("  - Data transformations and analysis")
print("  - Metadata and release calendar access")
print("  - Error handling")
print("  - Export functionality")

# 9. VISUALIZATION EXAMPLE (commented out to avoid matplotlib dependency)
"""
# If you want to create visualizations, uncomment this section:
if 'monetary_base' in locals() and not monetary_base.empty:
    plt.figure(figsize=(12, 6))
    
    # Plot monetary base
    plt.subplot(2, 1, 1)
    plt.plot(monetary_base.index, monetary_base.iloc[:, 0], 'b-', label='Monetary Base')
    plt.title('Bank of Japan - Monetary Base')
    plt.ylabel('Amount')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Plot year-over-year change
    plt.subplot(2, 1, 2)
    yoy_change = monetary_base.iloc[:, 0].pct_change(12) * 100
    plt.plot(monetary_base.index, yoy_change, 'r-', label='YoY Change %')
    plt.title('Year-over-Year Change')
    plt.ylabel('Percent')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('boj_monetary_base_analysis.png', dpi=300, bbox_inches='tight')
    print("✓ Saved visualization to: boj_monetary_base_analysis.png")
"""