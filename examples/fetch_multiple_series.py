#!/usr/bin/env python3
"""
Example: Fetch multiple BOJ series for a specific period and compare them
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import bojdata


def fetch_economic_indicators(start_date, end_date):
    """
    Fetch multiple economic indicators from BOJ for analysis
    
    Parameters:
    -----------
    start_date : str
        Start date in format 'YYYY-MM-DD'
    end_date : str
        End date in format 'YYYY-MM-DD'
    
    Returns:
    --------
    dict
        Dictionary of DataFrames for each indicator
    """
    print(f"Fetching BOJ economic indicators from {start_date} to {end_date}...")
    print("-" * 60)
    
    # Define the indicators we want to fetch
    indicators = {
        "Monetary Base": "BS01'MABJMTA",
        # These might not all work, but we'll try
        # "Interest Rate": "IR01",
        # "Exchange Rate": "FM01",
    }
    
    results = {}
    
    for name, series_code in indicators.items():
        try:
            print(f"Fetching {name} ({series_code})...", end=" ")
            df = bojdata.read_boj(
                series=series_code,
                start_date=start_date,
                end_date=end_date
            )
            results[name] = df
            print(f"✓ Success ({len(df)} observations)")
        except Exception as e:
            print(f"✗ Failed: {str(e)}")
            
    return results


def search_and_fetch_series(keyword, start_date, end_date, limit=3):
    """
    Search for series by keyword and fetch the data
    
    Parameters:
    -----------
    keyword : str
        Search keyword
    start_date : str
        Start date for data
    end_date : str
        End date for data
    limit : int
        Maximum number of series to fetch
    
    Returns:
    --------
    dict
        Dictionary of fetched data
    """
    print(f"\nSearching for '{keyword}' series...")
    print("-" * 60)
    
    # Search for series
    search_results = bojdata.search_series(keyword, limit=limit)
    
    if search_results.empty:
        print(f"No series found for '{keyword}'")
        return {}
    
    print(f"Found {len(search_results)} series:")
    for _, row in search_results.iterrows():
        print(f"  - {row['series_code']}: {row['name']}")
    
    # Fetch data for each series found
    fetched_data = {}
    
    for _, series in search_results.iterrows():
        series_code = series['series_code']
        series_name = series['name']
        
        try:
            print(f"\nFetching {series_code}...", end=" ")
            df = bojdata.read_boj(
                series=series_code,
                start_date=start_date,
                end_date=end_date
            )
            fetched_data[series_name] = df
            print(f"✓ Success ({len(df)} observations)")
        except Exception as e:
            print(f"✗ Failed: {str(e)}")
    
    return fetched_data


def compare_series(data_dict):
    """
    Compare multiple series and show correlations
    
    Parameters:
    -----------
    data_dict : dict
        Dictionary of DataFrames to compare
    
    Returns:
    --------
    pd.DataFrame
        Combined DataFrame with all series
    """
    if not data_dict:
        print("No data to compare")
        return None
    
    print("\nComparing series...")
    print("-" * 60)
    
    # Combine all series into one DataFrame
    combined_df = None
    
    for name, df in data_dict.items():
        if combined_df is None:
            combined_df = df.copy()
            combined_df.columns = [name]
        else:
            # Join on date index
            temp_df = df.copy()
            temp_df.columns = [name]
            combined_df = combined_df.join(temp_df, how='outer')
    
    # Show summary statistics
    print("\nSummary Statistics:")
    print(combined_df.describe())
    
    # Calculate correlations if more than one series
    if combined_df.shape[1] > 1:
        print("\nCorrelation Matrix:")
        corr_matrix = combined_df.corr()
        print(corr_matrix)
    
    # Calculate growth rates
    print("\nGrowth Rates (%):")
    for col in combined_df.columns:
        if len(combined_df[col].dropna()) > 0:
            start_val = combined_df[col].dropna().iloc[-1]
            end_val = combined_df[col].dropna().iloc[0]
            growth = ((end_val - start_val) / start_val) * 100
            print(f"  {col}: {growth:.2f}%")
    
    return combined_df


def create_analysis_report(combined_df, output_prefix="boj_analysis"):
    """
    Create a comprehensive analysis report
    
    Parameters:
    -----------
    combined_df : pd.DataFrame
        Combined data for all series
    output_prefix : str
        Prefix for output files
    """
    print("\nCreating analysis report...")
    print("-" * 60)
    
    # Export combined data
    csv_file = f"{output_prefix}_combined_data.csv"
    combined_df.to_csv(csv_file)
    print(f"✓ Data exported to: {csv_file}")
    
    # Create text report
    report_file = f"{output_prefix}_report.txt"
    with open(report_file, 'w') as f:
        f.write("BOJ Data Analysis Report\n")
        f.write("="*50 + "\n\n")
        
        f.write(f"Period: {combined_df.index[-1].date()} to {combined_df.index[0].date()}\n")
        f.write(f"Total observations: {len(combined_df)}\n")
        f.write(f"Series analyzed: {', '.join(combined_df.columns)}\n\n")
        
        f.write("Summary Statistics:\n")
        f.write("-"*30 + "\n")
        f.write(combined_df.describe().to_string())
        f.write("\n\n")
        
        if combined_df.shape[1] > 1:
            f.write("Correlation Matrix:\n")
            f.write("-"*30 + "\n")
            f.write(combined_df.corr().to_string())
            f.write("\n\n")
        
        f.write("Monthly Changes (%):\n")
        f.write("-"*30 + "\n")
        monthly_changes = combined_df.pct_change() * 100
        f.write(monthly_changes.describe().to_string())
        
    print(f"✓ Report exported to: {report_file}")
    
    return csv_file, report_file


def main():
    """Main function demonstrating multiple series fetching"""
    
    print("🏛️  BOJ Multi-Series Data Fetcher")
    print("="*60)
    
    # Define analysis period - last 2 years
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)
    
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    
    # Method 1: Fetch specific known indicators
    print(f"\n1. Fetching specific indicators for {start_str} to {end_str}")
    specific_data = fetch_economic_indicators(start_str, end_str)
    
    # Method 2: Search and fetch
    print(f"\n2. Searching and fetching interest rate data")
    interest_data = search_and_fetch_series("interest", start_str, end_str, limit=2)
    
    # Combine all data
    all_data = {**specific_data, **interest_data}
    
    if all_data:
        # Compare series
        combined_df = compare_series(all_data)
        
        # Create report
        if combined_df is not None:
            csv_file, report_file = create_analysis_report(combined_df)
            
            print("\n✅ Analysis complete!")
            print("\nNext steps:")
            print("1. View the combined data:")
            print(f"   df = pd.read_csv('{csv_file}', index_col=0, parse_dates=True)")
            print("2. Read the analysis report:")
            print(f"   with open('{report_file}') as f: print(f.read())")
            print("3. Create visualizations with matplotlib/seaborn/plotly")
            print("4. Perform time series analysis with statsmodels")
            
            return combined_df
    else:
        print("\n❌ No data was successfully fetched")
        return None


if __name__ == "__main__":
    # Run the analysis
    result = main()
    
    # Optional: Show a preview of the data
    if result is not None:
        print("\n📊 Data Preview:")
        print("-" * 60)
        print(result.head())
        print(f"\nShape: {result.shape}")
        print(f"Date range: {result.index[0]} to {result.index[-1]}")