"""
Utility functions for bojdata package
"""

import numpy as np
import pandas as pd

from .exceptions import BOJDataError


def parse_date_parameter(date_param):
    """
    Parse a date parameter into a pandas Timestamp.
    
    Parameters
    ----------
    date_param : str, pd.Timestamp, or datetime
        Date to parse
    
    Returns
    -------
    pd.Timestamp
        Parsed timestamp
    
    Raises
    ------
    BOJDataError
        If date cannot be parsed
    """
    try:
        return pd.Timestamp(date_param)
    except Exception as e:
        raise BOJDataError(f"Invalid date format: {date_param}. Error: {str(e)}")


def clean_data_frame(df: pd.DataFrame, series_name: str) -> pd.DataFrame:
    """
    Clean and format a BOJ data frame.
    
    Parameters
    ----------
    df : pd.DataFrame
        Raw data frame from BOJ
    series_name : str
        Name of the series for column naming
    
    Returns
    -------
    pd.DataFrame
        Cleaned data frame with proper formatting
    """
    # First row often contains metadata/headers
    if len(df) > 0:
        # Check if first row is metadata
        first_row = df.iloc[0]
        # Use .iloc to avoid deprecation warning
        if isinstance(first_row.iloc[0], str) and not _is_date_string(first_row.iloc[0]):
            # Extract column info from first row
            new_columns = df.columns + " " + first_row.astype(str)
            df.columns = new_columns
            df = df.iloc[1:]  # Remove metadata row
    
    # Clean column names
    df.columns = [col.strip() for col in df.columns]
    
    # Identify date column (usually first column)
    date_col = df.columns[0]
    
    # Parse dates - use copy to avoid SettingWithCopyWarning
    df = df.copy()
    
    # Try to detect date format from first non-null value
    first_date = df[date_col].dropna().iloc[0] if len(df[date_col].dropna()) > 0 else None
    if first_date and isinstance(first_date, str):
        if '-' in first_date and len(first_date) == 7:  # Format like "2023-12"
            df[date_col] = pd.to_datetime(df[date_col], format='%Y-%m', errors="coerce")
        elif '-' in first_date and len(first_date) == 10:  # Format like "2023-12-01"
            df[date_col] = pd.to_datetime(df[date_col], format='%Y-%m-%d', errors="coerce")
        elif '.' in first_date:  # Format like "2023.12"
            df[date_col] = df[date_col].apply(format_boj_date)
            df[date_col] = pd.to_datetime(df[date_col], format='%Y-%m-%d', errors="coerce")
        else:
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    else:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    
    # Set date as index
    df = df.set_index(date_col)
    df.index.name = "Date"
    
    # Replace missing value indicators
    df = df.replace(["ND", "NA", "...", "--", "-"], np.nan)
    
    # Convert to numeric
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    # Rename columns if only one value column
    if len(df.columns) == 1:
        df.columns = [series_name]
    
    # Sort by date (descending like BOJ website)
    df = df.sort_index(ascending=False)
    
    # Remove rows with all NaN values
    df = df.dropna(how="all")
    
    return df


def _is_date_string(s: str) -> bool:
    """Check if a string looks like a date"""
    try:
        pd.to_datetime(s)
        return True
    except:
        # Check for BOJ date formats like "2023.12"
        if "." in s and len(s.split(".")) == 2:
            try:
                year, month = s.split(".")
                int(year)
                int(month)
                return True
            except:
                pass
        return False


def format_boj_date(date_str: str) -> str:
    """
    Convert BOJ date format to standard format.
    
    BOJ uses formats like "2023.12" for December 2023
    """
    if "." in date_str:
        parts = date_str.split(".")
        if len(parts) == 2:
            year, month = parts
            try:
                # Convert to standard date
                return f"{year}-{month.zfill(2)}-01"
            except:
                pass
    return date_str


def validate_series_code(series_code: str) -> bool:
    """
    Validate if a series code follows BOJ format.
    
    Parameters
    ----------
    series_code : str
        Series code to validate
    
    Returns
    -------
    bool
        True if valid, False otherwise
    """
    if not series_code:
        return False
    
    # BOJ series codes are typically alphanumeric with possible special characters
    # Examples: "IR01", "BS01'MABJMTA", "FM01", "PR01'IUQCP001"
    
    # Basic validation - at least 2 characters
    if len(series_code) < 2:
        return False
    
    # Should contain at least one letter and one number
    has_letter = any(c.isalpha() for c in series_code)
    has_number = any(c.isdigit() for c in series_code)
    
    return has_letter and has_number