"""
Comprehensive search functionality for all BOJ data
"""

import re
from typing import Dict, List, Optional, Tuple, Union
from urllib.parse import quote, urlencode

import pandas as pd
import requests
from bs4 import BeautifulSoup

from .exceptions import BOJDataError


class BOJComprehensiveSearch:
    """Advanced search capabilities for all BOJ statistical data"""
    
    BASE_URL = "https://www.stat-search.boj.or.jp"
    
    # All data categories with their codes and search patterns
    CATEGORIES = {
        "interest_rates": {
            "name": "Interest Rates on Deposits and Loans",
            "code": "IR",
            "series_prefix": "IR",
            "subcategories": ["Deposit Rates", "Loan Rates", "Interest Rate Spreads"],
        },
        "financial_markets": {
            "name": "Financial Markets",
            "code": "FM",
            "series_prefix": "FM",
            "subcategories": ["Stock Market", "Bond Market", "Foreign Exchange", "Derivatives"],
        },
        "payment_settlement": {
            "name": "Payment and Settlement",
            "code": "PS",
            "series_prefix": "PS",
            "subcategories": ["BOJ-NET", "Zengin System", "Electronic Money"],
        },
        "money_deposits": {
            "name": "Money and Deposits",
            "code": "MD",
            "series_prefix": "MD|BS",  # Also includes BS (Balance Sheet) series
            "subcategories": ["Monetary Base", "Money Stock", "Deposits by Type"],
        },
        "loans": {
            "name": "Loans",
            "code": "LN",
            "series_prefix": "LN",
            "subcategories": ["Bank Lending", "Loans by Industry", "Non-Performing Loans"],
        },
        "balance_sheets": {
            "name": "Balance Sheets",
            "code": "BS",
            "series_prefix": "BS",
            "subcategories": ["BOJ Accounts", "Banking Accounts", "Other Financial Institutions"],
        },
        "flow_of_funds": {
            "name": "Flow of Funds",
            "code": "FF",
            "series_prefix": "FF",
            "subcategories": ["Financial Assets and Liabilities", "Sectoral Accounts", "Financial Transactions"],
        },
        "other_boj": {
            "name": "Other Bank of Japan Statistics",
            "code": "OT",
            "series_prefix": "OT",
            "subcategories": ["Research Papers", "Special Surveys", "Historical Statistics"],
        },
        "tankan": {
            "name": "TANKAN",
            "code": "TK",
            "series_prefix": "TK",
            "subcategories": ["Business Conditions", "Forecast", "Industry Analysis"],
        },
        "prices": {
            "name": "Prices",
            "code": "PR",
            "series_prefix": "PR|CGPI",
            "subcategories": ["Consumer Prices", "Producer Prices", "Service Prices", "Import/Export Prices"],
        },
        "public_finance": {
            "name": "Public Finance",
            "code": "PF",
            "series_prefix": "PF",
            "subcategories": ["Government Debt", "Fiscal Balance", "Tax Revenue"],
        },
        "balance_of_payments": {
            "name": "Balance of Payments",
            "code": "BP",
            "series_prefix": "BP",
            "subcategories": ["Current Account", "Financial Account", "International Investment Position"],
        },
        "others": {
            "name": "Others",
            "code": "OT",
            "series_prefix": "OT",
            "subcategories": ["Regional Statistics", "Miscellaneous"],
        },
    }
    
    def __init__(self):
        """Initialize comprehensive search"""
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; bojdata/1.0)"
        })
    
    def search_all_categories(
        self,
        keyword: str,
        categories: Optional[List[str]] = None,
        limit: int = 100,
    ) -> pd.DataFrame:
        """
        Search across all or specified categories.
        
        Parameters
        ----------
        keyword : str
            Search keyword
        categories : list of str, optional
            Specific categories to search. If None, searches all.
        limit : int, default 100
            Maximum results to return
        
        Returns
        -------
        pd.DataFrame
            Search results with series info
        """
        results = []
        
        search_categories = categories or list(self.CATEGORIES.keys())
        
        for category in search_categories:
            try:
                cat_results = self._search_category(category, keyword)
                results.extend(cat_results)
            except Exception as e:
                print(f"Error searching {category}: {e}")
        
        # Convert to DataFrame
        df = pd.DataFrame(results)
        
        # Remove duplicates and limit
        if not df.empty:
            df = df.drop_duplicates(subset=["series_code"])
            df = df.head(limit)
        
        return df
    
    def _search_category(self, category: str, keyword: str) -> List[Dict]:
        """Search within a specific category using series patterns"""
        if category not in self.CATEGORIES:
            raise BOJDataError(f"Unknown category: {category}")
        
        cat_info = self.CATEGORIES[category]
        results = []
        
        # Generate potential series codes based on category
        # BOJ series codes follow patterns like IR01, FM02, etc.
        series_prefixes = cat_info.get("series_prefix", cat_info["code"]).split("|")
        
        # Common BOJ series patterns - simulate search results
        # In a real implementation, this would query the actual BOJ search
        sample_patterns = {
            "interest_rates": [
                ("IR01", "Uncollateralized Overnight Call Rate"),
                ("IR02", "Basic Loan Rate"),
                ("IR03", "Average Interest Rates on Deposits"),
            ],
            "financial_markets": [
                ("FM01", "Foreign Exchange Rates"),
                ("FM02", "Stock Market Indices"),
                ("FM08", "Government Bond Yields"),
            ],
            "money_deposits": [
                ("BS01'MABJMTA", "Monetary Base (Average Amounts Outstanding)"),
                ("MD02", "Money Stock M2"),
                ("MD03", "Money Stock M3"),
            ],
            "balance_of_payments": [
                ("BP01", "Balance of Payments"),
                ("BP02", "International Investment Position"),
            ],
            "prices": [
                ("CGPI", "Corporate Goods Price Index"),
                ("PR01", "Services Producer Price Index"),
            ],
        }
        
        # Search in predefined patterns
        if category in sample_patterns:
            for code, name in sample_patterns[category]:
                if keyword.lower() in name.lower():
                    results.append({
                        "series_code": code,
                        "name": name,
                        "category": cat_info["name"],
                        "category_key": category,
                    })
        
        return results
    
    def _extract_series_info(self, link_element, category: str) -> Optional[Dict]:
        """Extract series information from a link element"""
        try:
            # Get series code from URL or text
            href = link_element.get("href", "")
            text = link_element.text.strip()
            
            # Try to extract series code
            code_match = re.search(r'([A-Z]{2}\d{2}[A-Z0-9\']*)', text)
            if not code_match:
                code_match = re.search(r'hdncode=([^&]+)', href)
            
            if code_match:
                series_code = code_match.group(1)
            else:
                return None
            
            return {
                "series_code": series_code,
                "name": text,
                "category": self.CATEGORIES[category]["name"],
                "category_key": category,
                "url": f"{self.BASE_URL}{href}" if href else None,
            }
        except:
            return None
    
    def get_series_by_exact_code(self, series_code: str) -> pd.DataFrame:
        """
        Get series data by exact code match.
        
        Parameters
        ----------
        series_code : str
            Exact series code (e.g., "BS01'MABJMTA")
        
        Returns
        -------
        pd.DataFrame
            Series data
        """
        # Use direct search URL
        params = {
            "cgi": "$nme_r030_en",
            "hdncode": series_code,
            "chkfrq": "MM",
            "rdoheader": "SIMPLE",
            "rdodelimitar": "COMMA",
        }
        
        url = f"{self.BASE_URL}/ssi/cgi-bin/famecgi2"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        # Find CSV download link
        soup = BeautifulSoup(response.content, "html.parser")
        csv_links = soup.select("a[href*=csv]")
        
        if not csv_links:
            raise BOJDataError(f"No data found for series: {series_code}")
        
        # Download CSV
        csv_url = f"{self.BASE_URL}{csv_links[0]['href']}"
        df = pd.read_csv(csv_url)
        
        return df
    
    def get_category_tree(self) -> Dict:
        """
        Get the complete category tree structure.
        
        Returns
        -------
        dict
            Hierarchical category structure
        """
        tree = {}
        
        for key, info in self.CATEGORIES.items():
            # Get subcategories with series counts
            subcats = self._get_subcategory_details(key)
            
            tree[key] = {
                "name": info["name"],
                "subcategories": subcats,
                "total_series": sum(s.get("series_count", 0) for s in subcats),
            }
        
        return tree
    
    def _get_subcategory_details(self, category: str) -> List[Dict]:
        """Get detailed subcategory information"""
        # This would parse the category page for subcategory details
        # Placeholder for now
        cat_info = self.CATEGORIES.get(category, {})
        subcats = []
        
        for subcat in cat_info.get("subcategories", []):
            subcats.append({
                "name": subcat,
                "series_count": 0,  # Would be populated from actual parsing
            })
        
        return subcats
    
    def discover_all_series_codes(self) -> pd.DataFrame:
        """
        Discover all available series codes across BOJ.
        
        Returns
        -------
        pd.DataFrame
            Complete list of series codes with metadata
        """
        all_series = []
        
        for category in self.CATEGORIES:
            print(f"Discovering series in {category}...")
            try:
                series_list = self._discover_category_series(category)
                all_series.extend(series_list)
            except Exception as e:
                print(f"Error in {category}: {e}")
        
        # Create DataFrame
        df = pd.DataFrame(all_series)
        
        # Add discovery timestamp
        df["discovered_at"] = pd.Timestamp.now()
        
        return df
    
    def _discover_category_series(self, category: str) -> List[Dict]:
        """Discover all series in a category"""
        cat_info = self.CATEGORIES[category]
        url = f"{self.BASE_URL}{cat_info['path']}"
        
        response = self.session.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        series_list = []
        
        # Find all series codes in the page
        # Look for patterns like IR01, FM02, etc.
        text_content = soup.get_text()
        
        # Pattern for BOJ series codes
        pattern = r'\b([A-Z]{2,3}\d{2}[A-Z0-9\'\-]*)\b'
        matches = re.findall(pattern, text_content)
        
        # Also look for links with series codes
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            if "hdncode=" in href:
                code_match = re.search(r'hdncode=([^&]+)', href)
                if code_match:
                    matches.append(code_match.group(1))
        
        # Deduplicate and create series info
        seen = set()
        for code in matches:
            if code not in seen and len(code) >= 4:  # Valid series codes
                seen.add(code)
                series_list.append({
                    "series_code": code,
                    "category": cat_info["name"],
                    "category_key": category,
                })
        
        return series_list
    
    def build_series_catalog(self, save_path: Optional[str] = None) -> pd.DataFrame:
        """
        Build a comprehensive catalog of all BOJ series.
        
        Parameters
        ----------
        save_path : str, optional
            Path to save the catalog
        
        Returns
        -------
        pd.DataFrame
            Complete series catalog
        """
        print("Building comprehensive BOJ series catalog...")
        
        # Discover all series
        catalog = self.discover_all_series_codes()
        
        # Enrich with metadata (this would involve fetching details for each series)
        print(f"Found {len(catalog)} unique series codes")
        
        # Save if requested
        if save_path:
            catalog.to_csv(save_path, index=False)
            print(f"Catalog saved to {save_path}")
        
        return catalog