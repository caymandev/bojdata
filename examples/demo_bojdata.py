#!/usr/bin/env python3
"""
Demonstration script showing bojdata capabilities
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bojdata
from bojdata import BOJBulkDownloader, BOJComprehensiveSearch
import pandas as pd


def demo_header(title):
    """Print a nice demo header"""
    print(f"\n{'='*70}")
    print(f" {title}")
    print(f"{'='*70}\n")


def demo_single_series():
    """Demonstrate downloading a single series"""
    demo_header("DEMO 1: Download Single Series - Monetary Base")
    
    print("Downloading Bank of Japan Monetary Base (BS01'MABJMTA)...")
    
    try:
        # Download monetary base data
        df = bojdata.read_boj(series="BS01'MABJMTA")
        
        print(f"\n✓ Successfully downloaded {len(df)} monthly observations")
        print(f"✓ Date range: {df.index.min().strftime('%Y-%m')} to {df.index.max().strftime('%Y-%m')}")
        
        # Show recent data
        print("\nRecent Monetary Base Data (in million yen):")
        print("-" * 40)
        recent_data = df.head(5)
        for date, value in recent_data.iterrows():
            print(f"{date.strftime('%Y-%m')}: ¥{value.iloc[0]:,.0f} million")
        
        # Calculate growth
        yoy_change = (df.iloc[0] - df.iloc[12]) / df.iloc[12] * 100
        print(f"\nYear-over-year change: {yoy_change.iloc[0]:.1f}%")
        
    except Exception as e:
        print(f"Error: {e}")


def demo_bulk_downloader_structure():
    """Demonstrate the bulk downloader structure"""
    demo_header("DEMO 2: Bulk Download Capabilities")
    
    print("The BOJBulkDownloader can download ALL available BOJ data:\n")
    
    downloader = BOJBulkDownloader("./demo_boj_data")
    
    print("Available bulk data files:")
    print("-" * 50)
    for file_type, info in downloader.FLAT_FILES.items():
        print(f"\n{file_type.upper()}:")
        print(f"  File: {info['filename']}")
        print(f"  Description: {info['description']}")
        print(f"  Frequency: {info['frequency']}")
    
    print("\n\nTo download all data, you would run:")
    print(">>> downloader.download_all_flat_files()")
    print(">>> downloader.extract_and_process_all()")
    print(">>> downloader.build_unified_database()")
    
    # Clean up
    import shutil
    if os.path.exists("./demo_boj_data"):
        shutil.rmtree("./demo_boj_data")


def demo_comprehensive_search():
    """Demonstrate comprehensive search capabilities"""
    demo_header("DEMO 3: Comprehensive Search Across All Categories")
    
    searcher = BOJComprehensiveSearch()
    
    print("BOJ Data Categories Available for Search:")
    print("-" * 50)
    
    categories = searcher.get_category_tree()
    for i, (key, info) in enumerate(categories.items(), 1):
        print(f"{i:2d}. {info['name']}")
        if i == 5:  # Show first 5
            print(f"    ... and {len(categories)-5} more categories\n")
            break
    
    print("The comprehensive search can:")
    print("✓ Search across all 13 major categories")
    print("✓ Discover series codes automatically")
    print("✓ Build a complete catalog of all BOJ data")
    print("✓ Navigate subcategories and hierarchies")


def demo_cli_usage():
    """Demonstrate CLI usage"""
    demo_header("DEMO 4: Command-Line Interface")
    
    print("bojdata includes a powerful CLI for easy access:\n")
    
    cli_examples = [
        ("Download specific series", "bojdata download IR01 FM01 --output ./data"),
        ("Search for data", "bojdata search 'inflation' --limit 50"),
        ("Bulk download everything", "bojdata bulk --build-db --db-format sqlite"),
        ("Build series catalog", "bojdata catalog --output all_series.csv"),
    ]
    
    for desc, cmd in cli_examples:
        print(f"{desc}:")
        print(f"  $ {cmd}\n")


def demo_data_coverage():
    """Show the comprehensive data coverage"""
    demo_header("DEMO 5: Complete Data Coverage")
    
    print("bojdata provides access to ALL Bank of Japan statistics:\n")
    
    categories = [
        "1. Interest Rates (deposit rates, loan rates, spreads)",
        "2. Financial Markets (stocks, bonds, forex, derivatives)",
        "3. Payment & Settlement (BOJ-NET, electronic payments)",
        "4. Money & Deposits (M1, M2, M3, monetary base)",
        "5. Loans (by sector, growth rates, NPLs)",
        "6. Balance Sheets (BOJ, banks, financial institutions)",
        "7. Flow of Funds (sectoral accounts, transactions)",
        "8. Other BOJ Statistics (research, surveys, historical)",
        "9. TANKAN Business Survey (confidence, outlook)",
        "10. Prices (CPI, PPI, CGPI, service prices)",
        "11. Public Finance (debt, fiscal balance, bonds)",
        "12. Balance of Payments (current/financial accounts)",
        "13. Miscellaneous (regional stats, special indicators)",
    ]
    
    print("Complete coverage of:")
    for cat in categories[:7]:
        print(f"  {cat}")
    print(f"  ... and {len(categories)-7} more categories")
    
    print("\nTotal accessible data:")
    print("  ✓ Thousands of individual time series")
    print("  ✓ Historical data going back decades")
    print("  ✓ Multiple frequencies (daily, monthly, quarterly)")
    print("  ✓ Regular updates (3x daily for key series)")


def demo_practical_example():
    """Show a practical example"""
    demo_header("DEMO 6: Practical Example - Economic Dashboard")
    
    print("Example: Building a Japan Economic Dashboard\n")
    
    # Define key indicators
    indicators = {
        "Monetary Base": "BS01'MABJMTA",
        "Overnight Call Rate": "IR01",
        "USD/JPY Exchange Rate": "FM01",
        "Consumer Price Index": "PR01'IUQCP001",
    }
    
    print("Key Economic Indicators:")
    print("-" * 50)
    
    # Try to download one as example
    try:
        mb_data = bojdata.read_boj(series="BS01'MABJMTA")
        latest = mb_data.iloc[0]
        print(f"\nMonetary Base (latest): ¥{latest.iloc[0]:,.0f} million")
        print(f"As of: {mb_data.index[0].strftime('%Y-%m')}")
    except:
        pass
    
    print("\nWith bojdata, you can easily:")
    print("✓ Download all these indicators with one command")
    print("✓ Update them automatically on a schedule")
    print("✓ Build visualizations and dashboards")
    print("✓ Analyze relationships between variables")
    print("✓ Export to any format (CSV, Excel, SQL database)")


def main():
    """Run all demos"""
    print("\n" + "="*70)
    print(" BOJDATA - Bank of Japan Data Access Package")
    print(" Version: " + bojdata.__version__)
    print("="*70)
    
    demos = [
        demo_single_series,
        demo_bulk_downloader_structure,
        demo_comprehensive_search,
        demo_cli_usage,
        demo_data_coverage,
        demo_practical_example,
    ]
    
    for demo in demos:
        try:
            demo()
        except Exception as e:
            print(f"\nError in demo: {e}")
    
    print("\n" + "="*70)
    print(" Demo Complete!")
    print("="*70)
    print("\nTo get started with bojdata:")
    print("1. pip install bojdata")
    print("2. import bojdata")
    print("3. df = bojdata.read_boj(series='YOUR_SERIES_CODE')")
    print("\nFor complete documentation, see the README.md file.")


if __name__ == "__main__":
    main()