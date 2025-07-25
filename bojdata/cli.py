"""
Command-line interface for bojdata
"""

import argparse
import json
from pathlib import Path

from .bulk_downloader import BOJBulkDownloader
from .comprehensive_search import BOJComprehensiveSearch
from .core import read_boj


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="BOJData - Access all Bank of Japan statistical data"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Download command
    download_parser = subparsers.add_parser(
        "download", help="Download BOJ data"
    )
    download_parser.add_argument(
        "series", nargs="*", help="Series codes to download (if empty, downloads all flat files)"
    )
    download_parser.add_argument(
        "--output", "-o", help="Output directory", default="./boj_data"
    )
    download_parser.add_argument(
        "--format", "-f", choices=["csv", "parquet", "excel"], 
        default="csv", help="Output format"
    )
    
    # Bulk download command
    bulk_parser = subparsers.add_parser(
        "bulk", help="Bulk download all available data"
    )
    bulk_parser.add_argument(
        "--data-dir", "-d", help="Data directory", default="./boj_data"
    )
    bulk_parser.add_argument(
        "--build-db", action="store_true", 
        help="Build unified database after download"
    )
    bulk_parser.add_argument(
        "--db-format", choices=["parquet", "sqlite"], 
        default="parquet", help="Database format"
    )
    
    # Search command
    search_parser = subparsers.add_parser(
        "search", help="Search for data series"
    )
    search_parser.add_argument(
        "keyword", help="Search keyword"
    )
    search_parser.add_argument(
        "--category", "-c", help="Limit search to specific category"
    )
    search_parser.add_argument(
        "--limit", "-l", type=int, default=50, help="Maximum results"
    )
    search_parser.add_argument(
        "--output", "-o", help="Save results to file"
    )
    
    # Catalog command
    catalog_parser = subparsers.add_parser(
        "catalog", help="Build complete series catalog"
    )
    catalog_parser.add_argument(
        "--output", "-o", help="Output file path", 
        default="boj_series_catalog.csv"
    )
    
    args = parser.parse_args()
    
    if args.command == "download":
        if args.series:
            # Download specific series
            for series in args.series:
                print(f"Downloading {series}...")
                try:
                    df = read_boj(series=series)
                    
                    # Save to file
                    output_path = Path(args.output) / f"{series.replace('/', '_')}"
                    if args.format == "csv":
                        df.to_csv(f"{output_path}.csv")
                    elif args.format == "parquet":
                        df.to_parquet(f"{output_path}.parquet")
                    elif args.format == "excel":
                        df.to_excel(f"{output_path}.xlsx")
                    
                    print(f"Saved to {output_path}.{args.format}")
                except Exception as e:
                    print(f"Error downloading {series}: {e}")
        else:
            # Download all flat files
            print("Downloading all flat files...")
            downloader = BOJBulkDownloader(args.output)
            downloader.download_all_flat_files()
    
    elif args.command == "bulk":
        print("Starting bulk download...")
        downloader = BOJBulkDownloader(args.data_dir)
        
        # Download all flat files
        downloaded = downloader.download_all_flat_files()
        print(f"Downloaded {len(downloaded)} files")
        
        # Process all files
        processed = downloader.extract_and_process_all()
        print(f"Processed {len(processed)} datasets")
        
        # Build unified database if requested
        if args.build_db:
            print(f"Building unified {args.db_format} database...")
            db_path = downloader.build_unified_database(args.db_format)
            print(f"Database created: {db_path}")
    
    elif args.command == "search":
        searcher = BOJComprehensiveSearch()
        
        if args.category:
            results = searcher.search_all_categories(
                args.keyword, categories=[args.category], limit=args.limit
            )
        else:
            results = searcher.search_all_categories(
                args.keyword, limit=args.limit
            )
        
        print(f"Found {len(results)} results")
        print(results)
        
        if args.output:
            results.to_csv(args.output, index=False)
            print(f"Results saved to {args.output}")
    
    elif args.command == "catalog":
        print("Building comprehensive series catalog...")
        searcher = BOJComprehensiveSearch()
        catalog = searcher.build_series_catalog(args.output)
        print(f"Catalog with {len(catalog)} series saved to {args.output}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()