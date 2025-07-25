"""
Comprehensive usage examples for accessing ALL BOJ data
"""

import bojdata
from bojdata import BOJBulkDownloader, BOJComprehensiveSearch


def example_bulk_download_all():
    """Download ALL available BOJ data"""
    print("Example: Bulk Download All BOJ Data")
    print("-" * 50)
    
    # Initialize bulk downloader
    downloader = BOJBulkDownloader(data_dir="./boj_data_complete")
    
    # Download all flat files
    print("Downloading all flat files...")
    downloaded_files = downloader.download_all_flat_files()
    
    print(f"\nDownloaded {len(downloaded_files)} files:")
    for file_type, path in downloaded_files.items():
        print(f"  - {file_type}: {path}")
    
    # Process all downloaded files
    print("\nProcessing downloaded files...")
    processed_data = downloader.extract_and_process_all()
    
    print(f"\nProcessed {len(processed_data)} datasets:")
    for file_type, df in processed_data.items():
        print(f"  - {file_type}: {len(df)} records")
    
    # Build unified database
    print("\nBuilding unified database...")
    db_path = downloader.build_unified_database(output_format="parquet")
    print(f"Unified database created: {db_path}")


def example_comprehensive_search():
    """Search across ALL BOJ data categories"""
    print("\nExample: Comprehensive Search")
    print("-" * 50)
    
    searcher = BOJComprehensiveSearch()
    
    # Search across all categories
    print("Searching for 'interest rate' across all categories...")
    results = searcher.search_all_categories("interest rate", limit=20)
    
    print(f"\nFound {len(results)} results:")
    print(results[["series_code", "name", "category"]].head(10))
    
    # Search in specific category
    print("\n\nSearching for 'overnight' in Financial Markets...")
    results = searcher.search_all_categories(
        "overnight", 
        categories=["financial_markets"],
        limit=10
    )
    print(results)


def example_discover_all_series():
    """Discover ALL available series codes"""
    print("\nExample: Discover All Series Codes")
    print("-" * 50)
    
    searcher = BOJComprehensiveSearch()
    
    # Get category tree
    print("Getting complete category structure...")
    category_tree = searcher.get_category_tree()
    
    print("\nBOJ Data Categories:")
    for key, info in category_tree.items():
        print(f"\n{info['name']}:")
        for subcat in info['subcategories']:
            print(f"  - {subcat['name']}")
    
    # Build complete series catalog
    print("\n\nBuilding complete series catalog...")
    catalog = searcher.build_series_catalog(save_path="boj_complete_catalog.csv")
    
    print(f"\nCatalog contains {len(catalog)} unique series codes")
    print("\nSample entries:")
    print(catalog.head(10))


def example_category_specific_download():
    """Download all data from specific categories"""
    print("\nExample: Category-Specific Download")
    print("-" * 50)
    
    # Categories to download
    categories = {
        "monetary_base": ["BS01'MABJMTA", "BS01'MABJ_MABJ", "BS01'MABJNA"],
        "interest_rates": ["IR01", "IR02", "IR03", "IR04"],
        "exchange_rates": ["FM01", "FM02", "FM03"],
        "prices": ["PR01'IUQCP001", "PR02'CGPIQ001", "PR03'SPPI001"],
    }
    
    all_data = {}
    
    for category, series_list in categories.items():
        print(f"\nDownloading {category} data...")
        
        try:
            # Download multiple series at once
            df = bojdata.read_boj(series=series_list)
            all_data[category] = df
            print(f"  Downloaded {len(df)} observations for {len(df.columns)} series")
        except Exception as e:
            print(f"  Error: {e}")
    
    return all_data


def example_advanced_data_pipeline():
    """Build an advanced data pipeline for BOJ data"""
    print("\nExample: Advanced Data Pipeline")
    print("-" * 50)
    
    # Step 1: Initialize components
    downloader = BOJBulkDownloader(data_dir="./boj_pipeline")
    searcher = BOJComprehensiveSearch()
    
    # Step 2: Discover available data
    print("Step 1: Discovering available data...")
    catalog = searcher.discover_all_series_codes()
    print(f"  Found {len(catalog)} series codes")
    
    # Step 3: Download flat files
    print("\nStep 2: Downloading flat files...")
    flat_files = downloader.download_all_flat_files()
    print(f"  Downloaded {len(flat_files)} files")
    
    # Step 4: Download specific high-frequency series
    print("\nStep 3: Downloading high-frequency series...")
    high_freq_series = [
        "IR01",  # Overnight call rate
        "FM01",  # USD/JPY exchange rate
        "BS01'MABJMTA",  # Monetary base
    ]
    
    for series in high_freq_series:
        try:
            df = bojdata.read_boj(series=series)
            # Save to pipeline directory
            df.to_parquet(f"./boj_pipeline/high_freq/{series}.parquet")
            print(f"  Saved {series}: {len(df)} observations")
        except Exception as e:
            print(f"  Error with {series}: {e}")
    
    # Step 5: Build unified database
    print("\nStep 4: Building unified database...")
    db_path = downloader.build_unified_database(output_format="sqlite")
    print(f"  Database created: {db_path}")
    
    print("\nPipeline complete!")


def example_using_cli():
    """Examples of using the command-line interface"""
    print("\nExample: Command-Line Interface Usage")
    print("-" * 50)
    
    print("The bojdata package includes a CLI for easy access:")
    print()
    print("# Download specific series:")
    print("$ bojdata download IR01 FM01 --output ./data --format parquet")
    print()
    print("# Bulk download all data:")
    print("$ bojdata bulk --data-dir ./boj_data --build-db --db-format sqlite")
    print()
    print("# Search for series:")
    print("$ bojdata search 'exchange rate' --limit 20 --output results.csv")
    print()
    print("# Build complete catalog:")
    print("$ bojdata catalog --output boj_all_series.csv")


if __name__ == "__main__":
    print("BOJ Data - Comprehensive Usage Examples")
    print("=" * 60)
    print()
    
    # Note: These examples would actually download/process data
    # Uncomment the ones you want to run
    
    # example_bulk_download_all()
    example_comprehensive_search()
    example_discover_all_series()
    # example_category_specific_download()
    # example_advanced_data_pipeline()
    example_using_cli()
    
    print("\n\nFor production use, consider:")
    print("- Setting up scheduled downloads (cron/Task Scheduler)")
    print("- Implementing incremental updates")
    print("- Adding data validation and quality checks")
    print("- Building a REST API on top of the local database")
    print("- Implementing caching for frequently accessed data")