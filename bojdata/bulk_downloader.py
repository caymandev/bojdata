"""
Bulk download functionality for all BOJ data
"""

import json
import os
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from .exceptions import BOJDataError
from .utils import list_valid_series_codes
from .utils import clean_data_frame


class BOJBulkDownloader:
    """Download and manage all available BOJ statistical data"""
    
    BASE_URL = "https://www.stat-search.boj.or.jp"
    FLAT_FILES_URL = "https://www.stat-search.boj.or.jp/info/dload_en.html"
    
    # Available flat file downloads
    FLAT_FILES = {
        "prices": {
            "filename": "prices_m_en.zip",
            "description": "Price indices (CPI, PPI, CGPI, SPPI)",
            "frequency": "monthly",
        },
        "flow_of_funds": {
            "filename": "fof_q_en.zip", 
            "description": "Flow of funds accounts",
            "frequency": "quarterly",
        },
        "tankan": {
            "filename": "tankan_q_en.zip",
            "description": "TANKAN business survey",
            "frequency": "quarterly",
        },
        "balance_of_payments": {
            "filename": "bp_m_en.zip",
            "description": "Balance of payments",
            "frequency": "monthly",
        },
        "bis_statistics": {
            "filename": "bis_q_en.zip",
            "description": "BIS-related statistics",
            "frequency": "quarterly",
        },
    }
    
    def __init__(self, data_dir: Optional[Union[str, Path]] = None):
        """
        Initialize BOJ bulk downloader.
        
        Parameters
        ----------
        data_dir : str or Path, optional
            Directory to store downloaded data. Defaults to ./boj_data
        """
        self.data_dir = Path(data_dir or "./boj_data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.metadata_dir = self.data_dir / "metadata"
        
        for dir in [self.raw_dir, self.processed_dir, self.metadata_dir]:
            dir.mkdir(exist_ok=True)
    
    def download_all_flat_files(self, force: bool = False, show_progress: bool = True) -> Dict[str, Path]:
        """
        Download all available flat files from BOJ.
        
        Parameters
        ----------
        force : bool, default False
            Force re-download even if files exist
        show_progress : bool, default True
            Show progress bar during downloads
        
        Returns
        -------
        dict
            Dictionary mapping file types to downloaded file paths
        """
        downloaded = {}
        failed = []
        
        file_items = list(self.FLAT_FILES.items())
        if show_progress:
            file_items = tqdm(file_items, desc="Downloading BOJ flat files")
        
        for file_type, info in file_items:
            try:
                path = self.download_flat_file(file_type, force=force, show_progress=show_progress)
                downloaded[file_type] = path
                if not show_progress:
                    print(f"✓ Downloaded {file_type}: {path}")
            except Exception as e:
                failed.append((file_type, str(e)))
                if not show_progress:
                    print(f"✗ Failed to download {file_type}: {e}")
        
        if failed:
            print(f"\nFailed downloads: {len(failed)}/{len(self.FLAT_FILES)}")
            for file_type, error in failed:
                print(f"  - {file_type}: {error}")
        
        return downloaded
    
    def download_flat_file(self, file_type: str, force: bool = False, show_progress: bool = True) -> Path:
        """
        Download a specific flat file.
        
        Parameters
        ----------
        file_type : str
            Type of file to download (e.g., 'prices', 'tankan')
        force : bool, default False
            Force re-download even if file exists
        
        Returns
        -------
        Path
            Path to downloaded file
        """
        if file_type not in self.FLAT_FILES:
            raise BOJDataError(f"Unknown file type: {file_type}")
        
        info = self.FLAT_FILES[file_type]
        filename = info["filename"]
        
        # Check if file already exists
        file_path = self.raw_dir / filename
        if file_path.exists() and not force:
            print(f"{filename} already exists, skipping download")
            return file_path
        
        # Get download URL
        download_url = self._get_flat_file_url(filename)
        
        # Download file with progress bar
        if not show_progress:
            print(f"Downloading {filename}...")
        
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        
        # Get file size if available
        total_size = int(response.headers.get('content-length', 0))
        
        # Save file with progress
        with open(file_path, "wb") as f:
            if show_progress and total_size > 0:
                with tqdm(total=total_size, unit='B', unit_scale=True, desc=filename) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
            else:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        
        return file_path
    
    def _get_flat_file_url(self, filename: str) -> str:
        """Get direct download URL for a flat file"""
        # Parse the flat files page to get current URLs
        response = requests.get(self.FLAT_FILES_URL)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Find link for the specific file
        for link in soup.find_all("a", href=True):
            if filename in link["href"]:
                return urljoin(self.BASE_URL, link["href"])
        
        # If not found on main page, try direct URL pattern
        return f"{self.BASE_URL}/info/{filename}"
    
    def extract_and_process_all(self) -> Dict[str, pd.DataFrame]:
        """
        Extract and process all downloaded flat files.
        
        Returns
        -------
        dict
            Dictionary mapping file types to processed DataFrames
        """
        processed = {}
        
        for file_type in self.FLAT_FILES:
            try:
                df = self.extract_and_process(file_type)
                processed[file_type] = df
                print(f"Processed {file_type}: {len(df)} records")
            except Exception as e:
                print(f"Failed to process {file_type}: {e}")
        
        return processed
    
    def extract_and_process(self, file_type: str) -> pd.DataFrame:
        """
        Extract and process a specific flat file.
        
        Parameters
        ----------
        file_type : str
            Type of file to process
        
        Returns
        -------
        pd.DataFrame
            Processed data
        """
        info = self.FLAT_FILES[file_type]
        zip_path = self.raw_dir / info["filename"]
        
        if not zip_path.exists():
            raise BOJDataError(f"File not found: {zip_path}. Run download_flat_file first.")
        
        # Extract ZIP file
        extract_dir = self.raw_dir / file_type
        extract_dir.mkdir(exist_ok=True)
        
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # Process extracted files
        all_data = []
        
        for file_path in extract_dir.glob("*.csv"):
            try:
                df = self._process_csv_file(file_path, file_type)
                if df is not None and not df.empty:
                    all_data.append(df)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
        
        # Combine all data
        if all_data:
            combined_df = pd.concat(all_data, axis=0, ignore_index=True)
            
            # Save processed data
            output_path = self.processed_dir / f"{file_type}_processed.parquet"
            combined_df.to_parquet(output_path)
            
            return combined_df
        else:
            return pd.DataFrame()
    
    def _process_csv_file(self, file_path: Path, file_type: str) -> Optional[pd.DataFrame]:
        """Process a single CSV file from BOJ"""
        try:
            # Read with different encodings
            for encoding in ["utf-8", "shift_jis", "cp932"]:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise BOJDataError(f"Could not decode {file_path}")
            
            # Add metadata
            df["source_file"] = file_path.name
            df["file_type"] = file_type
            df["download_date"] = datetime.now()
            
            return df
            
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return None
    
    def get_all_available_series(self) -> pd.DataFrame:
        """
        Get a comprehensive list of all available BOJ data series.
        
        Returns
        -------
        pd.DataFrame
            DataFrame with series codes, names, categories, and metadata
        """
        # For now, return our known valid series codes
        # In the future, this could be enhanced to scrape the BOJ website
        # or use a more comprehensive API
        return list_valid_series_codes()
    
    def _get_all_categories(self) -> List[Dict]:
        """Get all data categories from BOJ website"""
        url = f"{self.BASE_URL}/index_en.html"
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        categories = []
        
        # Find category links
        for section in soup.find_all("div", class_="category"):
            category_name = section.find("h3").text.strip()
            category_id = len(categories) + 1
            
            categories.append({
                "id": category_id,
                "name": category_name,
                "url": url,
            })
        
        return categories
    
    def _get_series_in_category(self, category: Dict) -> List[Dict]:
        """Get all series within a category"""
        # This would parse the category page to extract series
        # Placeholder implementation
        return []
    
    def build_unified_database(self, output_format: str = "parquet") -> Path:
        """
        Build a unified database of all BOJ data.
        
        Parameters
        ----------
        output_format : str, default "parquet"
            Output format: "parquet", "sqlite", or "csv"
        
        Returns
        -------
        Path
            Path to unified database file
        """
        print("Building unified BOJ database...")
        
        # Download all flat files
        self.download_all_flat_files()
        
        # Process all files
        processed_data = self.extract_and_process_all()
        
        # Get series metadata
        series_metadata = self.get_all_available_series()
        
        # Create unified structure
        if output_format == "parquet":
            output_path = self.data_dir / "boj_unified_database.parquet"
            # Combine all data with metadata
            # This is a simplified version - real implementation would be more sophisticated
            all_data = []
            for file_type, df in processed_data.items():
                df["category"] = file_type
                all_data.append(df)
            
            if all_data:
                unified_df = pd.concat(all_data, axis=0, ignore_index=True)
                unified_df.to_parquet(output_path)
            
        elif output_format == "sqlite":
            import sqlite3
            output_path = self.data_dir / "boj_unified_database.db"
            conn = sqlite3.connect(output_path)
            
            # Store each dataset as a table
            for file_type, df in processed_data.items():
                df.to_sql(file_type, conn, if_exists="replace", index=False)
            
            # Store metadata
            series_metadata.to_sql("series_metadata", conn, if_exists="replace", index=False)
            
            conn.close()
        
        else:
            raise ValueError(f"Unsupported format: {output_format}")
        
        print(f"Unified database created: {output_path}")
        return output_path