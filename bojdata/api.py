"""
FRED-compatible API wrapper for BOJ data access.

This module provides a wrapper class that matches FRED API patterns,
making it easier for users familiar with FRED to work with BOJ data.
"""

from typing import Optional, Union, List, Dict, Any
import pandas as pd
from datetime import datetime

from .core import read_boj, search_series as core_search_series
from .comprehensive_search import BOJComprehensiveSearch
from .transformations import get_transformation_description
from .exceptions import SeriesNotFoundError, InvalidParameterError
from .batch import read_boj_batch
from .releases import BOJReleaseCalendar
from .metadata import SeriesMetadataExtractor


class BOJDataAPI:
    """
    FRED-compatible API wrapper for Bank of Japan data.
    
    This class provides methods that match FRED API patterns, making it
    easier to migrate from FRED to BOJ data sources. All methods are
    designed to be familiar to FRED users while accessing BOJ data.
    
    Attributes
    ----------
    comprehensive_search : BOJComprehensiveSearch
        Instance for searching across all BOJ categories
    
    Examples
    --------
    >>> from bojdata import BOJDataAPI
    >>> api = BOJDataAPI()
    >>> 
    >>> # Get series metadata (like FRED's fred/series endpoint)
    >>> meta = api.get_series("BS01'MABJMTA")
    >>> print(meta['title'])  # 'Monetary Base (Average Amounts Outstanding)'
    >>> 
    >>> # Get observations with transformations
    >>> data = api.get_observations(
    ...     "BS01'MABJMTA", 
    ...     units='pch',  # Percent change
    ...     start_date='2020-01-01'
    ... )
    >>> 
    >>> # Search for series with pagination
    >>> results = api.search_series(
    ...     "interest rate", 
    ...     limit=10,
    ...     offset=0,
    ...     order_by='relevance'
    ... )
    >>> 
    >>> # Get FRED-style JSON response
    >>> json_data = api.get_observations("IR01", output_type='dict')
    >>> print(json_data['observations'][0])  # {'date': '2023-01-01', 'value': '0.1'}
    
    Notes
    -----
    This wrapper provides stateless access to BOJ data. Unlike FRED,
    no API key is required, but please be respectful of BOJ's servers.
    """
    
    def __init__(self):
        """Initialize the BOJ Data API wrapper."""
        self.comprehensive_search = BOJComprehensiveSearch()
        self.release_calendar = BOJReleaseCalendar()
        self.metadata_extractor = SeriesMetadataExtractor()
    
    def get_series(self, series_id: str, **kwargs) -> Dict[str, Any]:
        """
        Get metadata for a specific series.
        
        Parameters
        ----------
        series_id : str
            BOJ series identifier
        **kwargs : dict
            Additional parameters (for compatibility)
            
        Returns
        -------
        dict
            Series metadata including:
            - id: Series identifier
            - title: Series name/description
            - frequency: Data frequency
            - units: Original units
            - seasonal_adjustment: Whether seasonally adjusted
            - last_updated: Last update date (if available)
            
        Examples
        --------
        >>> api = BOJDataAPI()
        >>> meta = api.get_series("BS01'MABJMTA")
        >>> print(meta['title'])
        """
        # Search for the series to get metadata
        search_results = core_search_series(series_id, limit=1)
        
        if search_results.empty:
            # Try comprehensive search
            comp_results = self.comprehensive_search.search_all_categories(series_id)
            if comp_results.empty:
                raise SeriesNotFoundError(series_id)
            result = comp_results.iloc[0]
        else:
            result = search_results.iloc[0]
        
        # Try to get detailed metadata
        try:
            detailed_meta = self.metadata_extractor.get_series_metadata(series_id)
        except:
            detailed_meta = {}
        
        # Build metadata dictionary matching FRED structure
        metadata = {
            'id': series_id,
            'title': detailed_meta.get('name', result.get('name', series_id)),
            'frequency': detailed_meta.get('frequency', result.get('frequency', 'Unknown')),
            'frequency_short': self._get_frequency_short(
                detailed_meta.get('frequency', result.get('frequency', ''))
            ),
            'units': detailed_meta.get('units', result.get('units', 'Index')),
            'units_short': detailed_meta.get('units', result.get('units', 'Index')),
            'seasonal_adjustment': detailed_meta.get('seasonal_adjustment', 'Not Seasonally Adjusted'),
            'seasonal_adjustment_short': 'SA' if 'seasonal' in detailed_meta.get('seasonal_adjustment', '').lower() else 'NSA',
            'popularity': 50,  # Default popularity score
            'notes': detailed_meta.get('description', f"Bank of Japan series: {series_id}"),
            'realtime_start': datetime.now().strftime('%Y-%m-%d'),
            'realtime_end': datetime.now().strftime('%Y-%m-%d'),
        }
        
        # Add additional metadata if available
        if detailed_meta:
            metadata['observation_start'] = detailed_meta.get('start_date')
            metadata['observation_end'] = detailed_meta.get('end_date')
            metadata['last_updated'] = detailed_meta.get('last_updated')
            metadata['tags'] = detailed_meta.get('tags', [])
            metadata['related_series'] = detailed_meta.get('related_series', [])
        
        # Add category information
        metadata['category'] = detailed_meta.get('category', result.get('category', 'Unknown'))
        
        return metadata
    
    def get_observations(
        self, 
        series_id: str,
        start_date: Optional[Union[str, pd.Timestamp]] = None,
        end_date: Optional[Union[str, pd.Timestamp]] = None,
        units: str = 'lin',
        frequency: Optional[str] = None,
        aggregation_method: str = 'avg',
        output_type: str = 'pandas',
        **kwargs
    ) -> Union[pd.DataFrame, Dict[str, Any]]:
        """
        Get observations (data values) for a series with transformations.
        
        Parameters
        ----------
        series_id : str
            BOJ series identifier
        start_date : str or pd.Timestamp, optional
            Start date for data retrieval
        end_date : str or pd.Timestamp, optional
            End date for data retrieval
        units : str, default 'lin'
            Data transformation (lin, chg, ch1, pch, pc1, pca, cch, cca, log)
        frequency : str, optional
            Frequency aggregation (D, M, Q, Y)
        aggregation_method : str, default 'avg'
            How to aggregate when changing frequency (avg, sum, eop)
        output_type : str, default 'pandas'
            Output format ('pandas' or 'dict')
        **kwargs : dict
            Additional parameters for compatibility
            
        Returns
        -------
        pd.DataFrame or dict
            Series observations with requested transformations
            
        Examples
        --------
        >>> api = BOJDataAPI()
        >>> # Get percent change data
        >>> data = api.get_observations("BS01'MABJMTA", units='pch')
        >>> 
        >>> # Get quarterly averages with year-over-year change
        >>> data = api.get_observations("CPI", frequency='Q', units='pc1')
        """
        # Get data using core read_boj function
        df = read_boj(
            series=series_id,
            start_date=start_date,
            end_date=end_date,
            frequency=frequency,
            units=units,
            aggregation_method=aggregation_method
        )
        
        # Handle output type
        if output_type == 'dict':
            # Convert to FRED-style dictionary response
            observations = []
            for date, value in df.iloc[:, 0].items():
                observations.append({
                    'realtime_start': datetime.now().strftime('%Y-%m-%d'),
                    'realtime_end': datetime.now().strftime('%Y-%m-%d'),
                    'date': date.strftime('%Y-%m-%d'),
                    'value': str(value) if pd.notna(value) else '.'
                })
            
            return {
                'realtime_start': datetime.now().strftime('%Y-%m-%d'),
                'realtime_end': datetime.now().strftime('%Y-%m-%d'),
                'observation_start': df.index[0].strftime('%Y-%m-%d'),
                'observation_end': df.index[-1].strftime('%Y-%m-%d'),
                'units': units,
                'output_type': 1,  # Observations by Real-Time Period
                'file_type': 'json',
                'order_by': 'observation_date',
                'sort_order': 'asc',
                'count': len(df),
                'offset': 0,
                'limit': 100000,
                'observations': observations
            }
        else:
            return df
    
    def search_series(
        self,
        search_text: str,
        search_type: str = 'full_text',
        limit: int = 1000,
        offset: int = 0,
        order_by: str = 'relevance',
        filter_variable: Optional[str] = None,
        filter_value: Optional[str] = None,
        **kwargs
    ) -> pd.DataFrame:
        """
        Search for series matching text with FRED-compatible parameters.
        
        Parameters
        ----------
        search_text : str
            Text to search for
        search_type : str, default 'full_text'
            Type of search ('full_text' or 'series_id')
        limit : int, default 1000
            Maximum results to return
        offset : int, default 0
            Number of results to skip (for pagination)
        order_by : str, default 'relevance'
            Sort order (relevance, popularity, name, series_id)
        filter_variable : str, optional
            Variable to filter by (e.g., 'frequency', 'units')
        filter_value : str, optional
            Value to filter for
        **kwargs : dict
            Additional parameters for compatibility
            
        Returns
        -------
        pd.DataFrame
            Search results with series information
            
        Examples
        --------
        >>> api = BOJDataAPI()
        >>> # Search for interest rate series
        >>> results = api.search_series("interest rate", limit=20)
        >>> 
        >>> # Search by series ID pattern
        >>> results = api.search_series("IR", search_type='series_id')
        """
        if search_type == 'series_id':
            # For series_id search, use exact matching or prefix
            results = core_search_series(search_text, limit=limit)
            # Filter results where series_code starts with search_text
            if not results.empty:
                mask = results['series_code'].str.startswith(search_text.upper())
                results = results[mask]
        else:
            # Full text search
            results = self.comprehensive_search.search_all_categories(
                search_text, 
                max_results=limit
            )
        
        # Apply offset for pagination
        if offset > 0 and not results.empty:
            results = results.iloc[offset:]
        
        # Apply filters if provided
        if filter_variable and filter_value and not results.empty:
            if filter_variable in results.columns:
                results = results[results[filter_variable] == filter_value]
        
        # Sort results based on order_by parameter
        if not results.empty:
            if order_by == 'name' and 'name' in results.columns:
                results = results.sort_values('name')
            elif order_by == 'series_id' and 'series_code' in results.columns:
                results = results.sort_values('series_code')
            # Note: relevance and popularity sorting would require scoring
        
        # Add FRED-compatible columns
        if not results.empty:
            results['id'] = results.get('series_code', results.index)
            results['title'] = results.get('name', '')
            results['units_short'] = results.get('units', 'Index')
            results['frequency_short'] = results['frequency'].apply(
                self._get_frequency_short
            ) if 'frequency' in results.columns else 'Unknown'
            results['seasonal_adjustment_short'] = 'NSA'
            results['popularity'] = 50  # Default score
            
        return results
    
    def get_categories(self, category_id: Optional[int] = None) -> pd.DataFrame:
        """
        Get BOJ data categories.
        
        Parameters
        ----------
        category_id : int, optional
            Specific category ID to retrieve. If None, returns all top-level categories.
            
        Returns
        -------
        pd.DataFrame
            Categories with id, name, and parent_id
            
        Examples
        --------
        >>> api = BOJDataAPI()
        >>> # Get all top-level categories
        >>> categories = api.get_categories()
        >>> 
        >>> # Get subcategories of a specific category
        >>> subcats = api.get_categories(category_id=1)
        """
        # Get category tree from comprehensive search
        category_tree = self.comprehensive_search.get_category_tree()
        
        categories = []
        category_id_counter = 1
        
        for cat_name, cat_info in category_tree.items():
            categories.append({
                'id': category_id_counter,
                'name': cat_name,
                'parent_id': 0,  # Top level
            })
            
            # Add subcategories if they exist
            if isinstance(cat_info, dict) and 'subcategories' in cat_info:
                parent_id = category_id_counter
                category_id_counter += 1
                
                for subcat in cat_info['subcategories']:
                    categories.append({
                        'id': category_id_counter,
                        'name': subcat,
                        'parent_id': parent_id,
                    })
                    category_id_counter += 1
            else:
                category_id_counter += 1
        
        df = pd.DataFrame(categories)
        
        # Filter by category_id if provided
        if category_id is not None:
            # Return children of the specified category
            df = df[df['parent_id'] == category_id]
        else:
            # Return only top-level categories
            df = df[df['parent_id'] == 0]
        
        return df
    
    def get_series_categories(self, series_id: str) -> pd.DataFrame:
        """
        Get categories that contain a specific series.
        
        Parameters
        ----------
        series_id : str
            BOJ series identifier
            
        Returns
        -------
        pd.DataFrame
            Categories containing the series
            
        Examples
        --------
        >>> api = BOJDataAPI()
        >>> cats = api.get_series_categories("BS01'MABJMTA")
        """
        # Search for the series to find its category
        search_results = self.comprehensive_search.search_all_categories(series_id, max_results=1)
        
        if search_results.empty:
            raise SeriesNotFoundError(series_id)
        
        category = search_results.iloc[0].get('category', 'Unknown')
        
        # Return category information
        return pd.DataFrame([{
            'id': 1,
            'name': category,
            'parent_id': 0
        }])
    
    def get_observations_multi(
        self,
        series_ids: List[str],
        start_date: Optional[Union[str, pd.Timestamp]] = None,
        end_date: Optional[Union[str, pd.Timestamp]] = None,
        units: str = 'lin',
        frequency: Optional[str] = None,
        aggregation_method: str = 'avg',
        max_workers: int = 5,
        output_type: str = 'pandas',
    ) -> Union[pd.DataFrame, Dict[str, Any]]:
        """
        Get observations for multiple series with parallel downloads.
        
        Parameters
        ----------
        series_ids : List[str]
            List of BOJ series identifiers
        start_date : str or pd.Timestamp, optional
            Start date for data retrieval
        end_date : str or pd.Timestamp, optional
            End date for data retrieval
        units : str, default 'lin'
            Data transformation to apply to all series
        frequency : str, optional
            Frequency aggregation
        aggregation_method : str, default 'avg'
            How to aggregate when changing frequency
        max_workers : int, default 5
            Number of parallel downloads
        output_type : str, default 'pandas'
            Output format ('pandas' or 'dict')
            
        Returns
        -------
        pd.DataFrame or dict
            Combined observations for all series
            
        Examples
        --------
        >>> api = BOJDataAPI()
        >>> # Download multiple series efficiently
        >>> data = api.get_observations_multi(
        ...     ['IR01', 'IR02', 'FM01'],
        ...     units='pch'
        ... )
        """
        df = read_boj_batch(
            series_ids,
            start_date=start_date,
            end_date=end_date,
            frequency=frequency,
            units=units,
            aggregation_method=aggregation_method,
            max_workers=max_workers,
            show_progress=False
        )
        
        if output_type == 'dict':
            # Convert to FRED-style multi-series response
            observations = []
            
            for col in df.columns:
                for date, value in df[col].items():
                    observations.append({
                        'series_id': col,
                        'date': date.strftime('%Y-%m-%d'),
                        'value': str(value) if pd.notna(value) else '.'
                    })
            
            return {
                'series_count': len(df.columns),
                'observation_count': len(observations),
                'observations': observations
            }
        
        return df
    
    def get_releases(self, year: Optional[int] = None) -> pd.DataFrame:
        """
        Get BOJ data release calendar.
        
        Parameters
        ----------
        year : int, optional
            Year (default: current year)
            
        Returns
        -------
        pd.DataFrame
            Release schedule with date, series_name, frequency
            
        Examples
        --------
        >>> api = BOJDataAPI()
        >>> releases = api.get_releases(2024)
        """
        return self.release_calendar.get_releases(year)
    
    def get_release_dates(self, release_id: str, start_date: Optional[str] = None, 
                         end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Get release dates for a specific data series.
        
        Parameters
        ----------
        release_id : str
            Series name or identifier (e.g., 'TANKAN')
        start_date : str, optional
            Start date for filtering
        end_date : str, optional
            End date for filtering
            
        Returns
        -------
        pd.DataFrame
            Release dates for the series
        """
        # Get release dates
        dates = self.release_calendar.get_release_dates(release_id)
        
        # Filter by date range if provided
        if start_date:
            dates = dates[dates['date'] >= pd.to_datetime(start_date)]
        if end_date:
            dates = dates[dates['date'] <= pd.to_datetime(end_date)]
        
        return dates
    
    def get_series_tags(self, series_id: str) -> List[str]:
        """
        Get tags for a specific series.
        
        Parameters
        ----------
        series_id : str
            BOJ series identifier
            
        Returns
        -------
        List[str]
            Tags associated with the series
            
        Examples
        --------
        >>> api = BOJDataAPI()
        >>> tags = api.get_series_tags("BS01'MABJMTA")
        >>> print(tags)  # ['monetary base', 'money supply', 'monthly']
        """
        try:
            metadata = self.metadata_extractor.get_series_metadata(series_id)
            return metadata.get('tags', [])
        except:
            return []
    
    def search_by_tag(self, tag: str, limit: int = 100) -> pd.DataFrame:
        """
        Search for series by tag.
        
        Parameters
        ----------
        tag : str
            Tag to search for
        limit : int, default 100
            Maximum results
            
        Returns
        -------
        pd.DataFrame
            Series matching the tag
        """
        # Get all available series
        all_series = self.comprehensive_search.build_series_catalog()
        
        if all_series.empty:
            return pd.DataFrame()
        
        # Search for matching tags
        matching_series = []
        
        for idx, row in all_series.iterrows():
            if len(matching_series) >= limit:
                break
                
            series_id = row.get('series_code', row.get('code', ''))
            if not series_id:
                continue
            
            try:
                tags = self.get_series_tags(series_id)
                if tag.lower() in [t.lower() for t in tags]:
                    matching_series.append({
                        'series_id': series_id,
                        'name': row.get('name', ''),
                        'category': row.get('category', ''),
                        'frequency': row.get('frequency', ''),
                        'tags': tags
                    })
            except:
                continue
        
        return pd.DataFrame(matching_series)
    
    def _get_frequency_short(self, frequency: str) -> str:
        """Convert frequency to short form."""
        freq_map = {
            'Daily': 'D',
            'Monthly': 'M',
            'Quarterly': 'Q',
            'Annual': 'A',
            'Yearly': 'A',
        }
        return freq_map.get(frequency, frequency[0] if frequency else 'U')