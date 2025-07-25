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
    
    # BOJ series codes follow specific patterns:
    # Format 1: PREFIX+NUMBER (e.g., "IR01", "FM02", "BS01")
    # Format 2: PREFIX+NUMBER'SUFFIX (e.g., "BS01'MABJMTA", "PR01'IUQCP001")
    
    # Valid prefixes based on BOJ categories
    valid_prefixes = [
        'IR',  # Interest Rates
        'FM',  # Financial Markets
        'BS',  # Balance Sheet (Monetary Base)
        'MD',  # Money and Deposits
        'PR',  # Prices
        'BP',  # Balance of Payments
        'TK',  # TANKAN
        'PS',  # Payment and Settlement
        'LN',  # Loans
        'CP',  # Corporate Prices
        'SP',  # Service Prices
        'ST',  # Statistics
        'FF',  # Flow of Funds
        'BIS', # BIS Statistics
    ]
    
    # Check basic format
    import re
    
    # Pattern: PREFIX + NUMBER (optional: ' + SUFFIX)
    pattern = r'^([A-Z]+)(\d+)(\'.+)?$'
    match = re.match(pattern, series_code.upper())
    
    if not match:
        return False
    
    prefix = match.group(1)
    
    # Check if prefix is valid
    if prefix not in valid_prefixes:
        return False
    
    # If there's a suffix (like 'MABJMTA), check if it's a known valid code
    if match.group(3):  # Has suffix
        # Get list of known valid codes with this prefix
        valid_codes_df = list_valid_series_codes()
        valid_codes_list = valid_codes_df['series_code'].tolist()
        return series_code.upper() in [code.upper() for code in valid_codes_list]
    
    # If no suffix, just check prefix
    return True


def get_series_code_hint(series_code: str) -> str:
    """
    Get a helpful hint for an invalid series code.
    
    Parameters
    ----------
    series_code : str
        Invalid series code
    
    Returns
    -------
    str
        Helpful hint message
    """
    # Define valid prefixes at the top
    valid_prefixes = ['IR', 'FM', 'BS', 'MD', 'PR', 'BP', 'TK', 'PS', 'LN', 'CP', 'SP', 'ST', 'FF', 'BIS']
    
    # Common mistakes and their corrections
    common_mistakes = {
        'interest': 'Try IR01 or IR02 for interest rate data',
        'exchange': 'Try FM01 for USD/JPY exchange rate',
        'monetary': "Try BS01'MABJMTA for monetary base",
        'price': "Try PR01'IUQCP001 for consumer price index",
        'tankan': 'Try TK01 or TK02 for TANKAN survey data',
    }
    
    # Check if the code contains common search terms
    lower_code = series_code.lower()
    for term, hint in common_mistakes.items():
        if term in lower_code:
            return hint
    
    # Check if it looks like a series code but with invalid prefix
    import re
    pattern = r'^([A-Z]+)(\d+)(\'.+)?$'
    match = re.match(pattern, series_code.upper())
    if match:
        prefix = match.group(1)
        if prefix not in valid_prefixes:
            return f"Invalid prefix '{prefix}'. Valid prefixes are: {', '.join(valid_prefixes[:5])}... Use api.list_valid_series_codes() to see all valid codes"
    
    # Check if it's missing a quote
    if "'" not in series_code and len(series_code) > 4:
        # Might be missing the quote separator
        for i in range(2, min(6, len(series_code))):
            if series_code[:i].isalpha() and series_code[i:i+2].isdigit():
                potential_prefix = series_code[:i] + series_code[i:i+2]
                # Only suggest if it's a valid prefix
                if series_code[:i].upper() in valid_prefixes:
                    return f"Did you mean '{potential_prefix}'? BOJ codes use format like BS01'MABJMTA"
    
    # Default hints based on pattern
    if not any(c.isdigit() for c in series_code):
        return "Series codes need numbers. Try IR01, FM01, or BS01'MABJMTA"
    
    if not any(c.isalpha() for c in series_code):
        return "Series codes need letters. Try IR01, FM01, or BS01'MABJMTA"
    
    # Suggest using discovery methods
    return "Use api.search_series() or api.list_valid_series_codes() to find valid codes"


def list_valid_series_codes() -> pd.DataFrame:
    """
    Return DataFrame of all valid series codes with descriptions.
    
    Returns
    -------
    pd.DataFrame
        DataFrame with columns: series_code, name, category, frequency
    """
    # Comprehensive list of known BOJ series codes
    valid_series = [
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
        
        # Money and Deposits (with common suffixes)
        ("BS01'MABJMTA", "Monetary Base (Average Amounts Outstanding)", "Money and Deposits", "Monthly"),
        ("BS01'MABJ_MABJ", "Monetary Base (End of Period)", "Money and Deposits", "Monthly"),
        ("MD01", "Money Stock M1", "Money and Deposits", "Monthly"),
        ("MD02", "Money Stock M2", "Money and Deposits", "Monthly"),
        ("MD03", "Money Stock M3", "Money and Deposits", "Monthly"),
        
        # Prices
        ("PR01'IUQCP001", "Consumer Price Index", "Prices", "Monthly"),
        ("CP01", "Corporate Goods Price Index", "Prices", "Monthly"),
        ("SP01", "Services Producer Price Index", "Prices", "Monthly"),
        
        # Balance of Payments
        ("BP01'CJAA", "Current Account", "Balance of Payments", "Monthly"),
        ("BP02", "Trade Balance", "Balance of Payments", "Monthly"),
        ("BP03", "Financial Account", "Balance of Payments", "Monthly"),
        
        # TANKAN
        ("TK01", "Business Conditions DI (Large Manufacturers)", "TANKAN", "Quarterly"),
        ("TK02", "Business Conditions DI (Large Non-manufacturers)", "TANKAN", "Quarterly"),
        ("TK03", "Business Conditions DI (Medium-sized Enterprises)", "TANKAN", "Quarterly"),
        ("TK04", "Business Conditions DI (Small Enterprises)", "TANKAN", "Quarterly"),
        
        # Flow of Funds
        ("FF01", "Flow of Funds - Financial Assets and Liabilities", "Flow of Funds", "Quarterly"),
        ("FF02", "Flow of Funds - By Sector", "Flow of Funds", "Quarterly"),
        
        # Additional common series
        ("ST01", "Economic Statistics", "Statistics", "Various"),
        ("PS01", "Payment and Settlement Statistics", "Payment Systems", "Monthly"),
        ("LN01", "Loans by Deposit-taking Institutions", "Loans", "Monthly"),
    ]
    
    return pd.DataFrame(valid_series, columns=['series_code', 'name', 'category', 'frequency'])


def search_series_fuzzy(term: str, limit: int = 10) -> pd.DataFrame:
    """
    Fuzzy search that's more forgiving of search terms.
    
    Parameters
    ----------
    term : str
        Search term
    limit : int, default 10
        Maximum number of results
    
    Returns
    -------
    pd.DataFrame
        Matching series with fuzzy matching score
    """
    from difflib import SequenceMatcher
    
    # Get all valid series
    all_series = list_valid_series_codes()
    
    # Calculate fuzzy match scores
    scores = []
    term_lower = term.lower()
    
    for idx, row in all_series.iterrows():
        # Check series code
        code_score = SequenceMatcher(None, term_lower, row['series_code'].lower()).ratio()
        
        # Check name
        name_score = SequenceMatcher(None, term_lower, row['name'].lower()).ratio()
        
        # Check if term is contained in name (bonus points)
        contains_bonus = 0.3 if term_lower in row['name'].lower() else 0
        
        # Check category
        cat_score = SequenceMatcher(None, term_lower, row['category'].lower()).ratio()
        
        # Combined score (weighted)
        total_score = max(code_score, name_score + contains_bonus, cat_score * 0.8)
        
        scores.append(total_score)
    
    # Add scores to dataframe
    all_series['match_score'] = scores
    
    # Filter and sort by score
    matches = all_series[all_series['match_score'] > 0.3].copy()
    matches = matches.sort_values('match_score', ascending=False).head(limit)
    
    # Drop the score column before returning
    return matches.drop('match_score', axis=1).reset_index(drop=True)