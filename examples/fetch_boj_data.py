#!/usr/bin/env python3
"""
Practical example: Fetch BOJ data for a specific time period and analyze it
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime
import bojdata


def fetch_monetary_base_data(start_date, end_date):
    """
    Fetch Bank of Japan Monetary Base data for a specific period
    
    Parameters:
    -----------
    start_date : str
        Start date in format 'YYYY-MM-DD'
    end_date : str
        End date in format 'YYYY-MM-DD'
    
    Returns:
    --------
    pd.DataFrame
        Monetary base data for the specified period
    """
    print(f"Fetching BOJ Monetary Base data from {start_date} to {end_date}...")
    
    # Use bojdata to fetch the data
    df = bojdata.read_boj(
        series="BS01'MABJMTA",  # Monetary Base (Average Amounts Outstanding)
        start_date=start_date,
        end_date=end_date
    )
    
    print(f"✓ Successfully fetched {len(df)} months of data")
    return df


def analyze_monetary_base(df):
    """
    Perform analysis on the monetary base data
    
    Parameters:
    -----------
    df : pd.DataFrame
        Monetary base data
    
    Returns:
    --------
    dict
        Analysis results
    """
    print("\nAnalyzing monetary base data...")
    
    # Convert to billions for easier reading
    df_billions = df / 1000
    
    # Calculate statistics
    analysis = {
        'period_start': df.index[0].strftime('%Y-%m-%d'),
        'period_end': df.index[-1].strftime('%Y-%m-%d'),
        'months_of_data': len(df),
        'latest_value': df.iloc[0, 0],
        'oldest_value': df.iloc[-1, 0],
        'mean_value': df.mean().iloc[0],
        'std_deviation': df.std().iloc[0],
        'min_value': df.min().iloc[0],
        'max_value': df.max().iloc[0],
        'total_change': df.iloc[0, 0] - df.iloc[-1, 0],
        'percent_change': ((df.iloc[0, 0] - df.iloc[-1, 0]) / df.iloc[-1, 0]) * 100
    }
    
    # Calculate monthly changes
    df['Monthly_Change'] = df.iloc[:, 0].diff()
    df['Monthly_Change_Pct'] = df.iloc[:, 0].pct_change() * 100
    
    # Find months with largest changes
    largest_increase = df['Monthly_Change'].min()  # Min because data is sorted descending
    largest_decrease = df['Monthly_Change'].max()  # Max because data is sorted descending
    
    analysis['largest_monthly_increase'] = abs(largest_increase)
    analysis['largest_monthly_decrease'] = abs(largest_decrease)
    
    return analysis, df


def print_analysis_report(analysis, df):
    """Print a formatted analysis report"""
    print("\n" + "="*60)
    print("BANK OF JAPAN MONETARY BASE ANALYSIS REPORT")
    print("="*60)
    
    print(f"\nPeriod: {analysis['period_start']} to {analysis['period_end']}")
    print(f"Total months analyzed: {analysis['months_of_data']}")
    
    print("\n📊 Summary Statistics:")
    print("-" * 40)
    print(f"Latest value (as of {analysis['period_end']}): ¥{analysis['latest_value']:,.0f} million")
    print(f"Starting value: ¥{analysis['oldest_value']:,.0f} million")
    print(f"Average: ¥{analysis['mean_value']:,.0f} million")
    print(f"Standard deviation: ¥{analysis['std_deviation']:,.0f} million")
    print(f"Minimum: ¥{analysis['min_value']:,.0f} million")
    print(f"Maximum: ¥{analysis['max_value']:,.0f} million")
    
    print("\n📈 Growth Analysis:")
    print("-" * 40)
    print(f"Total change: ¥{analysis['total_change']:,.0f} million")
    print(f"Percentage change: {analysis['percent_change']:.2f}%")
    print(f"Largest monthly increase: ¥{analysis['largest_monthly_increase']:,.0f} million")
    print(f"Largest monthly decrease: ¥{analysis['largest_monthly_decrease']:,.0f} million")
    
    print("\n📅 Recent Data (Last 6 Months):")
    print("-" * 40)
    recent_data = df.head(6)
    for date, row in recent_data.iterrows():
        value = row.iloc[0]
        change_pct = row['Monthly_Change_Pct']
        if pd.notna(change_pct):
            print(f"{date.strftime('%Y-%m')}: ¥{value:,.0f} million ({change_pct:+.2f}%)")
        else:
            print(f"{date.strftime('%Y-%m')}: ¥{value:,.0f} million")


def export_results(df, analysis, output_prefix="boj_monetary_base"):
    """Export the data and analysis results"""
    print("\n💾 Exporting results...")
    
    # Export raw data
    csv_filename = f"{output_prefix}_data.csv"
    df.to_csv(csv_filename)
    print(f"✓ Data exported to: {csv_filename}")
    
    # Export analysis summary
    summary_filename = f"{output_prefix}_analysis.txt"
    with open(summary_filename, 'w') as f:
        f.write("BOJ Monetary Base Analysis Summary\n")
        f.write("="*50 + "\n\n")
        for key, value in analysis.items():
            if isinstance(value, float):
                f.write(f"{key}: {value:,.2f}\n")
            else:
                f.write(f"{key}: {value}\n")
    print(f"✓ Analysis exported to: {summary_filename}")
    
    return csv_filename, summary_filename


def main():
    """Main function to demonstrate fetching BOJ data for a specific period"""
    
    # Define the time period we want to analyze
    # Let's analyze the last 3 years of monetary base data
    end_date = "2024-12-31"
    start_date = "2022-01-01"
    
    print("🏛️  Bank of Japan Data Fetcher")
    print("="*60)
    print(f"Fetching monetary base data for: {start_date} to {end_date}")
    
    try:
        # Fetch the data
        df = fetch_monetary_base_data(start_date, end_date)
        
        # Analyze the data
        analysis, df_with_changes = analyze_monetary_base(df)
        
        # Print analysis report
        print_analysis_report(analysis, df_with_changes)
        
        # Export results
        data_file, analysis_file = export_results(df_with_changes, analysis)
        
        print("\n✅ Analysis complete!")
        print(f"\nYou can now:")
        print(f"- Load the data: pd.read_csv('{data_file}')")
        print(f"- View the analysis: open('{analysis_file}').read()")
        print(f"- Create visualizations with the DataFrame")
        print(f"- Perform further analysis with pandas/numpy")
        
        return df_with_changes, analysis
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None, None


if __name__ == "__main__":
    # Run the main function
    df, analysis = main()
    
    # Optional: Create a simple visualization if matplotlib is available
    try:
        import matplotlib.pyplot as plt
        
        print("\n📊 Creating visualization...")
        
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # Plot 1: Monetary Base over time
        ax1.plot(df.index, df.iloc[:, 0] / 1_000_000, 'b-', linewidth=2)
        ax1.set_title('Bank of Japan Monetary Base Over Time')
        ax1.set_ylabel('Trillion Yen')
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Monthly percentage changes
        ax2.bar(df.index[1:], df['Monthly_Change_Pct'].iloc[1:], 
                color=['g' if x > 0 else 'r' for x in df['Monthly_Change_Pct'].iloc[1:]])
        ax2.set_title('Monthly Percentage Changes')
        ax2.set_ylabel('% Change')
        ax2.set_xlabel('Date')
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        
        plt.tight_layout()
        plt.savefig('boj_monetary_base_analysis.png', dpi=300, bbox_inches='tight')
        print("✓ Visualization saved to: boj_monetary_base_analysis.png")
        
        # Show the plot
        # plt.show()  # Uncomment to display
        
    except ImportError:
        print("\n(Install matplotlib to generate visualizations)")