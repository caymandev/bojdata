"""
Batch operations for efficient multiple series downloads.

This module provides functionality for downloading multiple series in parallel,
improving performance when fetching many series at once.
"""

import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Union, Dict, Any, Tuple
import pandas as pd

from .core import _download_single_series, parse_date_parameter
from .exceptions import BOJDataError


def read_boj_batch(
    series_list: List[str],
    start_date: Optional[Union[str, pd.Timestamp]] = None,
    end_date: Optional[Union[str, pd.Timestamp]] = None,
    frequency: Optional[str] = None,
    units: str = 'lin',
    aggregation_method: str = 'avg',
    max_workers: int = 5,
    show_progress: bool = True,
) -> pd.DataFrame:
    """
    Download multiple BOJ series in parallel for improved performance.
    
    Parameters
    ----------
    series_list : List[str]
        List of BOJ series codes to download
    start_date : str or pd.Timestamp, optional
        Start date for data
    end_date : str or pd.Timestamp, optional
        End date for data
    frequency : str, optional
        Frequency conversion ('D', 'M', 'Q', 'Y')
    units : str, default 'lin'
        Data transformation (see transformations module)
    aggregation_method : str, default 'avg'
        Aggregation method ('avg', 'sum', 'eop')
    max_workers : int, default 5
        Maximum number of parallel downloads
    show_progress : bool, default True
        Show download progress
        
    Returns
    -------
    pd.DataFrame
        Combined DataFrame with all series
        
    Examples
    --------
    >>> from bojdata.batch import read_boj_batch
    >>> 
    >>> # Download 10 series in parallel
    >>> series = ['IR01', 'IR02', 'IR03', 'FM01', 'FM02', 
    ...           'BS01', 'MD01', 'MD02', 'PR01', 'BP01']
    >>> df = read_boj_batch(series, max_workers=5)
    >>> 
    >>> # With transformations
    >>> df = read_boj_batch(
    ...     series,
    ...     units='pch',
    ...     start_date='2020-01-01'
    ... )
    """
    if not series_list:
        raise BOJDataError("No series provided for batch download")
    
    # Parse dates once
    start_date = parse_date_parameter(start_date) if start_date else None
    end_date = parse_date_parameter(end_date) if end_date else None
    
    # Results storage
    successful_downloads: List[Tuple[str, pd.DataFrame]] = []
    failed_downloads: List[Tuple[str, str]] = []
    
    def download_series(series_code: str) -> Tuple[str, Union[pd.DataFrame, Exception]]:
        """Download a single series and return result or exception."""
        try:
            df = _download_single_series(
                series_code,
                start_date,
                end_date,
                frequency,
                units,
                aggregation_method
            )
            return (series_code, df)
        except Exception as e:
            return (series_code, e)
    
    # Download in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all downloads
        future_to_series = {
            executor.submit(download_series, s): s 
            for s in series_list
        }
        
        # Process completed downloads
        completed = 0
        total = len(series_list)
        
        for future in as_completed(future_to_series):
            series_code = future_to_series[future]
            completed += 1
            
            if show_progress:
                print(f"Downloaded {completed}/{total}: {series_code}", end='\r')
            
            try:
                series_code, result = future.result()
                
                if isinstance(result, Exception):
                    failed_downloads.append((series_code, str(result)))
                    warnings.warn(f"Failed to download {series_code}: {result}")
                else:
                    successful_downloads.append((series_code, result))
                    
            except Exception as e:
                failed_downloads.append((series_code, str(e)))
                warnings.warn(f"Failed to download {series_code}: {e}")
    
    if show_progress:
        print(f"\nCompleted: {len(successful_downloads)} successful, {len(failed_downloads)} failed")
    
    # Combine results
    if not successful_downloads:
        error_msg = f"Failed to download any series. Errors: {failed_downloads[:3]}"
        raise BOJDataError(error_msg)
    
    # Merge all DataFrames
    if len(successful_downloads) == 1:
        return successful_downloads[0][1]
    else:
        # Start with first DataFrame
        combined_df = successful_downloads[0][1]
        
        # Join others
        for series_code, df in successful_downloads[1:]:
            combined_df = combined_df.join(df, how='outer')
        
        return combined_df


def get_observations_multi(
    api_instance,
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
    FRED-compatible method to get observations for multiple series.
    
    This is a method to be added to BOJDataAPI class.
    
    Parameters
    ----------
    series_ids : List[str]
        List of BOJ series identifiers
    start_date : str or pd.Timestamp, optional
        Start date for data retrieval
    end_date : str or pd.Timestamp, optional
        End date for data retrieval
    units : str, default 'lin'
        Data transformation to apply
    frequency : str, optional
        Frequency aggregation
    aggregation_method : str, default 'avg'
        Aggregation method
    max_workers : int, default 5
        Number of parallel downloads
    output_type : str, default 'pandas'
        Output format ('pandas' or 'dict')
        
    Returns
    -------
    pd.DataFrame or dict
        Combined observations for all series
    """
    # Use batch download
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
        # Convert to FRED-style response
        # This would contain observations for all series
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