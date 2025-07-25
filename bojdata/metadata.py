"""
Series metadata extraction and organization.

This module provides functionality to extract detailed metadata about BOJ
data series including units, descriptions, update frequency, and more.
"""

import re
from typing import Dict, Any, Optional, List
import pandas as pd
import requests
from bs4 import BeautifulSoup

from .exceptions import BOJDataError, SeriesNotFoundError


class SeriesMetadataExtractor:
    """
    Extract and organize metadata for BOJ data series.
    
    This class scrapes detailed information about individual series from
    BOJ's website to provide comprehensive metadata.
    
    Examples
    --------
    >>> from bojdata.metadata import SeriesMetadataExtractor
    >>> extractor = SeriesMetadataExtractor()
    >>> 
    >>> # Get metadata for a series
    >>> meta = extractor.get_series_metadata("BS01'MABJMTA")
    >>> print(meta['description'])
    >>> print(meta['units'])
    """
    
    BASE_URL = "https://www.stat-search.boj.or.jp"
    
    def __init__(self):
        """Initialize the metadata extractor."""
        self._metadata_cache = {}
    
    def get_series_metadata(self, series_id: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get comprehensive metadata for a series.
        
        Parameters
        ----------
        series_id : str
            BOJ series identifier
        force_refresh : bool, default False
            Force refresh of cached metadata
            
        Returns
        -------
        dict
            Metadata including:
            - name: Series name
            - description: Detailed description
            - units: Data units (e.g., "Yen", "Index", "Percent")
            - frequency: Update frequency
            - start_date: First available date
            - end_date: Latest available date
            - last_updated: Last update timestamp
            - category: Data category
            - source: Data source
            - seasonal_adjustment: SA status
            - base_period: Base period for indices
            - notes: Additional notes
            - related_series: List of related series codes
            - tags: Extracted tags from description
            
        Examples
        --------
        >>> extractor = SeriesMetadataExtractor()
        >>> meta = extractor.get_series_metadata("IR01")
        >>> print(f"Units: {meta['units']}")
        >>> print(f"Frequency: {meta['frequency']}")
        """
        # Check cache
        if not force_refresh and series_id in self._metadata_cache:
            return self._metadata_cache[series_id]
        
        # Try to fetch series page
        metadata = self._fetch_series_metadata(series_id)
        
        # Extract tags from description
        metadata['tags'] = self._extract_tags(metadata)
        
        # Cache result
        self._metadata_cache[series_id] = metadata
        
        return metadata
    
    def _fetch_series_metadata(self, series_id: str) -> Dict[str, Any]:
        """Fetch metadata from BOJ website."""
        # Initialize metadata
        metadata = {
            'series_id': series_id,
            'name': series_id,
            'description': '',
            'units': 'Index',
            'frequency': 'Unknown',
            'start_date': None,
            'end_date': None,
            'last_updated': None,
            'category': 'Unknown',
            'source': 'Bank of Japan',
            'seasonal_adjustment': 'Not Seasonally Adjusted',
            'base_period': None,
            'notes': '',
            'related_series': [],
            'tags': []
        }
        
        # Try to get series information from search
        search_url = f"{self.BASE_URL}/ssi/cgi-bin/famecgi2"
        params = {
            'cgi': '$nme_a000_en',
            'hdncode': series_id,
        }
        
        try:
            response = requests.get(search_url, params=params, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract metadata from page
            metadata.update(self._parse_series_page(soup, series_id))
            
        except Exception as e:
            # If direct fetch fails, try to get from comprehensive search
            metadata.update(self._get_metadata_from_search(series_id))
        
        return metadata
    
    def _parse_series_page(self, soup: BeautifulSoup, series_id: str) -> Dict[str, Any]:
        """Parse metadata from series page."""
        updates = {}
        
        # Look for series name/title
        title_elements = soup.find_all(['h1', 'h2', 'h3'])
        for elem in title_elements:
            text = elem.get_text().strip()
            if text and series_id not in text:
                updates['name'] = text
                break
        
        # Look for metadata in tables
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label = cells[0].get_text().strip().lower()
                    value = cells[1].get_text().strip()
                    
                    # Map labels to metadata fields
                    if 'unit' in label:
                        updates['units'] = self._standardize_units(value)
                    elif 'frequency' in label or 'period' in label:
                        updates['frequency'] = self._standardize_frequency(value)
                    elif 'description' in label:
                        updates['description'] = value
                    elif 'start' in label and 'date' in label:
                        updates['start_date'] = value
                    elif 'end' in label and 'date' in label:
                        updates['end_date'] = value
                    elif 'update' in label:
                        updates['last_updated'] = value
                    elif 'category' in label:
                        updates['category'] = value
                    elif 'seasonal' in label:
                        updates['seasonal_adjustment'] = value
                    elif 'base' in label:
                        updates['base_period'] = value
                    elif 'note' in label:
                        updates['notes'] = value
        
        # Extract description from paragraphs if not found
        if not updates.get('description'):
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                text = p.get_text().strip()
                if len(text) > 50 and series_id not in text:
                    updates['description'] = text
                    break
        
        # Extract related series
        updates['related_series'] = self._extract_related_series(soup, series_id)
        
        return updates
    
    def _get_metadata_from_search(self, series_id: str) -> Dict[str, Any]:
        """Get metadata from comprehensive search as fallback."""
        updates = {}
        
        # Map known series patterns to metadata
        series_patterns = {
            # Interest rates
            r'^IR\d+': {
                'category': 'Interest Rates',
                'units': 'Percent per annum',
                'frequency': 'Daily'
            },
            # Financial markets
            r'^FM\d+': {
                'category': 'Financial Markets',
                'units': 'Index or Rate',
                'frequency': 'Daily'
            },
            # Money stock
            r'^(MD|MS)\d+': {
                'category': 'Money and Deposits',
                'units': 'Billions of Yen',
                'frequency': 'Monthly'
            },
            # Monetary base
            r"^BS01'": {
                'category': 'Balance Sheets',
                'units': 'Billions of Yen',
                'frequency': 'Monthly',
                'name': 'Monetary Base'
            },
            # Prices
            r'^PR\d+': {
                'category': 'Prices',
                'units': 'Index',
                'frequency': 'Monthly'
            },
            # TANKAN
            r'^TK\d+': {
                'category': 'TANKAN',
                'units': 'Diffusion Index',
                'frequency': 'Quarterly'
            },
            # Balance of Payments
            r'^BP\d+': {
                'category': 'Balance of Payments',
                'units': 'Billions of Yen',
                'frequency': 'Monthly'
            },
            # Flow of Funds
            r'^FF': {
                'category': 'Flow of Funds',
                'units': 'Billions of Yen',
                'frequency': 'Quarterly'
            }
        }
        
        # Match series ID to patterns
        for pattern, metadata in series_patterns.items():
            if re.match(pattern, series_id):
                updates.update(metadata)
                break
        
        return updates
    
    def _standardize_units(self, units_text: str) -> str:
        """Standardize units text."""
        units_lower = units_text.lower()
        
        # Common unit mappings
        unit_map = {
            'yen': 'Yen',
            'billions of yen': 'Billions of Yen',
            'millions of yen': 'Millions of Yen',
            'percent': 'Percent',
            '% per annum': 'Percent per annum',
            'index': 'Index',
            'persons': 'Persons',
            'diffusion index': 'Diffusion Index',
            'di': 'Diffusion Index',
        }
        
        for key, value in unit_map.items():
            if key in units_lower:
                return value
        
        return units_text
    
    def _standardize_frequency(self, freq_text: str) -> str:
        """Standardize frequency text."""
        freq_lower = freq_text.lower()
        
        if 'daily' in freq_lower or 'day' in freq_lower:
            return 'Daily'
        elif 'monthly' in freq_lower or 'month' in freq_lower:
            return 'Monthly'
        elif 'quarterly' in freq_lower or 'quarter' in freq_lower:
            return 'Quarterly'
        elif 'annual' in freq_lower or 'year' in freq_lower:
            return 'Annual'
        elif 'weekly' in freq_lower or 'week' in freq_lower:
            return 'Weekly'
        
        return freq_text
    
    def _extract_related_series(self, soup: BeautifulSoup, current_series: str) -> List[str]:
        """Extract related series codes from page."""
        related = []
        
        # Look for links that might be series codes
        links = soup.find_all('a')
        
        # Common BOJ series patterns
        series_pattern = r'^[A-Z]{2}\d{2}|^[A-Z]{2,4}\d{2}\'|^[A-Z]+_'
        
        for link in links:
            text = link.get_text().strip()
            href = link.get('href', '')
            
            # Check if text looks like a series code
            if re.match(series_pattern, text) and text != current_series:
                related.append(text)
            # Check href for series codes
            elif 'hdncode=' in href:
                match = re.search(r'hdncode=([^&]+)', href)
                if match:
                    code = match.group(1)
                    if code != current_series:
                        related.append(code)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_related = []
        for item in related:
            if item not in seen:
                seen.add(item)
                unique_related.append(item)
        
        return unique_related[:10]  # Limit to 10 related series
    
    def _extract_tags(self, metadata: Dict[str, Any]) -> List[str]:
        """Extract tags from metadata description and name."""
        tags = []
        
        # Combine text sources
        text_sources = [
            metadata.get('name', ''),
            metadata.get('description', ''),
            metadata.get('category', '')
        ]
        
        combined_text = ' '.join(text_sources).lower()
        
        # Keywords to look for
        tag_keywords = {
            # Economic indicators
            'interest rate': ['interest', 'rate', 'yield'],
            'exchange rate': ['exchange', 'forex', 'fx', 'usd/jpy'],
            'inflation': ['inflation', 'cpi', 'price index', 'deflation'],
            'gdp': ['gdp', 'gross domestic product', 'output'],
            'employment': ['employment', 'unemployment', 'labor', 'jobs'],
            
            # Financial markets
            'stock market': ['stock', 'equity', 'topix', 'nikkei'],
            'bond market': ['bond', 'jgb', 'government bond', 'yield curve'],
            'money market': ['money market', 'call rate', 'repo'],
            
            # Monetary policy
            'monetary base': ['monetary base', 'base money', 'high-powered money'],
            'money supply': ['money supply', 'money stock', 'm1', 'm2', 'm3'],
            'bank lending': ['lending', 'loans', 'credit', 'advances'],
            
            # Sectors
            'banking': ['bank', 'banking', 'financial institution'],
            'corporate': ['corporate', 'business', 'company', 'firm'],
            'household': ['household', 'consumer', 'personal'],
            'government': ['government', 'public', 'fiscal'],
            
            # Data characteristics
            'seasonally adjusted': ['seasonally adjusted', 'sa', 's.a.'],
            'real': ['real', 'inflation adjusted', 'constant price'],
            'nominal': ['nominal', 'current price'],
            
            # Frequency
            'high frequency': ['daily', 'weekly', 'high frequency'],
            'survey': ['survey', 'tankan', 'opinion', 'sentiment']
        }
        
        # Extract tags based on keywords
        for tag, keywords in tag_keywords.items():
            for keyword in keywords:
                if keyword in combined_text:
                    tags.append(tag)
                    break
        
        # Add category as tag
        category = metadata.get('category', '')
        if category and category != 'Unknown':
            tags.append(category.lower())
        
        # Add frequency as tag
        freq = metadata.get('frequency', '')
        if freq and freq != 'Unknown':
            tags.append(freq.lower())
        
        # Remove duplicates and return
        return list(set(tags))
    
    def get_series_by_tag(self, tag: str, all_series: List[str]) -> List[str]:
        """
        Find series that match a specific tag.
        
        Parameters
        ----------
        tag : str
            Tag to search for
        all_series : List[str]
            List of series codes to search
            
        Returns
        -------
        List[str]
            Series codes matching the tag
        """
        matching_series = []
        
        for series_id in all_series:
            try:
                metadata = self.get_series_metadata(series_id)
                if tag.lower() in [t.lower() for t in metadata.get('tags', [])]:
                    matching_series.append(series_id)
            except:
                continue
        
        return matching_series
    
    def build_metadata_database(self, series_list: List[str]) -> pd.DataFrame:
        """
        Build a database of metadata for multiple series.
        
        Parameters
        ----------
        series_list : List[str]
            List of series codes
            
        Returns
        -------
        pd.DataFrame
            DataFrame with metadata for all series
        """
        metadata_records = []
        
        for i, series_id in enumerate(series_list):
            if i % 10 == 0:
                print(f"Processing {i}/{len(series_list)} series...", end='\r')
            
            try:
                metadata = self.get_series_metadata(series_id)
                metadata_records.append(metadata)
            except Exception as e:
                print(f"\nError processing {series_id}: {e}")
                continue
        
        print(f"\nCompleted: {len(metadata_records)} series processed")
        
        return pd.DataFrame(metadata_records)


# Convenience function
def get_series_metadata(series_id: str) -> Dict[str, Any]:
    """
    Get metadata for a BOJ series.
    
    Parameters
    ----------
    series_id : str
        BOJ series identifier
        
    Returns
    -------
    dict
        Series metadata
    """
    extractor = SeriesMetadataExtractor()
    return extractor.get_series_metadata(series_id)