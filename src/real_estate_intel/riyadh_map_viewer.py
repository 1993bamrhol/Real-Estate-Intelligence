"""
Riyadh Neighborhoods Interactive Map Viewer
============================================

Comprehensive interactive map visualization for all neighborhoods in Riyadh
with integrated data analytics and real estate metrics.

Author: QAREENA AI Assistant
Date: 2026-08-17
"""

import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium.plugins import HeatMap, MarkerCluster, FastMarkerCluster
from streamlit_folium import st_folium
import gzip
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime


# ============================================================================
# CACHING LAYER - Prevent redundant data loading
# ============================================================================

@st.cache_resource
def get_viewer_instance() -> "RiyadhMapViewer":
    """Get or create a cached RiyadhMapViewer instance."""
    return RiyadhMapViewer()


@st.cache_data
def get_cached_neighborhoods_stats(_viewer: "RiyadhMapViewer") -> pd.DataFrame:
    """Cache the neighborhood statistics."""
    return _viewer.get_all_neighborhoods_stats()


@st.cache_data
def get_cached_comparison_data(_viewer: "RiyadhMapViewer") -> Dict:
    """Cache the comparison chart data."""
    return _viewer.create_comparison_chart()


@st.cache_data
def create_riyadh_map_cached(view_type: str, metric: str) -> folium.Map:
    """Create and cache a Riyadh map based on parameters.
    
    Args:
        view_type: Type of visualization
        metric: Metric to display
        
    Returns:
        Cached folium map object
    """
    viewer = get_viewer_instance()
    return viewer.create_riyadh_map(
        view_type=view_type,
        show_markers=True,
        metric=metric,
    )


class RiyadhMapViewer:
    """Interactive map viewer for all Riyadh neighborhoods."""
    
    # Approximate coordinates for Riyadh neighborhoods
    # Format: {neighborhood_name: (latitude, longitude)}
    NEIGHBORHOOD_COORDINATES = {
        'الرياض': (24.7136, 46.6753),
        'العليا': (24.7500, 46.6800),
        'الدقي': (24.7400, 46.6600),
        'السويدي': (24.7300, 46.6700),
        'الملز': (24.7200, 46.6900),
        'الحمراء': (24.7100, 46.7000),
        'الربوة': (24.7000, 46.6900),
        'الروضة': (24.7050, 46.6650),
        'الخليج': (24.7150, 46.6550),
        'الشميسي': (24.6900, 46.7100),
        'النزهة': (24.6800, 46.7200),
        'الصناعية': (24.6700, 46.7300),
        'السلام': (24.7250, 46.7050),
        'الخزامى': (24.7350, 46.6450),
        'الإسكان': (24.7450, 46.6550),
        'الياسمين': (24.7550, 46.6650),
        'التلال': (24.7300, 46.7150),
        'الشارقة': (24.7150, 46.7350),
        'قرطبة': (24.7000, 46.7350),
        'الرمال': (24.6850, 46.7450),
    }
    
    def __init__(self, data_path: str = "data/processed/rental_market.csv.gz"):
        """Initialize the Riyadh Map Viewer.
        
        Args:
            data_path: Path to the rental market data file
        """
        self.data_path = Path(data_path)
        self.df = None
        self.riyadh_data = None
        self.neighborhoods = None
        self._load_data()
    
    def _load_data(self) -> None:
        """Load and filter rental market data for Riyadh."""
        try:
            with gzip.open(self.data_path, 'rt', encoding='utf-8') as f:
                self.df = pd.read_csv(f)
            
            # Filter for Riyadh
            self.riyadh_data = self.df[
                self.df['city_ar'].str.contains('رياض', case=False, na=False)
            ].copy()
            
            # Get unique neighborhoods
            self.neighborhoods = sorted(
                self.riyadh_data['district_ar'].dropna().unique().tolist()
            )
        except Exception as e:
            st.error(f"خطأ في تحميل البيانات: {str(e)}")
            self.neighborhoods = []
    
    def get_neighborhood_stats(self, neighborhood: str) -> Dict:
        """Calculate statistics for a specific neighborhood.
        
        Args:
            neighborhood: The neighborhood name
            
        Returns:
            Dictionary containing neighborhood statistics
        """
        data = self.riyadh_data[
            self.riyadh_data['district_ar'] == neighborhood
        ]
        
        if data.empty:
            return {
                'name': neighborhood,
                'records': 0,
                'avg_rent': 0,
                'total_deals': 0,
                'property_types': [],
            }
        
        return {
            'name': neighborhood,
            'records': len(data),
            'avg_rent': data['average_rent'].mean(),
            'total_deals': data['total_deals'].sum(),
            'property_types': data['property_type'].unique().tolist(),
            'property_classes': data['property_class'].unique().tolist(),
            'latest_year': data['year'].max(),
        }
    
    def get_all_neighborhoods_stats(self) -> pd.DataFrame:
        """Get statistics for all neighborhoods.
        
        Returns:
            DataFrame with all neighborhoods and their statistics
        """
        stats = []
        for neighborhood in self.neighborhoods:
            data = self.riyadh_data[
                self.riyadh_data['district_ar'] == neighborhood
            ]
            if not data.empty:
                stats.append({
                    'الحي': neighborhood,
                    'عدد السجلات': len(data),
                    'متوسط الإيجار': data['average_rent'].mean(),
                    'إجمالي الصفقات': data['total_deals'].sum(),
                    'السنة الأخيرة': data['year'].max(),
                })
        
        return pd.DataFrame(stats)
    
    def create_riyadh_map(self, 
                         view_type: str = "heatmap",
                         show_markers: bool = True,
                         metric: str = "avg_rent") -> folium.Map:
        """Create an interactive map of Riyadh neighborhoods.
        
        Args:
            view_type: Type of map visualization ('heatmap', 'cluster', 'markers')
            show_markers: Whether to show markers for neighborhoods
            metric: The metric to visualize ('avg_rent', 'total_deals', 'records')
            
        Returns:
            Folium map object
        """
        # Center coordinates for Riyadh
        riyadh_center = [24.7136, 46.6753]
        
        # Create base map
        map_obj = folium.Map(
            location=riyadh_center,
            zoom_start=11,
            tiles='OpenStreetMap',
            prefer_canvas=True,
        )
        
        # Get statistics for all neighborhoods
        heat_data = []
        markers_data = []
        
        for neighborhood in self.neighborhoods:
            stats = self.get_neighborhood_stats(neighborhood)
            
            if stats['records'] == 0:
                continue
            
            # Get or estimate coordinates
            if neighborhood in self.NEIGHBORHOOD_COORDINATES:
                lat, lon = self.NEIGHBORHOOD_COORDINATES[neighborhood]
            else:
                # Generate approximate coordinates within Riyadh
                lat = riyadh_center[0] + np.random.uniform(-0.3, 0.3)
                lon = riyadh_center[1] + np.random.uniform(-0.3, 0.3)
            
            # Prepare data based on metric
            if metric == "avg_rent":
                value = stats['avg_rent']
                intensity = min(value / 100000, 1.0)  # Normalize to 0-1
            elif metric == "total_deals":
                value = stats['total_deals']
                intensity = min(value / 1000, 1.0)
            else:  # records
                value = stats['records']
                intensity = min(value / 100, 1.0)
            
            heat_data.append([lat, lon, intensity])
            markers_data.append({
                'lat': lat,
                'lon': lon,
                'neighborhood': neighborhood,
                'value': value,
                'stats': stats
            })
        
        # Add visualization based on type
        if view_type == "heatmap" and heat_data:
            HeatMap(heat_data, radius=25, blur=15, max_zoom=1).add_to(map_obj)
        
        if show_markers or view_type == "markers":
            for marker in markers_data:
                # Color based on intensity
                value = marker['value']
                if metric == "avg_rent":
                    color = self._get_color_for_rent(value)
                else:
                    color = self._get_color_for_value(value)
                
                # Create popup
                stats = marker['stats']
                popup_text = f"""
                <div style='direction: rtl; text-align: right; font-family: Arial; width: 250px;'>
                    <b style='font-size: 14px; color: #2c3e50;'>{marker['neighborhood']}</b><br>
                    <hr style='margin: 5px 0;'>
                    <b>متوسط الإيجار:</b> {stats['avg_rent']:,.0f} ر.س<br>
                    <b>إجمالي الصفقات:</b> {stats['total_deals']:,.0f}<br>
                    <b>عدد السجلات:</b> {stats['records']}<br>
                    <b>السنة:</b> {stats.get('latest_year', 'N/A')}<br>
                </div>
                """
                
                folium.CircleMarker(
                    location=[marker['lat'], marker['lon']],
                    radius=8,
                    popup=folium.Popup(popup_text, max_width=300),
                    color=color,
                    fill=True,
                    fillColor=color,
                    fillOpacity=0.7,
                    weight=2,
                ).add_to(map_obj)
        
        return map_obj
    
    def _get_color_for_rent(self, value: float) -> str:
        """Get color based on rental value.
        
        Args:
            value: Rental value in SAR
            
        Returns:
            Color hex code
        """
        if value < 20000:
            return '#27ae60'  # Green
        elif value < 40000:
            return '#f39c12'  # Orange
        elif value < 60000:
            return '#e74c3c'  # Red
        else:
            return '#8b0000'  # Dark Red
    
    def _get_color_for_value(self, value: float) -> str:
        """Get color based on generic value.
        
        Args:
            value: The value to map to color
            
        Returns:
            Color hex code
        """
        if value < 50:
            return '#3498db'  # Blue
        elif value < 200:
            return '#9b59b6'  # Purple
        elif value < 500:
            return '#e67e22'  # Orange
        else:
            return '#c0392b'  # Red
    
    def create_comparison_chart(self) -> Dict:
        """Create comparison data for top neighborhoods.
        
        Returns:
            Dictionary with comparison data
        """
        stats = self.get_all_neighborhoods_stats()
        
        if stats.empty:
            return {}
        
        # Sort by average rent
        top_expensive = stats.nlargest(10, 'متوسط الإيجار')
        top_active = stats.nlargest(10, 'إجمالي الصفقات')
        
        return {
            'top_expensive': top_expensive,
            'top_active': top_active,
            'all_stats': stats,
        }


def render_riyadh_map_page() -> None:
    """Render the Riyadh Map Viewer page in Streamlit."""
    
    st.markdown("## 🗺️ خريطة أحياء الرياض الشاملة")
    st.markdown("عرض تفاعلي شامل لجميع أحياء الرياض مع معلومات السوق العقاري")
    
    # Get cached viewer instance
    viewer = get_viewer_instance()
    
    if not viewer.neighborhoods:
        st.error("لم يتمكن من تحميل بيانات أحياء الرياض")
        return
    
    st.info(f"📊 تم العثور على **{len(viewer.neighborhoods)}** حي في الرياض")
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "🗺️ الخريطة التفاعلية",
        "📊 إحصائيات الأحياء",
        "🏆 الأحياء الأفضل",
        "📈 تقارير مقارنة",
    ])
    
    # Tab 1: Interactive Map
    with tab1:
        st.subheader("عرض الخريطة الحرارية لأحياء الرياض")
        
        # Use columns to organize controls
        col1, col2 = st.columns(2)
        
        # Store selections in session state to prevent re-renders
        if "map_view_type" not in st.session_state:
            st.session_state.map_view_type = "🔥 خريطة حرارية"
        if "map_metric" not in st.session_state:
            st.session_state.map_metric = "avg_rent"
        
        with col1:
            st.session_state.map_view_type = st.radio(
                "نوع العرض:",
                ["🔥 خريطة حرارية", "📍 علامات الأحياء", "👥 مجموعات"],
                index=["🔥 خريطة حرارية", "📍 علامات الأحياء", "👥 مجموعات"].index(st.session_state.map_view_type),
                horizontal=True,
                key="map_view_radio"
            )
        
        with col2:
            metric_options = [("متوسط الإيجار", "avg_rent"), 
                             ("إجمالي الصفقات", "total_deals"), 
                             ("عدد السجلات", "records")]
            selected_metric = st.selectbox(
                "المقياس المستخدم:",
                metric_options,
                index=next(i for i, (_, v) in enumerate(metric_options) if v == st.session_state.map_metric),
                format_func=lambda x: x[0],
                key="map_metric_select"
            )
            st.session_state.map_metric = selected_metric[1]
        
        # Map type mapping
        map_type_map = {
            "🔥 خريطة حرارية": "heatmap",
            "📍 علامات الأحياء": "markers",
            "👥 مجموعات": "cluster",
        }
        
        riyadh_map = create_riyadh_map_cached(
            view_type=map_type_map[st.session_state.map_view_type],
            metric=st.session_state.map_metric,
        )

        # Avoid reruns on pan/zoom/hover so the page does not keep dimming.
        st_folium(
            riyadh_map,
            width=1200,
            height=600,
            key=f"map_{st.session_state.map_view_type}_{st.session_state.map_metric}",
            returned_objects=[],
        )
        
        st.markdown("---")
        st.markdown("""
        **كيفية استخدام الخريطة:**
        - 🔍 استخدم عجلة الماوس للتكبير والتصغير
        - 📍 انقر على العلامات الملونة لرؤية تفاصيل الحي
        - 🎨 يشير اللون إلى شدة القيمة (أحمر = أعلى، أخضر = أقل)
        - 🌐 اسحب الخريطة لعرض مناطق مختلفة
        """)
    
    # Tab 2: Neighborhood Statistics
    with tab2:
        st.subheader("إحصائيات جميع الأحياء")
        
        # Get cached stats
        all_stats = get_cached_neighborhoods_stats(viewer)
        
        if not all_stats.empty:
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "إجمالي الأحياء",
                    len(all_stats),
                    "حي"
                )
            
            with col2:
                st.metric(
                    "متوسط الإيجار",
                    f"{all_stats['متوسط الإيجار'].mean():,.0f}",
                    "ر.س"
                )
            
            with col3:
                st.metric(
                    "أعلى إيجار",
                    f"{all_stats['متوسط الإيجار'].max():,.0f}",
                    "ر.س"
                )
            
            with col4:
                st.metric(
                    "إجمالي الصفقات",
                    f"{all_stats['إجمالي الصفقات'].sum():,.0f}",
                    "صفقة"
                )
            
            st.markdown("---")
            
            # Searchable table with session state
            if "stats_search" not in st.session_state:
                st.session_state.stats_search = ""
            
            st.markdown("**البحث والتصفية:**")
            st.session_state.stats_search = st.text_input(
                "ابحث عن حي...", 
                value=st.session_state.stats_search,
                placeholder="أدخل اسم الحي"
            )
            
            if st.session_state.stats_search:
                filtered = all_stats[
                    all_stats['الحي'].str.contains(st.session_state.stats_search, case=False, na=False)
                ]
            else:
                filtered = all_stats
            
            # Sort options
            if "stats_sort" not in st.session_state:
                st.session_state.stats_sort = "الحي"
            
            st.session_state.stats_sort = st.selectbox(
                "ترتيب حسب:",
                ["الحي", "متوسط الإيجار", "إجمالي الصفقات", "عدد السجلات"],
                index=["الحي", "متوسط الإيجار", "إجمالي الصفقات", "عدد السجلات"].index(st.session_state.stats_sort)
            )
            
            filtered = filtered.sort_values(
                by=st.session_state.stats_sort,
                ascending=(st.session_state.stats_sort == "الحي")
            )
            
            # Display table with formatting
            st.dataframe(
                filtered,
                use_container_width=True,
                height=500,
                hide_index=True,
            )
            
            # Download button
            csv = all_stats.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 تحميل البيانات (CSV)",
                data=csv,
                file_name=f"riyadh_neighborhoods_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )
    
    # Tab 3: Best Neighborhoods
    with tab3:
        st.subheader("الأحياء الأفضل والأكثر نشاطاً")
        
        comparison = get_cached_comparison_data(viewer)
        
        if comparison:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 💰 أغلى الأحياء (الإيجار الأعلى)")
                top_expensive = comparison['top_expensive']
                for idx, row in top_expensive.iterrows():
                    st.markdown(f"""
                    **{row['الحي']}**  
                    💵 {row['متوسط الإيجار']:,.0f} ر.س  
                    📊 {row['عدد السجلات']} سجل
                    """)
            
            with col2:
                st.markdown("### 🔥 الأحياء الأنشط (الصفقات الأكثر)")
                top_active = comparison['top_active']
                for idx, row in top_active.iterrows():
                    st.markdown(f"""
                    **{row['الحي']}**  
                    📈 {row['إجمالي الصفقات']:,.0f} صفقة  
                    💰 متوسط الإيجار: {row['متوسط الإيجار']:,.0f} ر.س
                    """)
    
    # Tab 4: Comparison Reports
    with tab4:
        st.subheader("تقارير مقارنة الأحياء")
        
        # Initialize session state for selected neighborhoods
        if "selected_neighborhoods" not in st.session_state:
            st.session_state.selected_neighborhoods = viewer.neighborhoods[:5]
        
        st.session_state.selected_neighborhoods = st.multiselect(
            "اختر الأحياء للمقارنة:",
            viewer.neighborhoods,
            default=st.session_state.selected_neighborhoods,
            max_selections=10,
        )
        
        if st.session_state.selected_neighborhoods:
            # Create comparison data
            comparison_data = []
            for neighborhood in st.session_state.selected_neighborhoods:
                stats = viewer.get_neighborhood_stats(neighborhood)
                comparison_data.append({
                    'الحي': neighborhood,
                    'متوسط الإيجار': stats['avg_rent'],
                    'إجمالي الصفقات': stats['total_deals'],
                    'عدد السجلات': stats['records'],
                })
            
            comparison_df = pd.DataFrame(comparison_data)
            
            # Display comparison
            st.dataframe(comparison_df, use_container_width=True)
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                st.bar_chart(
                    comparison_df.set_index('الحي')['متوسط الإيجار'],
                    height=400,
                )
            
            with col2:
                st.bar_chart(
                    comparison_df.set_index('الحي')['إجمالي الصفقات'],
                    height=400,
                )
