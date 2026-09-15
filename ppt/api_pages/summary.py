from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE

from ppt.common.layout import add_blank_slide
from ppt.common.text import add_textbox, add_section_title
from ppt.common.cards import add_info_card, add_metric_card
from ppt.common.theme import (
    PAGE_LEFT,
    PAGE_TOP,
    SLIDE_TITLE_SIZE,
    CARD_WIDTH,
    CARD_HEIGHT,
    CARD_GAP,
    SUMMARY_INFO_CARD_HEIGHT,
)

from services.report_export_service import (
    build_basic_info,
    build_metric_rows,
    value_from_ad,
    customer_name_from_ad,
)



SUMMARY_ACCENT_BLUE = RGBColor(0, 120, 215)

def _api_section_title(slide, text, left, top, width, height):
    accent = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.RECTANGLE, left, top, Pt(4), height
    )
    accent.fill.solid()
    accent.fill.fore_color.rgb = SUMMARY_ACCENT_BLUE
    accent.line.fill.background()
    return add_textbox(
        slide, text, left + Pt(10), top, width - Pt(10), height,
        font_size=Pt(14), bold=True,
    )

def add_api_summary_slide(
    prs,
    ad_row,
    report_period,
    period_result,
    visibility,
):
    slide = add_blank_slide(prs)

    add_textbox(
        slide,
        "Meta広告レポート",
        PAGE_LEFT,
        PAGE_TOP,
        Inches(6),
        Inches(0.4),
        font_size=SLIDE_TITLE_SIZE,
        bold=True,
    )

    basic_visibility = visibility.get("basic", {})
    customer_name = customer_name_from_ad(ad_row, default="―")

    if basic_visibility.get("customer_name", True):
        customer_text = (
            f"{customer_name} 様"
            if customer_name != "―"
            else "―"
        )
        add_textbox(
            slide,
            customer_text,
            PAGE_LEFT,
            Inches(0.82),
            Inches(12.0),
            Inches(0.48),
            font_size=Pt(20),
            bold=True,
        )

    basic_items = dict(
        build_basic_info(
            ad_row,
            report_period,
            visibility,
        )
    )

    first_row = [
        ("配信開始日", basic_items.get("配信開始日")),
        ("累計配信日数", basic_items.get("累計配信日数")),
        ("レポート集計期間", basic_items.get("レポート集計期間")),
    ]
    first_row = [
        (label, value)
        for label, value in first_row
        if value is not None
    ]

    if first_row:
        _api_section_title(
            slide,
            "配信概要",
            PAGE_LEFT,
            Inches(1.60),
            Inches(3.0),
            Inches(0.30),
        )
        _add_info_row(
            slide,
            first_row,
            top=Inches(1.93),
        )

    second_row = [
        ("訴求内容", basic_items.get("訴求内容")),
        ("配信エリア", basic_items.get("配信エリア")),
        ("年齢", basic_items.get("年齢")),
        ("性別", basic_items.get("性別")),
    ]
    second_row = [
        (label, value)
        for label, value in second_row
        if value is not None
    ]

    second_title_top = Inches(2.78) if first_row else Inches(1.60)
    second_card_top = Inches(3.11) if first_row else Inches(1.93)

    if second_row:
        _api_section_title(
            slide,
            "広告設定",
            PAGE_LEFT,
            second_title_top,
            Inches(3.0),
            Inches(0.30),
        )
        _add_info_row(
            slide,
            second_row,
            top=second_card_top,
        )

    metrics = build_metric_rows(
        (period_result or {}).get("target", {}),
        visibility,
        include_change=True,
        comparison=(period_result or {}).get("comparison", {}),
    )

    metric_title_top = Inches(4.06) if second_row else (
        Inches(2.91) if first_row else Inches(1.73)
    )
    metric_card_top = metric_title_top + Inches(0.37)

    if metrics:
        _api_section_title(
            slide,
            "設定期間 配信結果",
            PAGE_LEFT,
            metric_title_top,
            Inches(3.0),
            Inches(0.30),
        )
        _add_metric_row(
            slide,
            metrics,
            metric_card_top,
        )

    cumulative = build_metric_rows(
        (period_result or {}).get("cumulative", {}),
        visibility,
    )

    if cumulative:
        cumulative_title_top = (
            metric_card_top + Inches(1.18)
            if metrics
            else metric_title_top
        )
        cumulative_card_top = cumulative_title_top + Inches(0.37)

        _api_section_title(
            slide,
            "配信開始からの累計",
            PAGE_LEFT,
            cumulative_title_top,
            Inches(3.0),
            Inches(0.30),
        )
        _add_metric_row(
            slide,
            cumulative,
            cumulative_card_top,
        )

    return slide


def _add_info_row(slide, items, top):
    if not items:
        return

    count = len(items)
    usable_width = Inches(12.0)
    gap = Inches(0.16)
    card_width = (
        usable_width - gap * (count - 1)
    ) / count

    for index, (label, value) in enumerate(items):
        left = PAGE_LEFT + index * (card_width + gap)
        add_info_card(
            slide,
            label,
            value if value not in (None, "") else "―",
            left,
            top,
            card_width,
            SUMMARY_INFO_CARD_HEIGHT,
        )


def _to_optional_number(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = (
        str(value)
        .replace(",", "")
        .replace("回", "")
        .replace("%", "")
        .strip()
    )
    if not text or text in {"―", "-", "None"}:
        return None

    try:
        return float(text)
    except ValueError:
        return None


def _add_metric_row(slide, items, top):
    if not items:
        return

    count = len(items)

    if count == 5:
        width = CARD_WIDTH
        gap = CARD_GAP
    else:
        usable_width = Inches(12.0)
        gap = CARD_GAP
        width = (
            usable_width - gap * (count - 1)
        ) / count

    for index, item in enumerate(items):
        left = PAGE_LEFT + index * (width + gap)

        add_metric_card(
            slide,
            item["label"],
            item["value"],
            left,
            top,
            width,
            CARD_HEIGHT,
            frequency=(
                _to_optional_number(item.get("extra"))
                if item["key"] == "impressions"
                else None
            ),
            reach_rate=(
                _to_optional_number(item.get("extra"))
                if item["key"] in {
                    "clicks",
                    "link_clicks",
                    "landing_page_views",
                }
                else None
            ),
            change=_to_optional_number(item.get("change")),
        )
