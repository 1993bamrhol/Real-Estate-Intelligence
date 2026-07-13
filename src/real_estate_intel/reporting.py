from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from io import BytesIO
from pathlib import Path
from typing import Mapping


def build_investment_memo_html(
    *,
    property_details: Mapping[str, object],
    assumptions: Mapping[str, object],
    analysis: Mapping[str, object],
    stress_test: Mapping[str, object],
    market_context: Mapping[str, object],
    forecast: Mapping[str, object] | None = None,
    alternatives: object | None = None,
) -> str:
    decision_labels = {"buy": "شراء", "negotiate": "تفاوض", "reject": "رفض"}
    confidence_labels = {"high": "عالية", "medium": "متوسطة", "low": "منخفضة"}
    decision = decision_labels.get(str(analysis.get("decision", "")), "غير محدد")
    confidence = confidence_labels.get(str(stress_test.get("confidence", "")), "منخفضة")
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    scenarios = stress_test.get("scenarios", [])

    scenario_rows = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('label', '')))}</td>"
        f"<td>{_money(row.get('annual_cash_flow'))}</td>"
        f"<td>{_number(row.get('net_yield_pct'), 2)}%</td>"
        f"<td>{_ratio(row.get('dscr'))}</td>"
        f"<td>{_number(row.get('deal_score'), 1)}/100</td>"
        f"<td>{decision_labels.get(str(row.get('decision', '')), 'غير محدد')}</td>"
        "</tr>"
        for row in scenarios
    )

    return f"""<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>مذكرة قرار استثماري</title>
<style>
body {{ font-family: Tahoma, Arial, sans-serif; margin: 36px; color: #17211f; background: #f6f8f7; }}
.sheet {{ max-width: 980px; margin: auto; background: white; padding: 32px; border: 1px solid #dbe7e1; }}
h1, h2 {{ color: #0b6b53; }}
.decision {{ padding: 18px; background: #e5f2ee; border-right: 5px solid #0b6b53; font-size: 20px; }}
.grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 18px 0; }}
.metric {{ border: 1px solid #dbe7e1; padding: 12px; }}
.metric small {{ color: #66736e; display: block; }}
.metric strong {{ font-size: 18px; }}
table {{ width: 100%; border-collapse: collapse; margin: 16px 0; }}
th, td {{ border: 1px solid #dbe7e1; padding: 9px; text-align: right; }}
th {{ background: #eef4f1; }}
.note {{ color: #66736e; font-size: 13px; line-height: 1.8; }}
@media print {{ body {{ background: white; margin: 0; }} .sheet {{ border: 0; }} }}
</style>
</head>
<body><main class="sheet">
<h1>مذكرة قرار استثماري للعقار</h1>
<p class="note">تاريخ الإنشاء: {generated_at} | مصدر السوق: بيانات الإيجار الرسمية المتاحة داخل المنصة.</p>
<div class="decision"><strong>القرار: {decision}</strong> — درجة الصفقة {_number(analysis.get('deal_score'), 1)}/100 — ثقة {confidence}</div>

<h2>بيانات العقار</h2>
<table><tbody>
<tr><th>المدينة</th><td>{_text(property_details.get('city'))}</td><th>الحي</th><td>{_text(property_details.get('district'))}</td></tr>
<tr><th>نوع العقار</th><td>{_text(property_details.get('property_type'))}</td><th>المساحة</th><td>{_number(property_details.get('area'), 0)} م²</td></tr>
<tr><th>السعر المطلوب</th><td>{_money(property_details.get('price'))}</td><th>الفترة السوقية</th><td>{_text(market_context.get('period'))}</td></tr>
</tbody></table>

<h2>مؤشرات القرار</h2>
<section class="grid">
<div class="metric"><small>العائد الصافي</small><strong>{_number(analysis.get('net_yield_pct'), 2)}%</strong></div>
<div class="metric"><small>التدفق النقدي السنوي</small><strong>{_money(analysis.get('annual_cash_flow'))}</strong></div>
<div class="metric"><small>العائد على النقد</small><strong>{_number(analysis.get('cash_on_cash_pct'), 2)}%</strong></div>
<div class="metric"><small>تغطية القسط DSCR</small><strong>{_ratio(analysis.get('dscr'))}</strong></div>
<div class="metric"><small>أقصى سعر شراء آمن</small><strong>{_money(stress_test.get('risk_adjusted_max_offer'))}</strong></div>
<div class="metric"><small>إشغال التعادل</small><strong>{_number(analysis.get('break_even_occupancy_pct'), 1)}%</strong></div>
</section>

<h2>الافتراضات</h2>
<table><tbody>
<tr><th>الإيجار السنوي المرجعي</th><td>{_money(assumptions.get('annual_rent'))}</td><th>الإشغال</th><td>{_number(assumptions.get('occupancy_pct'), 1)}%</td></tr>
<tr><th>المصاريف التشغيلية</th><td>{_number(assumptions.get('operating_expense_pct'), 1)}%</td><th>الصيانة السنوية</th><td>{_money(assumptions.get('annual_maintenance'))}</td></tr>
<tr><th>الدفعة الأولى</th><td>{_number(assumptions.get('down_payment_pct'), 1)}%</td><th>نسبة التمويل</th><td>{_number(assumptions.get('interest_rate_pct'), 2)}%</td></tr>
</tbody></table>

<h2>اختبار الضغط</h2>
<table><thead><tr><th>السيناريو</th><th>التدفق السنوي</th><th>العائد الصافي</th><th>DSCR</th><th>الدرجة</th><th>القرار</th></tr></thead>
<tbody>{scenario_rows}</tbody></table>

<p class="note">هذه المذكرة أداة دعم قرار وليست تقييمًا عقاريًا معتمدًا أو توصية مالية نهائية. يجب التحقق من حالة العقار، الملكية، التمويل، والمصاريف الفعلية قبل الشراء.</p>
</main></body></html>"""


def build_investment_memo_pdf(
    *,
    property_details: Mapping[str, object],
    assumptions: Mapping[str, object],
    analysis: Mapping[str, object],
    stress_test: Mapping[str, object],
    market_context: Mapping[str, object],
    forecast: Mapping[str, object] | None = None,
    alternatives: object | None = None,
) -> bytes:
    """Build a shareable Arabic PDF decision memo."""
    import arabic_reshaper
    import pandas as pd
    from bidi.algorithm import get_display
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    font_path = _arabic_font_path()
    font_name = "ArabicMemoFont"
    if font_name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(font_name, str(font_path)))

    def rtl(value: object) -> str:
        return get_display(arabic_reshaper.reshape(str(value or "-")))

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="Investment Decision Memo",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ArabicTitle",
        parent=styles["Title"],
        fontName=font_name,
        fontSize=20,
        leading=28,
        alignment=TA_RIGHT,
        textColor=colors.HexColor("#0b6b53"),
    )
    heading_style = ParagraphStyle(
        "ArabicHeading",
        parent=styles["Heading2"],
        fontName=font_name,
        fontSize=13,
        leading=19,
        alignment=TA_RIGHT,
        textColor=colors.HexColor("#0b6b53"),
        spaceBefore=8,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "ArabicBody",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=9,
        leading=15,
        alignment=TA_RIGHT,
    )
    story: list[object] = [Paragraph(rtl("مذكرة قرار استثماري للعقار"), title_style)]
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    story.append(Paragraph(rtl(f"تاريخ الإنشاء: {generated_at}"), body_style))
    story.append(Spacer(1, 5 * mm))

    decision_labels = {"buy": "شراء", "negotiate": "تفاوض", "reject": "رفض"}
    confidence_labels = {"high": "عالية", "medium": "متوسطة", "low": "منخفضة"}
    decision = decision_labels.get(str(analysis.get("decision", "")), "غير محدد")
    confidence = confidence_labels.get(str(stress_test.get("confidence", "")), "منخفضة")
    story.append(
        Paragraph(
            rtl(f"القرار: {decision} | درجة الصفقة {_number(analysis.get('deal_score'), 1)}/100 | الثقة {confidence}"),
            heading_style,
        )
    )

    def add_table(title: str, rows: list[list[object]], widths: list[float] | None = None) -> None:
        story.append(Paragraph(rtl(title), heading_style))
        shaped = [[Paragraph(rtl(cell), body_style) for cell in row] for row in rows]
        table = Table(shaped, colWidths=widths, hAlign="RIGHT", repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), font_name),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5f2ee")),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b7c9c1")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(table)

    add_table(
        "بيانات العقار",
        [
            ["القيمة", "البيان"],
            [property_details.get("city"), "المدينة"],
            [property_details.get("district"), "الحي"],
            [property_details.get("property_type"), "نوع العقار"],
            [f"{_number(property_details.get('area'), 0)} م²", "المساحة"],
            [_money(property_details.get("price")), "السعر المطلوب"],
            [market_context.get("period", "-"), "الفترة السوقية"],
        ],
        [95 * mm, 65 * mm],
    )
    add_table(
        "مؤشرات القرار",
        [
            ["القيمة", "المؤشر"],
            [f"{_number(analysis.get('net_yield_pct'), 2)}%", "العائد الصافي"],
            [_money(analysis.get("annual_cash_flow")), "التدفق النقدي السنوي"],
            [f"{_number(analysis.get('cash_on_cash_pct'), 2)}%", "العائد على النقد"],
            [_ratio(analysis.get("dscr")), "تغطية القسط DSCR"],
            [_money(stress_test.get("risk_adjusted_max_offer")), "أقصى سعر شراء آمن"],
            [f"{_number(analysis.get('break_even_occupancy_pct'), 1)}%", "إشغال التعادل"],
        ],
        [95 * mm, 65 * mm],
    )

    if forecast and forecast.get("ready"):
        forecast_confidence = confidence_labels.get(str(forecast.get("confidence")), "منخفضة")
        add_table(
            "توقع سنة مقبلة",
            [
                ["القيمة", "المؤشر"],
                [forecast.get("target_period", "-"), "فترة التوقع"],
                [_money(forecast.get("forecast_rent")), "الإيجار المتوقع - محايد"],
                [f"{_number(forecast.get('rent_change_pct'), 1)}%", "تغير الإيجار المتوقع"],
                [f"{_number(forecast.get('demand_change_pct'), 1)}%", "تغير الطلب المتوقع"],
                [forecast_confidence, "ثقة التوقع"],
            ],
            [95 * mm, 65 * mm],
        )

    alternative_frame = alternatives if isinstance(alternatives, pd.DataFrame) else pd.DataFrame()
    if not alternative_frame.empty:
        rows = [["السبب", "المخاطرة", "العائد", "الحي"]]
        for _, row in alternative_frame.head(3).iterrows():
            rows.append(
                [
                    row.get("why_ar", "-"),
                    f"{_number(row.get('risk_score'), 0)}/100",
                    f"{_number(row.get('gross_yield_pct'), 2)}%",
                    row.get("neighborhood", "-"),
                ]
            )
        add_table("أفضل البدائل", rows, [60 * mm, 30 * mm, 30 * mm, 40 * mm])

    story.append(Spacer(1, 5 * mm))
    story.append(
        Paragraph(
            rtl(
                "هذه المذكرة أداة دعم قرار وليست تقييمًا عقاريًا معتمدًا أو ضمانًا للتوقع. "
                "تحقق من حالة العقار والملكية والتمويل والمصاريف الفعلية قبل الشراء."
            ),
            body_style,
        )
    )
    document.build(story)
    return buffer.getvalue()


def _arabic_font_path() -> Path:
    candidates = [
        Path(__file__).resolve().parents[2] / "assets" / "fonts" / "DejaVuSans.ttf",
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/dejavu/DejaVuSans.ttf"),
        Path("C:/Windows/Fonts/tahoma.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise RuntimeError("No Arabic-capable TrueType font was found for PDF generation.")


def _text(value: object) -> str:
    return escape(str(value or "-"))


def _money(value: object) -> str:
    return f"{_as_float(value):,.0f} ر.س"


def _number(value: object, digits: int) -> str:
    return f"{_as_float(value):,.{digits}f}"


def _ratio(value: object) -> str:
    number = _as_float(value)
    return "بدون تمويل" if number == float("inf") else f"{number:.2f}x"


def _as_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
