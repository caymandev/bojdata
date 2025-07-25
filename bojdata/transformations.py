"""
FRED-compatible data transformations for BOJ data series.

This module provides transformation functions matching FRED API's 'units' parameter.
All transformations operate on pandas Series/DataFrame objects.

Available Transformations
------------------------
- lin : Levels (no transformation) - returns original values
- chg : Change from previous period
- ch1 : Change from year ago (automatically detects frequency)
- pch : Percent change from previous period
- pc1 : Percent change from year ago
- pca : Compounded annual rate of change
- cch : Continuously compounded rate of change
- cca : Continuously compounded annual rate of change
- log : Natural logarithm

Examples
--------
>>> import pandas as pd
>>> from bojdata.transformations import apply_transformation
>>> 
>>> # Create sample data
>>> dates = pd.date_range('2020-01-01', '2023-12-31', freq='M')
>>> data = pd.Series(range(100, 100 + len(dates)), index=dates)
>>> 
>>> # Apply percent change transformation
>>> pch_data = apply_transformation(data, 'pch')
>>> 
>>> # Apply year-over-year percent change
>>> yoy_data = apply_transformation(data, 'pc1')
>>> 
>>> # Apply to DataFrame (transforms all columns)
>>> df = pd.DataFrame({'series1': data, 'series2': data * 2})
>>> transformed_df = apply_transformation(df, 'log')

Notes
-----
Transformations automatically handle:
- Missing values (NaN) in the data
- Frequency detection for year-over-year calculations
- Both Series and DataFrame inputs
"""

import pandas as pd
import numpy as np
from typing import Union, Callable, Dict


def lin(series: pd.Series) -> pd.Series:
    """Levels - no transformation (returns original series)."""
    return series


def chg(series: pd.Series) -> pd.Series:
    """Change from previous period."""
    return series.diff()


def ch1(series: pd.Series) -> pd.Series:
    """Change from year ago (12 periods for monthly, 4 for quarterly)."""
    if pd.infer_freq(series.index) in ['M', 'MS']:
        return series.diff(12)
    elif pd.infer_freq(series.index) in ['Q', 'QS']:
        return series.diff(4)
    else:
        # For annual or other frequencies, default to 1 period
        return series.diff(1)


def pch(series: pd.Series) -> pd.Series:
    """Percent change from previous period."""
    return series.pct_change() * 100


def pc1(series: pd.Series) -> pd.Series:
    """Percent change from year ago."""
    if pd.infer_freq(series.index) in ['M', 'MS']:
        return series.pct_change(12) * 100
    elif pd.infer_freq(series.index) in ['Q', 'QS']:
        return series.pct_change(4) * 100
    else:
        return series.pct_change(1) * 100


def pca(series: pd.Series) -> pd.Series:
    """Compounded annual rate of change."""
    freq = pd.infer_freq(series.index)
    if freq in ['M', 'MS']:
        periods_per_year = 12
    elif freq in ['Q', 'QS']:
        periods_per_year = 4
    elif freq in ['D']:
        periods_per_year = 252  # Trading days
    else:
        periods_per_year = 1
    
    pct_change = series.pct_change()
    return ((1 + pct_change) ** periods_per_year - 1) * 100


def cch(series: pd.Series) -> pd.Series:
    """Continuously compounded rate of change."""
    return series.pct_change().apply(lambda x: np.log(1 + x) * 100 if pd.notna(x) else np.nan)


def cca(series: pd.Series) -> pd.Series:
    """Continuously compounded annual rate of change."""
    freq = pd.infer_freq(series.index)
    if freq in ['M', 'MS']:
        periods_per_year = 12
    elif freq in ['Q', 'QS']:
        periods_per_year = 4
    elif freq in ['D']:
        periods_per_year = 252
    else:
        periods_per_year = 1
    
    cc_change = series.pct_change().apply(lambda x: np.log(1 + x) if pd.notna(x) else np.nan)
    return cc_change * periods_per_year * 100


def log(series: pd.Series) -> pd.Series:
    """Natural log transformation."""
    return series.apply(lambda x: np.log(x) if x > 0 else np.nan)


# Dictionary mapping FRED unit codes to transformation functions
TRANSFORMATIONS: Dict[str, Callable[[pd.Series], pd.Series]] = {
    'lin': lin,  # Levels (no transformation)
    'chg': chg,  # Change
    'ch1': ch1,  # Change from year ago
    'pch': pch,  # Percent change
    'pc1': pc1,  # Percent change from year ago
    'pca': pca,  # Compounded annual rate
    'cch': cch,  # Continuously compounded change
    'cca': cca,  # Continuously compounded annual rate
    'log': log   # Natural log
}


def apply_transformation(
    data: Union[pd.Series, pd.DataFrame], 
    units: str = 'lin'
) -> Union[pd.Series, pd.DataFrame]:
    """
    Apply FRED-compatible transformation to data.
    
    Parameters
    ----------
    data : pd.Series or pd.DataFrame
        The data to transform
    units : str
        FRED-compatible unit code:
        - 'lin': Levels (no transformation)
        - 'chg': Change from previous period
        - 'ch1': Change from year ago
        - 'pch': Percent change
        - 'pc1': Percent change from year ago
        - 'pca': Compounded annual rate
        - 'cch': Continuously compounded change
        - 'cca': Continuously compounded annual rate
        - 'log': Natural log
        
    Returns
    -------
    pd.Series or pd.DataFrame
        Transformed data
        
    Raises
    ------
    ValueError
        If units code is not recognized
    """
    if units not in TRANSFORMATIONS:
        from .exceptions import InvalidParameterError
        raise InvalidParameterError(
            'units', 
            units, 
            list(TRANSFORMATIONS.keys())
        )
    
    transform_func = TRANSFORMATIONS[units]
    
    if isinstance(data, pd.DataFrame):
        # Apply transformation to each column
        return data.apply(transform_func)
    else:
        return transform_func(data)


def get_transformation_description(units: str) -> str:
    """Get human-readable description of a transformation."""
    descriptions = {
        'lin': 'Levels (no transformation)',
        'chg': 'Change from previous period',
        'ch1': 'Change from year ago',
        'pch': 'Percent change',
        'pc1': 'Percent change from year ago',
        'pca': 'Compounded annual rate',
        'cch': 'Continuously compounded change',
        'cca': 'Continuously compounded annual rate',
        'log': 'Natural log'
    }
    return descriptions.get(units, f'Unknown transformation: {units}')