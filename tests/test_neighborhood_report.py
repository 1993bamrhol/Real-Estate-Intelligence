"""Tests for neighborhood report generation."""

import pandas as pd
import pytest

from real_estate_intel.neighborhood_report import NeighborhoodReportGenerator


@pytest.fixture
def sample_market_data():
    """Create sample market data for testing."""
    data = {
        'location_ar': ['الشرقية', 'الشرقية', 'الشرقية', 'الرياض', 'الرياض'],
        'city_ar': ['الدمام', 'الدمام', 'الدمام', 'الرياض', 'الرياض'],
        'region_ar': ['المنطقة الشرقية', 'المنطقة الشرقية', 'المنطقة الشرقية', 'منطقة الرياض', 'منطقة الرياض'],
        'property_type': ['فيلا', 'شقة', 'فيلا', 'شقة', 'فيلا'],
        'average_rent': [5000, 2000, 5500, 3000, 6000],
        'total_deals': [10, 50, 8, 60, 12],
        'period': ['2026 Q1', '2026 Q1', '2026 Q1', '2026 Q1', '2026 Q1'],
        'period_index': [1, 1, 1, 1, 1],
    }
    return pd.DataFrame(data)


def test_neighborhood_report_generator_init(sample_market_data):
    """Test generator initialization."""
    generator = NeighborhoodReportGenerator(sample_market_data)
    assert generator.market_data is not None
    assert len(generator.market_data) == 5


def test_get_available_locations(sample_market_data):
    """Test getting available locations."""
    generator = NeighborhoodReportGenerator(sample_market_data)
    locations = generator.get_available_locations()
    
    assert 'الشرقية' in locations
    assert 'الرياض' in locations
    assert len(locations) >= 2


def test_get_locations_by_city(sample_market_data):
    """Test getting locations for a specific city."""
    generator = NeighborhoodReportGenerator(sample_market_data)
    locations = generator.get_locations_by_city('الدمام')
    
    assert 'الشرقية' in locations
    assert len(locations) >= 1


def test_extract_neighborhood_data(sample_market_data):
    """Test extracting neighborhood data."""
    generator = NeighborhoodReportGenerator(sample_market_data)
    
    neighborhood_data = generator._extract_neighborhood_data('الشرقية')
    
    assert len(neighborhood_data) == 3  # 3 records for الشرقية
    assert all(neighborhood_data['location_ar'] == 'الشرقية')


def test_extract_neighborhood_data_with_city_filter(sample_market_data):
    """Test extracting neighborhood data with city filter."""
    generator = NeighborhoodReportGenerator(sample_market_data)
    
    neighborhood_data = generator._extract_neighborhood_data(
        'الشرقية',
        city_name='الدمام'
    )
    
    assert len(neighborhood_data) == 3
    assert all(neighborhood_data['city_ar'] == 'الدمام')


def test_calculate_metrics(sample_market_data):
    """Test calculating metrics."""
    generator = NeighborhoodReportGenerator(sample_market_data)
    neighborhood_data = generator._extract_neighborhood_data('الشرقية')
    
    metrics = generator._calculate_metrics(neighborhood_data)
    
    assert 'location' in metrics
    assert 'average_rent' in metrics
    assert 'total_deals' in metrics
    assert 'price_trend' in metrics
    assert metrics['location'] == 'الشرقية'
    assert metrics['average_rent'] > 0


def test_calculate_comparisons(sample_market_data):
    """Test calculating comparisons."""
    generator = NeighborhoodReportGenerator(sample_market_data)
    neighborhood_data = generator._extract_neighborhood_data('الشرقية')
    
    comparisons = generator._calculate_comparisons(
        neighborhood_data,
        city_name='الدمام'
    )
    
    assert 'city_average' in comparisons
    assert 'city_difference' in comparisons
    assert 'national_average' in comparisons
    assert isinstance(comparisons['city_difference'], (int, float))


def test_generate_neighborhood_report_pdf(sample_market_data):
    """Test PDF report generation."""
    generator = NeighborhoodReportGenerator(sample_market_data)
    
    pdf_bytes = generator.generate_neighborhood_report_pdf('الشرقية')
    
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 0
    assert isinstance(pdf_bytes, bytes)
    # Check if it's a valid PDF (starts with %PDF)
    assert pdf_bytes[:4] == b'%PDF'


def test_generate_empty_report_pdf(sample_market_data):
    """Test PDF generation for non-existent neighborhood."""
    generator = NeighborhoodReportGenerator(sample_market_data)
    
    pdf_bytes = generator.generate_neighborhood_report_pdf('حي غير موجود')
    
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 0
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes[:4] == b'%PDF'
