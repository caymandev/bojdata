"""
Test FRED to BOJ series mapping functionality
"""

import pytest
from bojdata.fred_mapping import (
    get_boj_series_from_fred,
    get_fred_series_from_boj,
    suggest_boj_alternative,
    get_all_fred_mappings,
    FRED_TO_BOJ_MAPPING
)


class TestFREDMapping:
    """Test FRED to BOJ series code mapping"""
    
    def test_known_fred_to_boj_mappings(self):
        """Test mapping of known FRED series to BOJ"""
        mappings = [
            ("DEXJPUS", "FM01"),  # USD/JPY
            ("NIKKEI225", "FM03"),  # Nikkei
            ("BOGMBASE", "BS01'MABJMTA"),  # Monetary Base
            ("MYAGM1JPM189S", "MD01"),  # M1
            ("MYAGM2JPM189S", "MD02"),  # M2
        ]
        
        for fred_code, expected_boj in mappings:
            assert get_boj_series_from_fred(fred_code) == expected_boj
    
    def test_unknown_fred_series_returns_none(self):
        """Test that unknown FRED series return None"""
        assert get_boj_series_from_fred("UNKNOWN_SERIES") is None
        assert get_boj_series_from_fred("DGS10") is None  # US Treasury
    
    def test_case_insensitive_fred_lookup(self):
        """Test that FRED lookup is case-insensitive"""
        assert get_boj_series_from_fred("dexjpus") == "FM01"
        assert get_boj_series_from_fred("DEXJPUS") == "FM01"
        assert get_boj_series_from_fred("DexJpUs") == "FM01"
    
    def test_reverse_mapping_boj_to_fred(self):
        """Test reverse mapping from BOJ to FRED"""
        assert get_fred_series_from_boj("FM01") == "DEXJPUS"
        assert get_fred_series_from_boj("FM03") == "NIKKEI225"
        assert get_fred_series_from_boj("BS01'MABJMTA") == "BOGMBASE"
    
    def test_unmapped_boj_series_returns_none(self):
        """Test that unmapped BOJ series return None"""
        assert get_fred_series_from_boj("IR99") is None
        assert get_fred_series_from_boj("UNKNOWN") is None


class TestFREDAlternativeSuggestions:
    """Test FRED alternative suggestions"""
    
    def test_direct_mapping_suggestions(self):
        """Test suggestions for directly mapped series"""
        suggestion = suggest_boj_alternative("DEXJPUS")
        assert "FM01" in suggestion
        assert "exchange rate" in suggestion.lower()
        
        suggestion = suggest_boj_alternative("NIKKEI225")
        assert "FM03" in suggestion
        assert "nikkei" in suggestion.lower()
    
    def test_partial_match_suggestions(self):
        """Test suggestions based on partial matches"""
        # Exchange rate related
        suggestion = suggest_boj_alternative("USDJPY")
        assert "FM01" in suggestion
        assert "exchange" in suggestion.lower()
        
        # CPI/Inflation related
        suggestion = suggest_boj_alternative("JPCPIALLMINMEI")
        assert "PR01" in suggestion
        assert "price" in suggestion.lower() or "cpi" in suggestion.lower()
        
        # Interest rate related
        suggestion = suggest_boj_alternative("JPNINTEREST")
        assert "IR01" in suggestion or "IR02" in suggestion
        assert "interest" in suggestion.lower()
    
    def test_gdp_special_case(self):
        """Test special message for GDP data"""
        suggestion = suggest_boj_alternative("JPNGDP")
        assert "cabinet office" in suggestion.lower() or "doesn't directly provide" in suggestion.lower()
    
    def test_generic_suggestion_for_unknown(self):
        """Test generic suggestion for completely unknown series"""
        suggestion = suggest_boj_alternative("COMPLETELY_UNKNOWN_SERIES")
        assert "search_series" in suggestion or "list_valid_series_codes" in suggestion


class TestFREDMappingMetadata:
    """Test FRED mapping metadata functions"""
    
    def test_get_all_mappings_structure(self):
        """Test structure of all mappings response"""
        mappings = get_all_fred_mappings()
        
        assert isinstance(mappings, dict)
        assert len(mappings) > 0
        
        # Check a known mapping
        assert "DEXJPUS" in mappings
        dexjpus_info = mappings["DEXJPUS"]
        assert dexjpus_info["boj_code"] == "FM01"
        assert "Exchange Rate" in dexjpus_info["description"]
        assert dexjpus_info["available"] == True
    
    def test_unavailable_series_marked(self):
        """Test that unavailable series are marked correctly"""
        mappings = get_all_fred_mappings()
        
        # GDP should be marked as unavailable
        if "JPNRGDPEXP" in mappings:
            assert mappings["JPNRGDPEXP"]["available"] == False
            assert mappings["JPNRGDPEXP"]["boj_code"] is None
    
    def test_all_mapped_series_have_descriptions(self):
        """Test that all mapped series have descriptions"""
        mappings = get_all_fred_mappings()
        
        for fred_code, info in mappings.items():
            assert "description" in info
            assert isinstance(info["description"], str)
            # Available series should have non-empty descriptions
            if info["available"]:
                assert len(info["description"]) > 0