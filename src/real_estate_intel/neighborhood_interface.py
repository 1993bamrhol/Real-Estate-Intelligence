"""Streamlit interface for neighborhood report generation."""

from __future__ import annotations

import streamlit as st
import pandas as pd

from real_estate_intel.neighborhood_report import NeighborhoodReportGenerator
from real_estate_intel.data_engine import load_market_data


def render_neighborhood_report_page():
    """Render the neighborhood report generation page."""
    
    st.markdown("### 📋 تقرير المخطط الشامل")
    st.markdown("_احصل على تقرير مفصل عن أي حي أو مخطط سكني_")
    
    # Load market data
    market_data = load_market_data()
    
    if market_data.empty:
        st.error("لا يمكن تحميل بيانات السوق")
        return
    
    # Initialize report generator
    generator = NeighborhoodReportGenerator(market_data)
    
    # Get available locations
    available_locations = generator.get_available_locations()
    
    if not available_locations:
        st.warning("لا توجد بيانات متاحة للأحياء")
        return
    
    # Sidebar filters
    col1, col2 = st.columns(2)
    
    with col1:
        # City filter (optional)
        unique_cities = sorted(market_data['city_ar'].dropna().unique().tolist())
        selected_city = st.selectbox(
            "المدينة (اختياري)",
            options=["جميع المدن"] + unique_cities,
            key="neighborhood_city"
        )
        
        if selected_city != "جميع المدن":
            # Get locations for this city
            city_locations = generator.get_locations_by_city(selected_city)
            location_options = city_locations
        else:
            location_options = available_locations
    
    with col2:
        # Location/Neighborhood selector
        selected_location = st.selectbox(
            "اختر الحي أو المخطط",
            options=location_options,
            key="neighborhood_location"
        )
    
    # Optional region filter
    unique_regions = sorted(market_data['region_ar'].dropna().unique().tolist())
    selected_region = st.selectbox(
        "المنطقة الإدارية (اختياري)",
        options=["جميع المناطق"] + unique_regions,
        key="neighborhood_region",
    )
    
    if selected_region == "جميع المناطق":
        selected_region = None
    
    st.markdown("---")
    
    # Report generation section
    st.markdown("### 📄 إنشاء التقرير")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 عرض ملخص البيانات", use_container_width=True):
            _display_neighborhood_summary(
                market_data,
                selected_location,
                selected_city if selected_city != "جميع المدن" else None,
                selected_region
            )
    
    with col2:
        if st.button("📈 إنشاء تقرير PDF", use_container_width=True):
            _generate_and_download_pdf(
                generator,
                selected_location,
                selected_city if selected_city != "جميع المدن" else None,
                selected_region
            )
    
    with col3:
        if st.button("🔍 تحليل سريع", use_container_width=True):
            _display_quick_analysis(
                market_data,
                selected_location,
                selected_city if selected_city != "جميع المدن" else None,
                selected_region
            )


def _display_neighborhood_summary(
    market_data: pd.DataFrame,
    location: str,
    city: str | None = None,
    region: str | None = None
):
    """Display neighborhood summary."""
    
    # Filter data
    df = market_data[market_data['location_ar'].str.contains(location, case=False, na=False)]
    
    if city:
        df = df[df['city_ar'].str.contains(city, case=False, na=False)]
    
    if region:
        df = df[df['region_ar'].str.contains(region, case=False, na=False)]
    
    if df.empty:
        st.error("لا توجد بيانات لهذا الحي")
        return
    
    # Get latest period data
    latest_period = df['period_index'].max()
    latest_data = df[df['period_index'] == latest_period]
    
    # Display metrics
    st.markdown("### 📊 البيانات الأساسية")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_rent = latest_data['average_rent'].mean()
        st.metric("متوسط الإيجار", f"ر.س {avg_rent:,.0f}")
    
    with col2:
        total_deals = latest_data['total_deals'].sum()
        st.metric("إجمالي الصفقات", f"{total_deals:,.0f}")
    
    with col3:
        num_records = len(latest_data)
        st.metric("عدد السجلات", f"{num_records}")
    
    with col4:
        latest_period_str = df['period'].iloc[-1]
        st.metric("آخر فترة", latest_period_str)
    
    # Price by property type
    st.markdown("### 📈 الأسعار حسب نوع العقار")
    
    price_by_type = latest_data.groupby('property_type').agg({
        'average_rent': 'mean',
        'total_deals': 'sum'
    }).round(0).sort_values('average_rent', ascending=False)
    
    if not price_by_type.empty:
        st.dataframe(
            price_by_type.rename(columns={
                'average_rent': 'متوسط الإيجار (ر.س)',
                'total_deals': 'عدد الصفقات'
            }),
            use_container_width=True
        )
    
    # Historical trend
    st.markdown("### 📊 الاتجاه التاريخي")
    
    historical = df.groupby('period')['average_rent'].mean()
    
    if not historical.empty:
        st.line_chart(historical, use_container_width=True)
        
        # Trend info
        if len(historical) > 1:
            change = historical.iloc[-1] - historical.iloc[-2]
            change_pct = (change / historical.iloc[-2] * 100) if historical.iloc[-2] > 0 else 0
            
            if change > 0:
                st.success(f"📈 ارتفاع: {abs(change_pct):.1f}%")
            elif change < 0:
                st.info(f"📉 انخفاض: {abs(change_pct):.1f}%")
            else:
                st.info("➡️ مستقر")


def _generate_and_download_pdf(
    generator: NeighborhoodReportGenerator,
    location: str,
    city: str | None = None,
    region: str | None = None
):
    """Generate and download PDF report."""
    
    with st.spinner("جاري إنشاء التقرير..."):
        pdf_bytes = generator.generate_neighborhood_report_pdf(
            location_name=location,
            city_name=city,
            region_name=region
        )
    
    # Create filename
    filename = f"تقرير_{location}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    st.success("✅ تم إنشاء التقرير بنجاح")
    
    st.download_button(
        label="⬇️ تحميل التقرير (PDF)",
        data=pdf_bytes,
        file_name=filename,
        mime="application/pdf",
        use_container_width=True
    )


def _display_quick_analysis(
    market_data: pd.DataFrame,
    location: str,
    city: str | None = None,
    region: str | None = None
):
    """Display quick analysis."""
    
    # Filter data
    df = market_data[market_data['location_ar'].str.contains(location, case=False, na=False)]
    
    if city:
        df = df[df['city_ar'].str.contains(city, case=False, na=False)]
    
    if region:
        df = df[df['region_ar'].str.contains(region, case=False, na=False)]
    
    if df.empty:
        st.error("لا توجد بيانات لهذا الحي")
        return
    
    # Get comparisons
    latest_period = market_data['period_index'].max()
    neighborhood_avg = df['average_rent'].mean()
    
    # City comparison
    if city:
        city_data = market_data[market_data['city_ar'].str.contains(city, case=False, na=False)]
        city_data = city_data[city_data['period_index'] == latest_period]
        city_avg = city_data['average_rent'].mean()
        
        st.markdown("### 📍 مقارنة مع المدينة")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("متوسط الحي", f"ر.س {neighborhood_avg:,.0f}")
        
        with col2:
            st.metric("متوسط المدينة", f"ر.س {city_avg:,.0f}")
        
        if city_avg > 0:
            diff_pct = ((neighborhood_avg - city_avg) / city_avg * 100)
            if diff_pct > 0:
                st.success(f"📈 أعلى من متوسط المدينة بـ {diff_pct:.1f}%")
            else:
                st.info(f"📉 أقل من متوسط المدينة بـ {abs(diff_pct):.1f}%")
    
    # Investment opportunities
    st.markdown("### 💡 فرص الاستثمار")
    
    # Get highest performing property types
    latest_data = df[df['period_index'] == latest_period]
    best_types = latest_data.nlargest(3, 'average_rent')[['property_type', 'average_rent']]
    
    if not best_types.empty:
        st.subheader("أنواع العقارات الأكثر قيمة:")
        for idx, (_, row) in enumerate(best_types.iterrows(), 1):
            st.write(f"{idx}. {row['property_type']}: ر.س {row['average_rent']:,.0f}")
    
    # Market activity
    st.markdown("### 📊 نشاط السوق")
    
    total_deals = latest_data['total_deals'].sum()
    avg_deals_per_type = total_deals / len(latest_data) if len(latest_data) > 0 else 0
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("إجمالي الصفقات الأخيرة", f"{total_deals:,.0f}")
    
    with col2:
        st.metric("متوسط الصفقات", f"{avg_deals_per_type:.0f}")
    
    if total_deals > market_data[market_data['period_index'] == latest_period]['total_deals'].mean():
        st.success("📈 السوق نشط جداً في هذا الحي")
    else:
        st.info("⚠️ نشاط السوق منخفض نسبياً")
