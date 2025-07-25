"""
Test mode with mock data for development and testing
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

import numpy as np
import pandas as pd

from .exceptions import SeriesNotFoundError


class MockDataGenerator:
    """Generate realistic mock data for testing"""
    
    def __init__(self):
        self.seed = 42
        np.random.seed(self.seed)
        
        # Mock series definitions
        self.mock_series = {
            "BS01'MABJMTA": {
                "name": "Monetary Base (Average Amounts Outstanding)",
                "frequency": "Monthly",
                "category": "Money and Deposits",
                "units": "100 Million Yen",
                "base_value": 5000000,
                "trend": 0.002,
                "volatility": 0.01,
            },
            "IR01": {
                "name": "Uncollateralized Overnight Call Rate",
                "frequency": "Daily",
                "category": "Interest Rates",
                "units": "Percent",
                "base_value": 0.1,
                "trend": 0.0,
                "volatility": 0.05,
            },
            "FM01": {
                "name": "Foreign Exchange Rates (USD/JPY)",
                "frequency": "Daily",
                "category": "Financial Markets",
                "units": "Yen per Dollar",
                "base_value": 110,
                "trend": 0.0001,
                "volatility": 0.02,
            },
            "PR01'IUQCP001": {
                "name": "Consumer Price Index",
                "frequency": "Monthly",
                "category": "Prices",
                "units": "Index (2020=100)",
                "base_value": 100,
                "trend": 0.001,
                "volatility": 0.005,
            },
            "TK01": {
                "name": "Business Conditions DI (Large Manufacturers)",
                "frequency": "Quarterly",
                "category": "TANKAN",
                "units": "DI (%points)",
                "base_value": 10,
                "trend": 0.0,
                "volatility": 0.2,
            },
            "TEST_SERIES": {
                "name": "Test Series for Development",
                "frequency": "Monthly",
                "category": "Test Data",
                "units": "Test Units",
                "base_value": 1000,
                "trend": 0.01,
                "volatility": 0.05,
            },
        }
    
    def generate_series(
        self,
        series_id: str,
        start_date: Optional[Union[str, pd.Timestamp]] = None,
        end_date: Optional[Union[str, pd.Timestamp]] = None,
        periods: Optional[int] = None,
    ) -> pd.DataFrame:
        """Generate mock time series data"""
        
        if series_id not in self.mock_series:
            # Check if it's a valid but not mocked series
            from .utils import validate_series_code
            if validate_series_code(series_id):
                # Create a generic mock series
                series_info = {
                    "name": f"Mock Series {series_id}",
                    "frequency": "Monthly",
                    "category": "Mock Data",
                    "units": "Units",
                    "base_value": 100,
                    "trend": 0.001,
                    "volatility": 0.02,
                }
            else:
                raise SeriesNotFoundError(f"Mock series '{series_id}' not found in test data")
        else:
            series_info = self.mock_series[series_id]
        
        # Determine date range
        if start_date is None:
            start_date = pd.Timestamp("2020-01-01")
        else:
            start_date = pd.Timestamp(start_date)
            
        if end_date is None:
            end_date = pd.Timestamp.now()
        else:
            end_date = pd.Timestamp(end_date)
        
        # Generate dates based on frequency
        freq_map = {
            "Daily": "D",
            "Monthly": "MS",  # Month start
            "Quarterly": "QS",  # Quarter start
            "Yearly": "YS",  # Year start
        }
        
        freq = freq_map.get(series_info["frequency"], "MS")
        dates = pd.date_range(start=start_date, end=end_date, freq=freq)
        
        if periods and len(dates) > periods:
            dates = dates[-periods:]
        
        # Generate data with trend and random walk
        n = len(dates)
        base = series_info["base_value"]
        trend = series_info["trend"]
        vol = series_info["volatility"]
        
        # Create trend component
        trend_component = base * (1 + trend) ** np.arange(n)
        
        # Add random walk component - use deterministic seed based on series and dates
        # This ensures same series/date range always produces same data
        seed_string = f"{series_id}_{start_date}_{end_date}_{n}"
        seed_value = hash(seed_string) % (2**32)
        rng = np.random.RandomState(seed_value)
        random_shocks = rng.normal(0, vol, n)
        random_walk = np.cumsum(random_shocks)
        
        # Combine components
        values = trend_component * (1 + random_walk)
        
        # Add some seasonality for monthly/quarterly data
        if series_info["frequency"] in ["Monthly", "Quarterly"]:
            seasonal_period = 12 if series_info["frequency"] == "Monthly" else 4
            seasonal_component = 0.05 * np.sin(2 * np.pi * np.arange(n) / seasonal_period)
            values = values * (1 + seasonal_component)
        
        # Create DataFrame
        df = pd.DataFrame({
            series_id: values
        }, index=dates)
        
        df.index.name = "Date"
        
        # Sort by date descending (like BOJ)
        df = df.sort_index(ascending=False)
        
        return df
    
    def get_series_metadata(self, series_id: str) -> Dict[str, any]:
        """Get mock metadata for a series"""
        
        if series_id not in self.mock_series:
            from .utils import validate_series_code
            if validate_series_code(series_id):
                return {
                    "id": series_id,
                    "title": f"Mock Series {series_id}",
                    "frequency": "Monthly",
                    "units": "Units",
                    "seasonal_adjustment": "Not Seasonally Adjusted",
                    "notes": f"This is mock data for series {series_id}",
                    "category": "Mock Data",
                }
            else:
                raise SeriesNotFoundError(f"Mock series '{series_id}' not found")
        
        series_info = self.mock_series[series_id]
        
        return {
            "id": series_id,
            "title": series_info["name"],
            "frequency": series_info["frequency"],
            "units": series_info["units"],
            "seasonal_adjustment": "Not Seasonally Adjusted",
            "notes": f"Mock data for {series_info['name']}",
            "category": series_info["category"],
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "observation_start": "2020-01-01",
            "observation_end": datetime.now().strftime("%Y-%m-%d"),
            "popularity": 50,
            "tags": [series_info["category"].lower(), "mock", "test"],
        }


# Global test mode flag
_TEST_MODE = os.environ.get("BOJ_TEST_MODE", "").lower() in ("true", "1", "yes")


def is_test_mode() -> bool:
    """Check if test mode is enabled"""
    return _TEST_MODE


def enable_test_mode():
    """Enable test mode"""
    global _TEST_MODE
    _TEST_MODE = True


def disable_test_mode():
    """Disable test mode"""
    global _TEST_MODE
    _TEST_MODE = False


# Global mock data generator
_mock_generator = MockDataGenerator()


def get_mock_data(
    series_id: str,
    start_date: Optional[Union[str, pd.Timestamp]] = None,
    end_date: Optional[Union[str, pd.Timestamp]] = None,
) -> pd.DataFrame:
    """Get mock data for a series"""
    return _mock_generator.generate_series(series_id, start_date, end_date)


def get_mock_metadata(series_id: str) -> Dict[str, any]:
    """Get mock metadata for a series"""
    return _mock_generator.get_series_metadata(series_id)