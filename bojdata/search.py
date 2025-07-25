"""
Functions for searching and discovering BOJ data series
"""

from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

from .exceptions import BOJDataError

BASE_URL = "https://www.stat-search.boj.or.jp"


def search_for_series(series_code: str) -> str:
    """
    Search for a specific series code and return the results page URL.
    
    Parameters
    ----------
    series_code : str
        The BOJ series code to search for
    
    Returns
    -------
    str
        URL of the search results page
    
    Raises
    ------
    BOJDataError
        If the search fails or series is not found
    """
    search_path = "/ssi/cgi-bin/famecgi2?cgi=$nme_a000_en"
    search_params = {
        "hdncode": series_code,
        "chkfrq": "MM",  # Monthly frequency as default
        "rdoheader": "SIMPLE",
        "rdodelimitar": "COMMA",
        "sw_freq": "NONE",
        "sw_yearend": "NONE",
        "sw_observed": "NONE",
    }
    
    # Construct search URL
    params_str = urlencode(search_params)
    url = f"{BASE_URL}{search_path}&{params_str}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return url
    except Exception as e:
        raise BOJDataError(f"Failed to search for series {series_code}: {str(e)}")


def extract_download_url(search_results_url: str) -> str:
    """
    Extract the CSV download URL from a search results page.
    
    Parameters
    ----------
    search_results_url : str
        URL of the search results page
    
    Returns
    -------
    str
        Direct URL to download the CSV file
    
    Raises
    ------
    BOJDataError
        If no download link is found
    """
    try:
        response = requests.get(search_results_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Look for CSV download links
        csv_links = soup.find_all("a", href=lambda x: x and ".csv" in x)
        
        if not csv_links:
            # Try alternative patterns
            csv_links = soup.find_all("a", href=lambda x: x and "csv" in x.lower())
        
        if not csv_links:
            raise BOJDataError("No CSV download link found in search results")
        
        # Get the first CSV link
        csv_path = csv_links[0]["href"]
        
        # Construct full URL
        if csv_path.startswith("http"):
            return csv_path
        else:
            return f"{BASE_URL}{csv_path}"
            
    except BOJDataError:
        raise
    except Exception as e:
        raise BOJDataError(f"Failed to extract download URL: {str(e)}")


def list_categories() -> list:
    """
    List all available data categories from BOJ.
    
    Returns
    -------
    list
        List of category names
    """
    categories = [
        "Interest Rates",
        "Financial Markets", 
        "Money and Deposits",
        "Loans",
        "Balance Sheets",
        "Flow of Funds",
        "TANKAN",
        "Prices",
        "Public Finance",
        "Balance of Payments",
        "BIS-Related Statistics",
    ]
    return categories


def get_series_metadata(series_code: str) -> dict:
    """
    Get metadata for a specific series.
    
    Parameters
    ----------
    series_code : str
        The BOJ series code
    
    Returns
    -------
    dict
        Dictionary containing series metadata (name, frequency, unit, etc.)
    """
    # This would typically fetch from the BOJ website
    # For now, return placeholder data
    metadata = {
        "series_code": series_code,
        "name": f"Series {series_code}",
        "frequency": "Monthly",
        "unit": "Index",
        "start_date": "2000-01-01",
        "last_updated": "2024-01-01",
    }
    return metadata