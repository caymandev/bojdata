"""
FRED to BOJ series code mapping for users migrating from FRED
"""

from typing import Dict, Optional

# FRED to BOJ series mapping
FRED_TO_BOJ_MAPPING: Dict[str, str] = {
    # Exchange Rates
    "DEXJPUS": "FM01",  # USD/JPY Exchange Rate
    "EXJPUS": "FM01",   # Alternative FRED code for USD/JPY
    
    # Interest Rates
    "IRSTCI01JPM156N": "IR01",  # Japan Immediate Rates: Call Money/Interbank Rate
    "INTDSRJPM193N": "IR03",    # Interest Rates: Deposit Rates
    "IR3TIB01JPM156N": "IR01",  # 3-Month Tokyo Interbank Rate
    
    # Stock Market
    "NIKKEI225": "FM03",  # Nikkei 225 Index
    "JPNASARTINDEXD": "FM02",  # Tokyo Stock Price Index (TOPIX)
    
    # Monetary Aggregates
    "MYAGM1JPM189S": "MD01",  # M1 Money Stock
    "MYAGM2JPM189S": "MD02",  # M2 Money Stock
    "MYAGM3JPM189S": "MD03",  # M3 Money Stock
    "BOGMBASE": "BS01'MABJMTA",  # Monetary Base
    
    # Prices / Inflation
    "JPNCPIALLMINMEI": "PR01'IUQCP001",  # CPI All Items
    "CPALTT01JPM661S": "PR01'IUQCP001",  # CPI All Items Alternative
    
    # Balance of Payments
    "BPBLTD01JPQ637S": "BP01'CJAA",  # Current Account Balance
    "XTEXVA01JPM667S": "BP02",  # Trade Balance
    
    # Production and Business
    "JPNPROINDMISMEI": "ST01",  # Industrial Production Index
    
    # Government Bond Yields
    "IRLTLT01JPM156N": "FM08",  # Long-Term Government Bond Yields (10-year)
    
    # GDP (Note: BOJ may not have direct GDP series)
    "JPNRGDPEXP": None,  # Real GDP - No direct BOJ equivalent
}

# Reverse mapping - prefer primary FRED codes
BOJ_TO_FRED_MAPPING: Dict[str, str] = {}
# Build reverse mapping with preference for primary codes
for k, v in FRED_TO_BOJ_MAPPING.items():
    if v is not None and v not in BOJ_TO_FRED_MAPPING:
        BOJ_TO_FRED_MAPPING[v] = k
# Override with preferred mappings
BOJ_TO_FRED_MAPPING.update({
    "FM01": "DEXJPUS",  # Prefer DEXJPUS over EXJPUS
    "PR01'IUQCP001": "JPNCPIALLMINMEI",  # Prefer primary CPI code
})

# Category mapping
FRED_CATEGORY_TO_BOJ: Dict[str, str] = {
    "Exchange Rates": "Financial Markets",
    "Interest Rates": "Interest Rates",
    "Stock Market Indexes": "Financial Markets",
    "Money Supply": "Money and Deposits",
    "Prices": "Prices",
    "Trade Balance": "Balance of Payments",
    "Production & Business Activity": "Statistics",
}


def get_boj_series_from_fred(fred_series_id: str) -> Optional[str]:
    """
    Get the equivalent BOJ series code for a FRED series.
    
    Parameters
    ----------
    fred_series_id : str
        FRED series identifier
        
    Returns
    -------
    str or None
        Equivalent BOJ series code, or None if no mapping exists
        
    Examples
    --------
    >>> get_boj_series_from_fred("DEXJPUS")
    'FM01'
    
    >>> get_boj_series_from_fred("NIKKEI225")
    'FM03'
    """
    return FRED_TO_BOJ_MAPPING.get(fred_series_id.upper())


def get_fred_series_from_boj(boj_series_id: str) -> Optional[str]:
    """
    Get the equivalent FRED series code for a BOJ series.
    
    Parameters
    ----------
    boj_series_id : str
        BOJ series identifier
        
    Returns
    -------
    str or None
        Equivalent FRED series code, or None if no mapping exists
        
    Examples
    --------
    >>> get_fred_series_from_boj("FM01")
    'DEXJPUS'
    
    >>> get_fred_series_from_boj("BS01'MABJMTA")
    'BOGMBASE'
    """
    return BOJ_TO_FRED_MAPPING.get(boj_series_id)


def suggest_boj_alternative(fred_series_id: str) -> str:
    """
    Suggest a BOJ alternative for a FRED series with helpful message.
    
    Parameters
    ----------
    fred_series_id : str
        FRED series identifier
        
    Returns
    -------
    str
        Helpful message about BOJ equivalent or alternatives
        
    Examples
    --------
    >>> suggest_boj_alternative("DEXJPUS")
    "Use BOJ series 'FM01' for USD/JPY exchange rate data"
    """
    boj_code = get_boj_series_from_fred(fred_series_id)
    
    if boj_code:
        # Get the description from our mapping
        descriptions = {
            "FM01": "USD/JPY exchange rate",
            "FM03": "Nikkei 225 stock index",
            "FM02": "TOPIX stock index",
            "IR01": "overnight call rate",
            "MD01": "M1 money stock",
            "MD02": "M2 money stock",
            "MD03": "M3 money stock",
            "BS01'MABJMTA": "monetary base",
            "PR01'IUQCP001": "consumer price index",
            "BP01'CJAA": "current account balance",
            "BP02": "trade balance",
            "FM08": "10-year JGB yields",
        }
        
        desc = descriptions.get(boj_code, "equivalent data")
        return f"Use BOJ series '{boj_code}' for {desc}"
    
    # Check for partial matches or categories
    fred_upper = fred_series_id.upper()
    
    if "JPY" in fred_upper or "EXJP" in fred_upper:
        return "Try BOJ series 'FM01' for USD/JPY exchange rate data"
    
    if "NIKKEI" in fred_upper:
        return "Try BOJ series 'FM03' for Nikkei 225 index data"
    
    if "M1" in fred_upper or "M2" in fred_upper or "M3" in fred_upper:
        return "Try BOJ series 'MD01', 'MD02', or 'MD03' for money stock data"
    
    if "CPI" in fred_upper or "INFLATION" in fred_upper:
        return "Try BOJ series 'PR01'IUQCP001' for consumer price index data"
    
    if "INTEREST" in fred_upper or "RATE" in fred_upper:
        return "Try BOJ series 'IR01' through 'IR04' for interest rate data"
    
    if "DGS" in fred_upper or "TREASURY" in fred_upper or "BOND" in fred_upper or "YIELD" in fred_upper:
        return "Try BOJ series 'FM08' for 10-year JGB yields or search for 'bond' for other maturities"
    
    if "GDP" in fred_upper:
        return "BOJ doesn't directly provide GDP data. Check Cabinet Office statistics instead"
    
    return ("No direct BOJ equivalent found. Use api.search_series() to find similar data "
            "or api.list_valid_series_codes() to browse all available series")


def get_all_fred_mappings() -> Dict[str, Dict[str, Optional[str]]]:
    """
    Get all FRED to BOJ mappings with metadata.
    
    Returns
    -------
    dict
        Dictionary with FRED codes as keys and mapping info as values
        
    Examples
    --------
    >>> mappings = get_all_fred_mappings()
    >>> print(mappings['DEXJPUS'])
    {'boj_code': 'FM01', 'description': 'USD/JPY Exchange Rate'}
    """
    descriptions = {
        "DEXJPUS": "USD/JPY Exchange Rate",
        "EXJPUS": "USD/JPY Exchange Rate (Alternative)",
        "IRSTCI01JPM156N": "Call Money/Interbank Rate",
        "INTDSRJPM193N": "Deposit Interest Rates",
        "IR3TIB01JPM156N": "3-Month Interbank Rate",
        "NIKKEI225": "Nikkei 225 Stock Index",
        "JPNASARTINDEXD": "TOPIX Stock Index",
        "MYAGM1JPM189S": "M1 Money Stock",
        "MYAGM2JPM189S": "M2 Money Stock",
        "MYAGM3JPM189S": "M3 Money Stock",
        "BOGMBASE": "Monetary Base",
        "JPNCPIALLMINMEI": "Consumer Price Index",
        "CPALTT01JPM661S": "Consumer Price Index (Alternative)",
        "BPBLTD01JPQ637S": "Current Account Balance",
        "XTEXVA01JPM667S": "Trade Balance",
        "JPNPROINDMISMEI": "Industrial Production Index",
        "IRLTLT01JPM156N": "10-Year Government Bond Yields",
        "JPNRGDPEXP": "Real GDP (No BOJ equivalent)",
    }
    
    result = {}
    for fred_code, boj_code in FRED_TO_BOJ_MAPPING.items():
        result[fred_code] = {
            "boj_code": boj_code,
            "description": descriptions.get(fred_code, ""),
            "available": boj_code is not None
        }
    
    return result