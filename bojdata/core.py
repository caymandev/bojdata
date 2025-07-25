"""
Core functions for accessing Bank of Japan statistical data
"""

import warnings
from typing import List, Optional, Union

import pandas as pd
import requests
from bs4 import BeautifulSoup

from .exceptions import BOJDataError
from .search import extract_download_url, search_for_series
from .utils import clean_data_frame, parse_date_parameter
from .transformations import apply_transformation

warnings.filterwarnings("ignore", category=UserWarning)

BASE_URL = "https://www.stat-search.boj.or.jp"


def read_boj(
    series: Optional[Union[str, List[str]]] = None,
    start_date: Optional[Union[str, pd.Timestamp]] = None,
    end_date: Optional[Union[str, pd.Timestamp]] = None,
    frequency: Optional[str] = None,
    units: str = 'lin',
    aggregation_method: str = 'avg',
) -> pd.DataFrame:
    """
    Download data series from the Bank of Japan Time-Series Data Search.
    
    Parameters
    ----------
    series : str or list of str, optional
        BOJ series code(s) to download (e.g., "BS01'MABJMTA" or ["IR01", "FM02"])
    start_date : str or pd.Timestamp, optional
        Start date for data (e.g., "2020-01-01")
    end_date : str or pd.Timestamp, optional
        End date for data (e.g., "2023-12-31")
    frequency : str, optional
        Data frequency conversion. Options: "D" (daily), "M" (monthly), 
        "Q" (quarterly), "Y" (yearly), None (original frequency)
    units : str, default 'lin'
        FRED-compatible data transformation:
        - 'lin': Levels (no transformation)
        - 'chg': Change from previous period
        - 'ch1': Change from year ago
        - 'pch': Percent change
        - 'pc1': Percent change from year ago
        - 'pca': Compounded annual rate
        - 'cch': Continuously compounded change
        - 'cca': Continuously compounded annual rate
        - 'log': Natural log
    aggregation_method : str, default 'avg'
        Method for frequency aggregation:
        - 'avg': Average (mean) of values in period
        - 'sum': Sum of values in period
        - 'eop': End of period value (last value)
    
    Returns
    -------
    pd.DataFrame
        DataFrame with dates as index and series as columns
    
    Raises
    ------
    BOJDataError
        If series is not provided or data cannot be downloaded
    
    Examples
    --------
    >>> # Single series
    >>> df = read_boj(series="BS01'MABJMTA")
    
    >>> # Multiple series with percent change
    >>> df = read_boj(series=["IR01", "FM02"], units='pch')
    
    >>> # With date range and year-over-year change
    >>> df = read_boj(series="FM01", start_date="2020-01-01", end_date="2023-12-31", units='pc1')
    """
    if series is None:
        raise BOJDataError("'series' parameter is required")
    
    # Convert to list if string
    if isinstance(series, str):
        series = [series]
    
    # Parse dates
    start_date = parse_date_parameter(start_date) if start_date else None
    end_date = parse_date_parameter(end_date) if end_date else None
    
    # Download data for each series
    all_data = []
    failed_series = []
    
    for s in series:
        try:
            df = _download_single_series(s, start_date, end_date, frequency, units, aggregation_method)
            all_data.append(df)
        except Exception as e:
            failed_series.append((s, str(e)))
            warnings.warn(f"Failed to download series {s}: {str(e)}")
    
    if not all_data:
        # Provide more helpful error message
        error_msg = "Failed to download any series."
        if failed_series:
            error_msg += " Errors: " + "; ".join([f"{s}: {e}" for s, e in failed_series[:3]])
        raise BOJDataError(error_msg)
    
    # Combine all series
    if len(all_data) == 1:
        return all_data[0]
    else:
        # Merge on date index
        result = all_data[0]
        for df in all_data[1:]:
            result = result.join(df, how="outer")
        return result


def _download_single_series(
    series: str,
    start_date: Optional[pd.Timestamp] = None,
    end_date: Optional[pd.Timestamp] = None,
    frequency: Optional[str] = None,
    units: str = 'lin',
    aggregation_method: str = 'avg',
) -> pd.DataFrame:
    """Download a single data series using BOJ's direct URL format"""
    from urllib.parse import urlencode
    
    # Build URL parameters
    params = {
        "cgi": "$nme_r030_en",
        "chkfrq": "MM",
        "rdoheader": "SIMPLE", 
        "rdodelimitar": "COMMA",
        "hdnYyyyFrom": "",
        "hdnYyyyTo": "",
        "sw_freq": "NONE",
        "sw_yearend": "NONE",
        "sw_observed": "NONE",
        "hdncode": series,
    }
    
    # Construct URL
    base_url = "https://www.stat-search.boj.or.jp/ssi/cgi-bin/famecgi2"
    url = f"{base_url}?{urlencode(params)}"
    
    try:
        # Get the search results page
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse to find CSV link
        soup = BeautifulSoup(response.content, "html.parser")
        csv_links = soup.select("a[href*=csv]")
        
        if not csv_links:
            raise BOJDataError(f"Could not find CSV file for series {series}")
        
        # Get CSV URL
        csv_url = f"https://www.stat-search.boj.or.jp/{csv_links[0]['href']}"
        
        # Download CSV
        df = pd.read_csv(csv_url, skiprows=0)
        
        # Clean and format
        df = clean_data_frame(df, series)
        
        # Filter by date range if specified
        if start_date or end_date:
            df = _filter_date_range(df, start_date, end_date)
        
        # Resample if frequency conversion requested
        if frequency:
            df = _resample_data(df, frequency, aggregation_method)
        
        # Apply transformation if requested
        if units != 'lin':
            df = apply_transformation(df, units)
        
        return df
        
    except requests.RequestException as e:
        raise BOJDataError(f"Failed to download series {series}: {str(e)}")
    except Exception as e:
        raise BOJDataError(f"Error processing series {series}: {str(e)}")


def _filter_date_range(
    df: pd.DataFrame,
    start_date: Optional[pd.Timestamp] = None,
    end_date: Optional[pd.Timestamp] = None,
) -> pd.DataFrame:
    """Filter DataFrame by date range"""
    if start_date:
        df = df[df.index >= start_date]
    if end_date:
        df = df[df.index <= end_date]
    return df


def _resample_data(df: pd.DataFrame, frequency: str, aggregation_method: str = 'avg') -> pd.DataFrame:
    """Resample data to specified frequency with chosen aggregation method"""
    freq_map = {
        "D": "D",  # Daily
        "M": "ME",  # Monthly (Month End)
        "Q": "QE",  # Quarterly (Quarter End)
        "Y": "YE",  # Yearly (Year End)
    }
    
    if frequency not in freq_map:
        warnings.warn(f"Invalid frequency '{frequency}', returning original data")
        return df
    
    # Apply chosen aggregation method
    resampler = df.resample(freq_map[frequency])
    
    if aggregation_method == 'avg':
        return resampler.mean()
    elif aggregation_method == 'sum':
        return resampler.sum()
    elif aggregation_method == 'eop':
        return resampler.last()
    else:
        from .exceptions import InvalidParameterError
        raise InvalidParameterError(
            'aggregation_method',
            aggregation_method,
            ['avg', 'sum', 'eop']
        )


def get_boj_datasets() -> pd.DataFrame:
    """
    Retrieve a list of available BOJ data sets.
    
    Returns
    -------
    pd.DataFrame
        DataFrame with columns: 'name', 'description', 'url'
    
    Examples
    --------
    >>> datasets = get_boj_datasets()
    >>> # Filter for interest rate datasets
    >>> ir_datasets = datasets[datasets['name'].str.contains('ir')]
    """
    # Since the BOJ website structure has changed, we'll use the download page
    url = f"{BASE_URL}/info/dload_en.html"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Extract dataset information from the flat files download page
        datasets = []
        
        # Look for all download links
        links = soup.find_all("a", href=True)
        
        for link in links:
            href = link.get("href", "")
            text = link.text.strip()
            
            # Check if it's a data file link
            if any(ext in href for ext in [".zip", ".csv", ".xlsx", ".xls"]):
                # Extract category from link text or filename
                if "price" in text.lower() or "price" in href.lower():
                    category = "Prices"
                elif "tankan" in text.lower() or "tankan" in href.lower():
                    category = "TANKAN"
                elif "flow" in text.lower() or "fof" in href.lower():
                    category = "Flow of Funds"
                elif "balance" in text.lower() or "bp" in href.lower():
                    category = "Balance of Payments"
                elif "bis" in text.lower():
                    category = "BIS Statistics"
                else:
                    category = "Other"
                
                datasets.append({
                    "name": text or href.split("/")[-1],
                    "category": category,
                    "url": f"{BASE_URL}{href}" if not href.startswith("http") else href,
                    "type": "flat_file",
                })
        
        # Add known categories even if not found in links
        if not datasets:
            # Provide a default list of known datasets
            datasets = [
                {"name": "Prices (Monthly)", "category": "Prices", "url": f"{BASE_URL}/info/prices_m_en.zip", "type": "flat_file"},
                {"name": "TANKAN (Quarterly)", "category": "TANKAN", "url": f"{BASE_URL}/info/tankan_q_en.zip", "type": "flat_file"},
                {"name": "Flow of Funds (Quarterly)", "category": "Flow of Funds", "url": f"{BASE_URL}/info/fof_q_en.zip", "type": "flat_file"},
                {"name": "Balance of Payments (Monthly)", "category": "Balance of Payments", "url": f"{BASE_URL}/info/bp_m_en.zip", "type": "flat_file"},
                {"name": "BIS Statistics (Quarterly)", "category": "BIS Statistics", "url": f"{BASE_URL}/info/bis_q_en.zip", "type": "flat_file"},
            ]
        
        return pd.DataFrame(datasets)
        
    except Exception as e:
        raise BOJDataError(f"Failed to retrieve dataset list: {str(e)}")


def search_series(
    keyword: str,
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    search_type: str = 'full_text',
    order_by: str = 'relevance',
    filter_variable: Optional[str] = None,
    filter_value: Optional[str] = None,
) -> pd.DataFrame:
    """
    Search for BOJ data series by keyword with FRED-compatible parameters.
    
    Parameters
    ----------
    keyword : str
        Search keyword (e.g., "interest rate", "exchange", "GDP")
    category : str, optional
        Filter by category (e.g., "Interest Rates", "Prices")
    limit : int, default 50
        Maximum number of results to return
    offset : int, default 0
        Number of results to skip for pagination
    search_type : str, default 'full_text'
        Type of search: 'full_text' or 'series_id'
    order_by : str, default 'relevance'
        Sort order: 'relevance', 'name', 'series_id', 'popularity'
    filter_variable : str, optional
        Variable to filter by (e.g., 'frequency', 'units')
    filter_value : str, optional
        Value to filter for (e.g., 'Monthly', 'Index')
    
    Returns
    -------
    pd.DataFrame
        DataFrame with columns: 'series_code', 'name', 'category', 'frequency'
    
    Examples
    --------
    >>> # Search for interest rate series
    >>> results = search_series("interest rate")
    
    >>> # Search by series ID pattern
    >>> results = search_series("IR", search_type='series_id')
    
    >>> # Search with pagination
    >>> results = search_series("price", limit=20, offset=20)
    """
    # This would typically query the BOJ search API
    # For now, return a placeholder implementation
    # In a full implementation, this would scrape or use an API
    
    results = []
    
    # Comprehensive list of actual BOJ series for realistic search
    sample_series = [
        # Interest Rates
        ("IR01", "Uncollateralized Overnight Call Rate", "Interest Rates", "Daily"),
        ("IR02", "Basic Loan Rate", "Interest Rates", "Monthly"),
        ("IR03", "Average Interest Rates on Deposits", "Interest Rates", "Monthly"),
        ("IR04", "Average Contract Interest Rates on Loans and Discounts", "Interest Rates", "Monthly"),
        
        # Financial Markets
        ("FM01", "Foreign Exchange Rates (USD/JPY)", "Financial Markets", "Daily"),
        ("FM02", "Stock Market Indices (TOPIX)", "Financial Markets", "Daily"),
        ("FM03", "Stock Market Indices (Nikkei 225)", "Financial Markets", "Daily"),
        ("FM08", "Yields on Government Bonds", "Financial Markets", "Daily"),
        
        # Money and Deposits
        ("BS01'MABJMTA", "Monetary Base (Average Amounts Outstanding)", "Money and Deposits", "Monthly"),
        ("BS01'MABJ_MABJ", "Monetary Base (End of Period)", "Money and Deposits", "Monthly"),
        ("MD01", "Money Stock M1", "Money and Deposits", "Monthly"),
        ("MD02", "Money Stock M2", "Money and Deposits", "Monthly"),
        ("MD03", "Money Stock M3", "Money and Deposits", "Monthly"),
        
        # Prices
        ("PR01'IUQCP001", "Consumer Price Index", "Prices", "Monthly"),
        ("CGPI", "Corporate Goods Price Index", "Prices", "Monthly"),
        ("SPPI", "Services Producer Price Index", "Prices", "Monthly"),
        
        # Balance of Payments
        ("BP01'CJAA", "Current Account", "Balance of Payments", "Monthly"),
        ("BP02", "Trade Balance", "Balance of Payments", "Monthly"),
        ("BP03", "Financial Account", "Balance of Payments", "Monthly"),
        
        # TANKAN
        ("TK01", "Business Conditions DI (Large Manufacturers)", "TANKAN", "Quarterly"),
        ("TK02", "Business Conditions DI (Large Non-manufacturers)", "TANKAN", "Quarterly"),
    ]
    
    # Apply search based on search_type
    for code, name, cat, freq in sample_series:
        match = False
        
        if search_type == 'series_id':
            # Match by series code prefix
            match = code.upper().startswith(keyword.upper())
        else:
            # Full text search in name
            match = keyword.lower() in name.lower()
        
        if match and (category is None or category == cat):
            results.append({
                "series_code": code,
                "name": name,
                "category": cat,
                "frequency": freq,
            })
    
    # Sort results based on order_by parameter
    if results and order_by != 'relevance':
        df_temp = pd.DataFrame(results)
        if order_by == 'name':
            df_temp = df_temp.sort_values('name')
        elif order_by == 'series_id':
            df_temp = df_temp.sort_values('series_code')
        results = df_temp.to_dict('records')
    
    # Apply filter if provided
    if filter_variable and filter_value and results:
        filtered_results = []
        for r in results:
            if filter_variable in r and str(r[filter_variable]).lower() == str(filter_value).lower():
                filtered_results.append(r)
        results = filtered_results
    
    # Apply offset and limit for pagination
    if offset > 0:
        results = results[offset:]
    
    return pd.DataFrame(results[:limit])