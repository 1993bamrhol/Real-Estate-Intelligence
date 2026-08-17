"""
Tests for Riyadh Map Viewer Feature
===================================

Comprehensive test suite for the interactive Riyadh neighborhoods map viewer.
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from real_estate_intel.riyadh_map_viewer import RiyadhMapViewer


@pytest.fixture
def sample_market_data():
    """Create sample market data for testing."""
    return pd.DataFrame({
        'district_ar': [
            'الرياض', 'العليا', 'الدقي', 'السويدي', 'الملز',
            'الحمراء', 'الربوة', 'الروضة', 'الخليج', 'الشميسي',
        ] * 10,
        'city_ar': ['الرياض'] * 100,
        'region_ar': ['منطقة الرياض'] * 100,
        'average_rent': [30000 + i*1000 for i in range(100)],
        'total_deals': [20 + i for i in range(100)],
        'property_type': ['شقة'] * 100,
        'property_class': ['فاخرة'] * 50 + ['عادية'] * 50,
        'year': [2025] * 100,
    })


class TestRiyadhMapViewerInit:
    """Tests for RiyadhMapViewer initialization."""
    
    @patch('real_estate_intel.riyadh_map_viewer.gzip.open')
    @patch('real_estate_intel.riyadh_map_viewer.pd.read_csv')
    def test_initialization(self, mock_read_csv, mock_gzip, sample_market_data):
        """Test RiyadhMapViewer initialization."""
        mock_gzip.return_value.__enter__.return_value = MagicMock()
        mock_read_csv.return_value = sample_market_data
        
        viewer = RiyadhMapViewer()
        
        assert viewer.data_path is not None
        assert viewer.riyadh_data is not None
        assert viewer.neighborhoods is not None
        assert len(viewer.neighborhoods) > 0
    
    @patch('real_estate_intel.riyadh_map_viewer.gzip.open')
    @patch('real_estate_intel.riyadh_map_viewer.pd.read_csv')
    def test_neighborhoods_loaded(self, mock_read_csv, mock_gzip, sample_market_data):
        """Test that neighborhoods are properly loaded."""
        mock_gzip.return_value.__enter__.return_value = MagicMock()
        mock_read_csv.return_value = sample_market_data
        
        viewer = RiyadhMapViewer()
        
        # Check that unique neighborhoods are extracted
        assert len(viewer.neighborhoods) == 10
        assert 'الرياض' in viewer.neighborhoods
        assert 'العليا' in viewer.neighborhoods


class TestNeighborhoodStatistics:
    """Tests for neighborhood statistics calculation."""
    
    @patch('real_estate_intel.riyadh_map_viewer.gzip.open')
    @patch('real_estate_intel.riyadh_map_viewer.pd.read_csv')
    def test_get_neighborhood_stats(self, mock_read_csv, mock_gzip, sample_market_data):
        """Test getting statistics for a specific neighborhood."""
        mock_gzip.return_value.__enter__.return_value = MagicMock()
        mock_read_csv.return_value = sample_market_data
        
        viewer = RiyadhMapViewer()
        stats = viewer.get_neighborhood_stats('الرياض')
        
        assert stats['name'] == 'الرياض'
        assert stats['records'] == 10
        assert stats['avg_rent'] > 0
        assert stats['total_deals'] > 0
    
    @patch('real_estate_intel.riyadh_map_viewer.gzip.open')
    @patch('real_estate_intel.riyadh_map_viewer.pd.read_csv')
    def test_get_all_neighborhoods_stats(self, mock_read_csv, mock_gzip, sample_market_data):
        """Test getting statistics for all neighborhoods."""
        mock_gzip.return_value.__enter__.return_value = MagicMock()
        mock_read_csv.return_value = sample_market_data
        
        viewer = RiyadhMapViewer()
        stats_df = viewer.get_all_neighborhoods_stats()
        
        assert not stats_df.empty
        assert 'الحي' in stats_df.columns
        assert 'متوسط الإيجار' in stats_df.columns
        assert len(stats_df) == 10
    
    @patch('real_estate_intel.riyadh_map_viewer.gzip.open')
    @patch('real_estate_intel.riyadh_map_viewer.pd.read_csv')
    def test_get_nonexistent_neighborhood_stats(self, mock_read_csv, mock_gzip, sample_market_data):
        """Test getting statistics for non-existent neighborhood."""
        mock_gzip.return_value.__enter__.return_value = MagicMock()
        mock_read_csv.return_value = sample_market_data
        
        viewer = RiyadhMapViewer()
        stats = viewer.get_neighborhood_stats('حي غير موجود')
        
        assert stats['name'] == 'حي غير موجود'
        assert stats['records'] == 0
        assert stats['avg_rent'] == 0


class TestMapCreation:
    """Tests for map creation."""
    
    @patch('real_estate_intel.riyadh_map_viewer.gzip.open')
    @patch('real_estate_intel.riyadh_map_viewer.pd.read_csv')
    def test_create_riyadh_map_heatmap(self, mock_read_csv, mock_gzip, sample_market_data):
        """Test creating a heatmap visualization."""
        mock_gzip.return_value.__enter__.return_value = MagicMock()
        mock_read_csv.return_value = sample_market_data
        
        viewer = RiyadhMapViewer()
        map_obj = viewer.create_riyadh_map(view_type="heatmap", metric="avg_rent")
        
        assert map_obj is not None
        assert hasattr(map_obj, 'save')
    
    @patch('real_estate_intel.riyadh_map_viewer.gzip.open')
    @patch('real_estate_intel.riyadh_map_viewer.pd.read_csv')
    def test_create_riyadh_map_markers(self, mock_read_csv, mock_gzip, sample_market_data):
        """Test creating a marker visualization."""
        mock_gzip.return_value.__enter__.return_value = MagicMock()
        mock_read_csv.return_value = sample_market_data
        
        viewer = RiyadhMapViewer()
        map_obj = viewer.create_riyadh_map(view_type="markers", metric="total_deals")
        
        assert map_obj is not None
    
    @patch('real_estate_intel.riyadh_map_viewer.gzip.open')
    @patch('real_estate_intel.riyadh_map_viewer.pd.read_csv')
    def test_create_riyadh_map_with_different_metrics(self, mock_read_csv, mock_gzip, sample_market_data):
        """Test creating maps with different metrics."""
        mock_gzip.return_value.__enter__.return_value = MagicMock()
        mock_read_csv.return_value = sample_market_data
        
        viewer = RiyadhMapViewer()
        
        # Test with average rent
        map1 = viewer.create_riyadh_map(metric="avg_rent")
        assert map1 is not None
        
        # Test with total deals
        map2 = viewer.create_riyadh_map(metric="total_deals")
        assert map2 is not None
        
        # Test with records
        map3 = viewer.create_riyadh_map(metric="records")
        assert map3 is not None


class TestColorMapping:
    """Tests for color mapping functions."""
    
    @patch('real_estate_intel.riyadh_map_viewer.gzip.open')
    @patch('real_estate_intel.riyadh_map_viewer.pd.read_csv')
    def test_get_color_for_rent_low(self, mock_read_csv, mock_gzip, sample_market_data):
        """Test color mapping for low rent values."""
        mock_gzip.return_value.__enter__.return_value = MagicMock()
        mock_read_csv.return_value = sample_market_data
        
        viewer = RiyadhMapViewer()
        color = viewer._get_color_for_rent(15000)
        
        assert color == '#27ae60'  # Green
    
    @patch('real_estate_intel.riyadh_map_viewer.gzip.open')
    @patch('real_estate_intel.riyadh_map_viewer.pd.read_csv')
    def test_get_color_for_rent_medium(self, mock_read_csv, mock_gzip, sample_market_data):
        """Test color mapping for medium rent values."""
        mock_gzip.return_value.__enter__.return_value = MagicMock()
        mock_read_csv.return_value = sample_market_data
        
        viewer = RiyadhMapViewer()
        color = viewer._get_color_for_rent(30000)
        
        assert color == '#f39c12'  # Orange
    
    @patch('real_estate_intel.riyadh_map_viewer.gzip.open')
    @patch('real_estate_intel.riyadh_map_viewer.pd.read_csv')
    def test_get_color_for_rent_high(self, mock_read_csv, mock_gzip, sample_market_data):
        """Test color mapping for high rent values."""
        mock_gzip.return_value.__enter__.return_value = MagicMock()
        mock_read_csv.return_value = sample_market_data
        
        viewer = RiyadhMapViewer()
        color = viewer._get_color_for_rent(70000)
        
        assert color == '#8b0000'  # Dark Red


class TestComparisonChart:
    """Tests for comparison chart creation."""
    
    @patch('real_estate_intel.riyadh_map_viewer.gzip.open')
    @patch('real_estate_intel.riyadh_map_viewer.pd.read_csv')
    def test_create_comparison_chart(self, mock_read_csv, mock_gzip, sample_market_data):
        """Test creating comparison chart data."""
        mock_gzip.return_value.__enter__.return_value = MagicMock()
        mock_read_csv.return_value = sample_market_data
        
        viewer = RiyadhMapViewer()
        comparison = viewer.create_comparison_chart()
        
        assert 'top_expensive' in comparison
        assert 'top_active' in comparison
        assert 'all_stats' in comparison
        assert not comparison['top_expensive'].empty
        assert not comparison['top_active'].empty


class TestDataIntegration:
    """Integration tests with actual data loading."""
    
    def test_real_data_loading(self):
        """Test loading real market data (if available)."""
        data_path = Path("data/processed/rental_market.csv.gz")
        
        if not data_path.exists():
            pytest.skip("Test data not available")
        
        viewer = RiyadhMapViewer(str(data_path))
        
        # Basic checks
        assert viewer.neighborhoods is not None
        assert len(viewer.neighborhoods) > 0
        assert viewer.riyadh_data is not None
        assert not viewer.riyadh_data.empty
    
    def test_riyadh_neighborhoods_count(self):
        """Test that Riyadh has expected number of neighborhoods."""
        data_path = Path("data/processed/rental_market.csv.gz")
        
        if not data_path.exists():
            pytest.skip("Test data not available")
        
        viewer = RiyadhMapViewer(str(data_path))
        
        # Riyadh should have 200+ neighborhoods
        assert len(viewer.neighborhoods) > 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
