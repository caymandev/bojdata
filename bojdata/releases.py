"""
BOJ Release Calendar integration.

This module provides functionality to scrape and work with BOJ's statistical
release calendar, allowing users to track when data series are updated.
"""

import re
from datetime import datetime
from typing import List, Dict, Optional, Union, Any
import pandas as pd
import requests
from bs4 import BeautifulSoup

from .exceptions import BOJDataError


class BOJReleaseCalendar:
    """
    Access Bank of Japan's statistical release calendar.
    
    This class scrapes BOJ's release schedule to provide information about
    when different data series are released and updated.
    
    Examples
    --------
    >>> from bojdata.releases import BOJReleaseCalendar
    >>> calendar = BOJReleaseCalendar()
    >>> 
    >>> # Get all releases
    >>> releases = calendar.get_releases()
    >>> 
    >>> # Get releases for specific month
    >>> jan_releases = calendar.get_releases_for_month(2024, 1)
    >>> 
    >>> # Find release dates for a specific series type
    >>> tankan_dates = calendar.get_release_dates('TANKAN')
    """
    
    BASE_URL = "https://www.boj.or.jp/en/statistics/outline/release/index.htm"
    CALENDAR_URL = "https://www.boj.or.jp/en/statistics/outline/release/release_{year}.htm"
    
    def __init__(self):
        """Initialize the release calendar."""
        self._releases_cache = None
    
    def get_releases(self, year: Optional[int] = None, force_refresh: bool = False) -> pd.DataFrame:
        """
        Get all scheduled releases for a given year.
        
        Parameters
        ----------
        year : int, optional
            Year to get releases for (default: current year)
        force_refresh : bool, default False
            Force refresh of cached data
            
        Returns
        -------
        pd.DataFrame
            DataFrame with columns: date, series_name, frequency, time
            
        Examples
        --------
        >>> calendar = BOJReleaseCalendar()
        >>> releases = calendar.get_releases(2024)
        >>> print(releases.head())
        """
        if year is None:
            year = datetime.now().year
        
        # Check cache
        if not force_refresh and self._releases_cache is not None:
            cached_year = self._releases_cache.get('year')
            if cached_year == year:
                return self._releases_cache['data']
        
        # Scrape release calendar
        url = self.CALENDAR_URL.format(year=year)
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            # Try base URL as fallback
            try:
                response = requests.get(self.BASE_URL, timeout=30)
                response.raise_for_status()
            except requests.RequestException:
                raise BOJDataError(f"Failed to fetch release calendar: {e}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Parse release schedule
        releases = self._parse_release_schedule(soup, year)
        
        # Convert to DataFrame
        df = pd.DataFrame(releases)
        
        # Sort by date
        if not df.empty and 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
        
        # Cache results
        self._releases_cache = {'year': year, 'data': df}
        
        return df
    
    def _parse_release_schedule(self, soup: BeautifulSoup, year: int) -> List[Dict[str, Any]]:
        """Parse release schedule from BOJ webpage."""
        releases = []
        
        # Look for release schedule table
        tables = soup.find_all('table')
        
        for table in tables:
            # Check if this is a release schedule table
            headers = table.find_all('th')
            if not headers:
                continue
            
            header_text = ' '.join([h.get_text().strip() for h in headers])
            if 'release' not in header_text.lower() and 'schedule' not in header_text.lower():
                continue
            
            # Parse table rows
            rows = table.find_all('tr')
            
            for row in rows[1:]:  # Skip header row
                cells = row.find_all(['td', 'th'])
                if len(cells) < 2:
                    continue
                
                # Extract date and series info
                date_text = cells[0].get_text().strip()
                series_text = cells[1].get_text().strip()
                
                # Parse date
                parsed_date = self._parse_date(date_text, year)
                if not parsed_date:
                    continue
                
                # Extract series name and frequency
                series_info = self._parse_series_info(series_text)
                
                releases.append({
                    'date': parsed_date,
                    'series_name': series_info['name'],
                    'frequency': series_info['frequency'],
                    'time': series_info.get('time', 'TBD'),
                    'raw_text': series_text
                })
        
        # If no table found, try to parse from text
        if not releases:
            releases = self._parse_releases_from_text(soup, year)
        
        return releases
    
    def _parse_date(self, date_text: str, year: int) -> Optional[str]:
        """Parse date from various formats."""
        # Remove extra whitespace
        date_text = ' '.join(date_text.split())
        
        # Common patterns
        patterns = [
            r'(\d{1,2})[/-](\d{1,2})',  # MM-DD or MM/DD
            r'(\w+)\s+(\d{1,2})',        # Month DD
            r'(\d{1,2})\s+(\w+)',        # DD Month
        ]
        
        for pattern in patterns:
            match = re.search(pattern, date_text)
            if match:
                try:
                    # Try to parse the date
                    if pattern == patterns[0]:
                        month, day = match.groups()
                        return f"{year}-{int(month):02d}-{int(day):02d}"
                    else:
                        # Parse month name
                        month_str = match.group(1) if match.group(1).isalpha() else match.group(2)
                        day_str = match.group(2) if match.group(1).isalpha() else match.group(1)
                        
                        # Convert month name to number
                        month_num = self._month_to_number(month_str)
                        if month_num:
                            return f"{year}-{month_num:02d}-{int(day_str):02d}"
                except:
                    continue
        
        return None
    
    def _month_to_number(self, month_str: str) -> Optional[int]:
        """Convert month name to number."""
        months = {
            'jan': 1, 'january': 1,
            'feb': 2, 'february': 2,
            'mar': 3, 'march': 3,
            'apr': 4, 'april': 4,
            'may': 5,
            'jun': 6, 'june': 6,
            'jul': 7, 'july': 7,
            'aug': 8, 'august': 8,
            'sep': 9, 'september': 9,
            'oct': 10, 'october': 10,
            'nov': 11, 'november': 11,
            'dec': 12, 'december': 12
        }
        
        month_lower = month_str.lower()
        for key, value in months.items():
            if key.startswith(month_lower[:3]):
                return value
        
        return None
    
    def _parse_series_info(self, text: str) -> Dict[str, str]:
        """Extract series name and frequency from text."""
        info = {
            'name': text,
            'frequency': 'Unknown'
        }
        
        # Clean text
        text = ' '.join(text.split())
        
        # Extract frequency if mentioned
        freq_patterns = {
            'Monthly': ['monthly', 'month'],
            'Quarterly': ['quarterly', 'quarter'],
            'Annual': ['annual', 'yearly', 'year'],
            'Weekly': ['weekly', 'week'],
            'Daily': ['daily', 'day']
        }
        
        text_lower = text.lower()
        for freq, patterns in freq_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    info['frequency'] = freq
                    break
        
        # Extract time if mentioned
        time_match = re.search(r'(\d{1,2}:\d{2})', text)
        if time_match:
            info['time'] = time_match.group(1)
        
        # Clean up series name
        # Remove frequency and time info
        name = text
        for pattern in ['monthly', 'quarterly', 'annual', 'weekly', 'daily']:
            name = re.sub(f'\\b{pattern}\\b', '', name, flags=re.IGNORECASE)
        
        name = re.sub(r'\d{1,2}:\d{2}', '', name)
        name = ' '.join(name.split())
        
        info['name'] = name.strip()
        
        return info
    
    def _parse_releases_from_text(self, soup: BeautifulSoup, year: int) -> List[Dict[str, Any]]:
        """Fallback parser for release information from general text."""
        releases = []
        
        # Find all text that might contain release info
        text_blocks = soup.find_all(['p', 'div', 'li'])
        
        for block in text_blocks:
            text = block.get_text()
            
            # Look for date patterns followed by series names
            date_pattern = r'(\d{1,2}[/-]\d{1,2}|\w+\s+\d{1,2}|\d{1,2}\s+\w+)'
            series_pattern = r'(TANKAN|Flow of Funds|Money Stock|Price|Balance of Payments|Interest Rate)'
            
            combined_pattern = f'{date_pattern}.*?{series_pattern}'
            
            matches = re.finditer(combined_pattern, text, re.IGNORECASE)
            
            for match in matches:
                date_text = match.group(1)
                series_name = match.group(2)
                
                parsed_date = self._parse_date(date_text, year)
                if parsed_date:
                    releases.append({
                        'date': parsed_date,
                        'series_name': series_name,
                        'frequency': 'Unknown',
                        'time': 'TBD',
                        'raw_text': match.group(0)
                    })
        
        return releases
    
    def get_releases_for_month(self, year: int, month: int) -> pd.DataFrame:
        """
        Get releases for a specific month.
        
        Parameters
        ----------
        year : int
            Year
        month : int
            Month (1-12)
            
        Returns
        -------
        pd.DataFrame
            Releases for the specified month
        """
        # Get all releases for the year
        all_releases = self.get_releases(year)
        
        if all_releases.empty:
            return pd.DataFrame()
        
        # Filter by month
        mask = (all_releases['date'].dt.year == year) & (all_releases['date'].dt.month == month)
        return all_releases[mask].copy()
    
    def get_release_dates(self, series_name: str, year: Optional[int] = None) -> pd.DataFrame:
        """
        Get release dates for a specific series.
        
        Parameters
        ----------
        series_name : str
            Name or partial name of the series (e.g., 'TANKAN', 'Money Stock')
        year : int, optional
            Year to search (default: current year)
            
        Returns
        -------
        pd.DataFrame
            Release dates for the series
            
        Examples
        --------
        >>> calendar = BOJReleaseCalendar()
        >>> tankan_dates = calendar.get_release_dates('TANKAN')
        """
        releases = self.get_releases(year)
        
        if releases.empty:
            return pd.DataFrame()
        
        # Filter by series name (case-insensitive partial match)
        series_lower = series_name.lower()
        mask = releases['series_name'].str.lower().str.contains(series_lower, na=False)
        
        return releases[mask].copy()
    
    def get_next_release(self, series_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the next scheduled release for a series.
        
        Parameters
        ----------
        series_name : str
            Name of the series
            
        Returns
        -------
        dict or None
            Next release information or None if not found
        """
        # Get current year releases
        current_year = datetime.now().year
        releases = self.get_release_dates(series_name, current_year)
        
        if releases.empty:
            # Try next year
            releases = self.get_release_dates(series_name, current_year + 1)
        
        if releases.empty:
            return None
        
        # Find next future release
        today = pd.Timestamp.now()
        future_releases = releases[releases['date'] >= today]
        
        if future_releases.empty:
            return None
        
        # Return the next release
        next_release = future_releases.iloc[0]
        return next_release.to_dict()
    
    def to_ical(self, year: Optional[int] = None, output_file: Optional[str] = None) -> str:
        """
        Export release calendar to iCal format.
        
        Parameters
        ----------
        year : int, optional
            Year to export
        output_file : str, optional
            File path to save the calendar
            
        Returns
        -------
        str
            iCal format string
        """
        releases = self.get_releases(year)
        
        if releases.empty:
            return ""
        
        # Build iCal content
        ical_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//BOJ Data Release Calendar//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "X-WR-CALNAME:BOJ Data Releases",
            "X-WR-CALDESC:Bank of Japan Statistical Data Release Schedule"
        ]
        
        for _, release in releases.iterrows():
            date_str = release['date'].strftime('%Y%m%d')
            
            ical_lines.extend([
                "BEGIN:VEVENT",
                f"DTSTART;VALUE=DATE:{date_str}",
                f"SUMMARY:BOJ: {release['series_name']}",
                f"DESCRIPTION:Frequency: {release['frequency']}\\nTime: {release['time']}",
                f"UID:{date_str}-{release['series_name'].replace(' ', '')}@boj.or.jp",
                "END:VEVENT"
            ])
        
        ical_lines.append("END:VCALENDAR")
        
        ical_content = '\n'.join(ical_lines)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(ical_content)
        
        return ical_content


# Convenience function for API
def get_releases(year: Optional[int] = None) -> pd.DataFrame:
    """
    Get BOJ release calendar for a given year.
    
    Parameters
    ----------
    year : int, optional
        Year (default: current year)
        
    Returns
    -------
    pd.DataFrame
        Release schedule
    """
    calendar = BOJReleaseCalendar()
    return calendar.get_releases(year)