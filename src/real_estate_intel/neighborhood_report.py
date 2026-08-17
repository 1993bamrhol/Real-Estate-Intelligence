"""Generate comprehensive neighborhood/district reports."""

from __future__ import annotations

from io import BytesIO
from datetime import datetime
from typing import Any

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    PageBreak, Image, KeepTogether
)
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from arabic_reshaper import reshape
from bidi.algorithm import get_display


def _ar_text(text: str) -> str:
    """Reshape Arabic text for PDF display."""
    if not text:
        return ""
    reshaped = reshape(text)
    return get_display(reshaped)


class NeighborhoodReportGenerator:
    """Generate comprehensive reports for neighborhoods/districts."""
    
    def __init__(self, market_data: pd.DataFrame):
        """
        Initialize report generator.
        
        Args:
            market_data: DataFrame with rental market data
        """
        self.market_data = market_data
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom Reportlab styles for Arabic text."""
        self.styles.add(ParagraphStyle(
            name='ArabicTitle',
            parent=self.styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#0B6B53'),
            alignment=TA_RIGHT,
            spaceAfter=12,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='ArabicHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#0B6B53'),
            alignment=TA_RIGHT,
            spaceAfter=8,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='ArabicBody',
            parent=self.styles['Normal'],
            fontSize=11,
            alignment=TA_RIGHT,
            spaceAfter=6
        ))
    
    def generate_neighborhood_report_pdf(
        self,
        location_name: str,
        city_name: str | None = None,
        region_name: str | None = None
    ) -> bytes:
        """
        Generate a complete neighborhood report as PDF.
        
        Args:
            location_name: Name of the neighborhood/location
            city_name: Optional city name for filtering
            region_name: Optional region name for filtering
            
        Returns:
            PDF bytes of the report
        """
        # Extract neighborhood data
        neighborhood_data = self._extract_neighborhood_data(
            location_name, city_name, region_name
        )
        
        if neighborhood_data.empty:
            return self._generate_empty_report_pdf(location_name)
        
        # Calculate metrics
        metrics = self._calculate_metrics(neighborhood_data)
        comparisons = self._calculate_comparisons(
            neighborhood_data, city_name, region_name
        )
        
        # Build PDF
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=A4,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch,
            title=f"تقرير {location_name}",
            author="قرينة",
            subject="تقرير تحليل حي عقاري"
        )
        
        # Build story
        story = []
        story.append(self._build_title_page(location_name, metrics))
        story.append(PageBreak())
        story.append(self._build_executive_summary(location_name, metrics))
        story.append(PageBreak())
        story.append(self._build_market_analysis(neighborhood_data, metrics))
        story.append(PageBreak())
        story.append(self._build_comparisons(comparisons, metrics))
        story.append(PageBreak())
        story.append(self._build_recommendations(metrics))
        
        # Build PDF
        doc.build(story)
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()
    
    def _extract_neighborhood_data(
        self,
        location_name: str,
        city_name: str | None = None,
        region_name: str | None = None
    ) -> pd.DataFrame:
        """Extract data for a specific neighborhood."""
        df = self.market_data.copy()
        
        # Filter by location
        df = df[df['location_ar'].str.contains(location_name, case=False, na=False)]
        
        if city_name:
            df = df[df['city_ar'].str.contains(city_name, case=False, na=False)]
        
        if region_name:
            df = df[df['region_ar'].str.contains(region_name, case=False, na=False)]
        
        return df
    
    def _calculate_metrics(self, data: pd.DataFrame) -> dict[str, Any]:
        """Calculate key metrics for the neighborhood."""
        latest_period_data = data[
            data['period_index'] == data['period_index'].max()
        ]
        
        metrics = {
            'location': data['location_ar'].iloc[0] if not data.empty else "غير معروف",
            'city': data['city_ar'].iloc[0] if not data.empty else "غير معروف",
            'region': data['region_ar'].iloc[0] if not data.empty else "غير معروف",
            'total_records': len(latest_period_data),
            'average_rent': latest_period_data['average_rent'].mean(),
            'total_deals': latest_period_data['total_deals'].sum(),
            'property_types': latest_period_data['property_type'].unique().tolist(),
            'period': data['period'].iloc[-1] if not data.empty else "غير متاح",
        }
        
        # Calculate trends
        if len(data) > 1:
            historical = data.groupby('period')['average_rent'].mean()
            metrics['price_trend'] = (
                (historical.iloc[-1] - historical.iloc[-2]) / historical.iloc[-2] * 100
                if len(historical) > 1 else 0
            )
            metrics['price_trend_direction'] = (
                'ارتفاع' if metrics['price_trend'] > 0 else 'انخفاض'
            )
        else:
            metrics['price_trend'] = 0
            metrics['price_trend_direction'] = 'مستقر'
        
        return metrics
    
    def _calculate_comparisons(
        self,
        neighborhood_data: pd.DataFrame,
        city_name: str | None = None,
        region_name: str | None = None
    ) -> dict[str, Any]:
        """Calculate comparisons with other neighborhoods."""
        latest_period = self.market_data['period_index'].max()
        latest_data = self.market_data[
            self.market_data['period_index'] == latest_period
        ]
        
        # City comparison
        city_avg = (
            latest_data[latest_data['city_ar'] == city_name]['average_rent'].mean()
            if city_name else latest_data['average_rent'].mean()
        )
        
        neighborhood_avg = neighborhood_data['average_rent'].mean()
        city_diff = (
            ((neighborhood_avg - city_avg) / city_avg * 100)
            if city_avg > 0 else 0
        )
        
        # Region comparison
        region_avg = (
            latest_data[latest_data['region_ar'] == region_name]['average_rent'].mean()
            if region_name else latest_data['average_rent'].mean()
        )
        
        region_diff = (
            ((neighborhood_avg - region_avg) / region_avg * 100)
            if region_avg > 0 else 0
        )
        
        return {
            'city_average': city_avg,
            'city_difference': city_diff,
            'region_average': region_avg,
            'region_difference': region_diff,
            'national_average': latest_data['average_rent'].mean(),
        }
    
    def _build_title_page(
        self,
        location_name: str,
        metrics: dict[str, Any]
    ) -> KeepTogether:
        """Build the title page."""
        elements = []
        
        # Title
        title = Paragraph(
            _ar_text(f"تقرير تحليل حي {location_name}"),
            self.styles['ArabicTitle']
        )
        elements.append(title)
        elements.append(Spacer(1, 0.3*inch))
        
        # Subtitle
        subtitle = Paragraph(
            _ar_text(f"دراسة شاملة لفرص الاستثمار العقاري"),
            self.styles['ArabicHeading']
        )
        elements.append(subtitle)
        elements.append(Spacer(1, 0.5*inch))
        
        # Key metrics
        metrics_data = [
            [_ar_text("المنطقة"), _ar_text(str(metrics.get('region', 'غير معروف')))],
            [_ar_text("المدينة"), _ar_text(str(metrics.get('city', 'غير معروف')))],
            [_ar_text("متوسط الإيجار"), f"ر.س {metrics.get('average_rent', 0):,.0f}"],
            [_ar_text("إجمالي الصفقات"), f"{metrics.get('total_deals', 0):,.0f}"],
            [_ar_text("الاتجاه السعري"), _ar_text(metrics.get('price_trend_direction', 'مستقر'))],
            [_ar_text("آخر فترة"), _ar_text(str(metrics.get('period', 'غير متاح')))],
        ]
        
        table = Table(metrics_data, colWidths=[2.5*inch, 2.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#E5F2EE')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#17211F')),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#DBE7E1')),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.5*inch))
        
        # Metadata
        metadata = Paragraph(
            _ar_text(f"تاريخ التقرير: {datetime.now().strftime('%d-%m-%Y')}"),
            self.styles['ArabicBody']
        )
        elements.append(metadata)
        
        return KeepTogether(elements)
    
    def _build_executive_summary(
        self,
        location_name: str,
        metrics: dict[str, Any]
    ) -> KeepTogether:
        """Build the executive summary section."""
        elements = []
        
        heading = Paragraph(
            _ar_text("الملخص التنفيذي"),
            self.styles['ArabicHeading']
        )
        elements.append(heading)
        elements.append(Spacer(1, 0.2*inch))
        
        # Summary text
        summary_text = f"""
        <b>موقع الحي:</b> {metrics.get('location', 'غير معروف')} في مدينة {metrics.get('city', 'غير معروف')} بمنطقة {metrics.get('region', 'غير معروف')}<br/>
        <b>حالة السوق:</b> متوسط الإيجار في الحي هو ر.س {metrics.get('average_rent', 0):,.0f} مع اتجاه {metrics.get('price_trend_direction', 'مستقر')}<br/>
        <b>نشاط السوق:</b> تم تسجيل {metrics.get('total_deals', 0):,.0f} صفقة إيجارية<br/>
        <b>أنواع العقارات:</b> يشمل الحي عدة أنواع من العقارات<br/>
        """
        
        summary = Paragraph(summary_text, self.styles['ArabicBody'])
        elements.append(summary)
        
        return KeepTogether(elements)
    
    def _build_market_analysis(
        self,
        data: pd.DataFrame,
        metrics: dict[str, Any]
    ) -> KeepTogether:
        """Build the market analysis section."""
        elements = []
        
        heading = Paragraph(
            _ar_text("تحليل السوق"),
            self.styles['ArabicHeading']
        )
        elements.append(heading)
        elements.append(Spacer(1, 0.2*inch))
        
        # Price distribution by property type
        if not data.empty:
            price_by_type = data.groupby('property_type')['average_rent'].agg(['mean', 'count']).round(0)
            
            if not price_by_type.empty:
                table_data = [
                    [_ar_text("نوع العقار"), _ar_text("متوسط الإيجار"), _ar_text("عدد الصفقات")]
                ]
                
                for idx, (property_type, row) in enumerate(price_by_type.iterrows()):
                    table_data.append([
                        _ar_text(str(property_type)),
                        f"ر.س {row['mean']:,.0f}",
                        f"{int(row['count'])}"
                    ])
                
                table = Table(table_data, colWidths=[2*inch, 2*inch, 1.5*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0B6B53')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ]))
                
                elements.append(table)
        
        return KeepTogether(elements)
    
    def _build_comparisons(
        self,
        comparisons: dict[str, Any],
        metrics: dict[str, Any]
    ) -> KeepTogether:
        """Build the comparisons section."""
        elements = []
        
        heading = Paragraph(
            _ar_text("المقارنات مع مناطق أخرى"),
            self.styles['ArabicHeading']
        )
        elements.append(heading)
        elements.append(Spacer(1, 0.2*inch))
        
        comparison_text = f"""
        <b>المتوسط الوطني:</b> ر.س {comparisons.get('national_average', 0):,.0f}<br/>
        <b>مقارنة مع المدينة:</b> أعلى بـ {comparisons.get('city_difference', 0):.1f}% من متوسط المدينة<br/>
        <b>مقارنة مع المنطقة:</b> أعلى بـ {comparisons.get('region_difference', 0):.1f}% من متوسط المنطقة<br/>
        """
        
        comparison = Paragraph(comparison_text, self.styles['ArabicBody'])
        elements.append(comparison)
        
        return KeepTogether(elements)
    
    def _build_recommendations(
        self,
        metrics: dict[str, Any]
    ) -> KeepTogether:
        """Build the recommendations section."""
        elements = []
        
        heading = Paragraph(
            _ar_text("التوصيات"),
            self.styles['ArabicHeading']
        )
        elements.append(heading)
        elements.append(Spacer(1, 0.2*inch))
        
        recommendations = """
        <b>1. الفرص المحتملة:</b><br/>
        تحليل السوق يشير إلى فرص استثمارية محتملة في هذا الحي<br/>
        <br/>
        <b>2. المخاطر المحتملة:</b><br/>
        يجب الانتباه لتقلبات السوق والعوامل الاقتصادية المؤثرة<br/>
        <br/>
        <b>3. التوصيات:</b><br/>
        يفضل إجراء دراسة تفصيلية قبل اتخاذ قرار استثماري<br/>
        """
        
        rec = Paragraph(recommendations, self.styles['ArabicBody'])
        elements.append(rec)
        
        return KeepTogether(elements)
    
    def _generate_empty_report_pdf(self, location_name: str) -> bytes:
        """Generate a report indicating no data available."""
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=A4,
            title=f"تقرير {location_name} - بدون بيانات"
        )
        
        story = [
            Paragraph(
                _ar_text(f"عذراً - لا توجد بيانات متاحة لـ {location_name}"),
                self.styles['ArabicHeading']
            ),
            Spacer(1, 0.5*inch),
            Paragraph(
                _ar_text("الرجاء التأكد من اسم الحي والمحاولة مجدداً"),
                self.styles['ArabicBody']
            ),
        ]
        
        doc.build(story)
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()
    
    def get_available_locations(self) -> list[str]:
        """Get list of available neighborhoods/locations."""
        return sorted(self.market_data['location_ar'].unique().tolist())
    
    def get_locations_by_city(self, city_name: str) -> list[str]:
        """Get locations for a specific city."""
        city_data = self.market_data[
            self.market_data['city_ar'].str.contains(city_name, case=False, na=False)
        ]
        return sorted(city_data['location_ar'].unique().tolist())
