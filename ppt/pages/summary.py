from ppt.common.layout import add_blank_slide
from ppt.common.text import (
    add_textbox,
    add_section_title,
)

from ppt.common.cards import (
    add_info_card,
    add_metric_card,
)
from ppt.common.table import add_table
from ppt.common.theme import (
    PAGE_LEFT,
    PAGE_TOP,
    SLIDE_TITLE_SIZE,
    SLIDE_SUBTITLE_SIZE,

    CARD_WIDTH,
    CARD_HEIGHT,
    CARD_GAP,

    SUMMARY_CONDITION_TITLE_TOP,
    SUMMARY_CONDITION_CARD_TOP,
    SUMMARY_METRIC_TITLE_TOP,
    SUMMARY_METRIC_CARD_TOP,
    SUMMARY_CUMULATIVE_TITLE_TOP,
    SUMMARY_CUMULATIVE_CARD_TOP,
    SUMMARY_PLACEMENT_TITLE_TOP,
    SUMMARY_PLACEMENT_TABLE_TOP,
    SUMMARY_PLACEMENT_TABLE_WIDTH,
    SUMMARY_PLACEMENT_TABLE_HEIGHT,
    SUMMARY_INFO_CARD_TOP,

    SUMMARY_START_DATE_LEFT,
    SUMMARY_ELAPSED_DAYS_LEFT,

    SUMMARY_INFO_CARD_WIDTH,
    SUMMARY_INFO_CARD_HEIGHT,
)

from pptx.util import Inches
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.util import Pt


def add_summary_slide(prs, report):

    slide = add_blank_slide(prs)
    summary = report["summary"]

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

    add_info_card(
        slide,
        "掲載開始日",
        summary["start_date"],
        SUMMARY_START_DATE_LEFT,
        SUMMARY_INFO_CARD_TOP,
        SUMMARY_INFO_CARD_WIDTH,
        SUMMARY_INFO_CARD_HEIGHT,
    )

    add_info_card(
        slide,
        "累計掲載日数",
        summary["elapsed_days"],
        SUMMARY_ELAPSED_DAYS_LEFT,
        SUMMARY_INFO_CARD_TOP,
        SUMMARY_INFO_CARD_WIDTH,
        SUMMARY_INFO_CARD_HEIGHT,
    )

    # 数値実績
    add_section_title(
        slide,
        "数値実績",
        PAGE_LEFT,
        SUMMARY_METRIC_TITLE_TOP,
        Inches(3),
        Inches(0.3),
    )

    metric_left = PAGE_LEFT
    metric_top = SUMMARY_METRIC_CARD_TOP
    metric_width = CARD_WIDTH
    metric_gap = CARD_GAP

    for i, item in enumerate(summary["metrics"]):
        add_metric_card(
            slide,
            item["label"],
            item["value"],
            metric_left + (metric_width + metric_gap) * i,
            metric_top,
            metric_width,
            CARD_HEIGHT,
            frequency=item.get("frequency"),
            reach_rate=item.get("reach_rate"),
            change=item.get("change"),
        )

    # 掲載開始からの累計
    add_section_title(
        slide,
        "掲載開始からの累計",
        PAGE_LEFT,
        SUMMARY_CUMULATIVE_TITLE_TOP,
        Inches(3),
        Inches(0.3),
    )

    cum_left = PAGE_LEFT
    cum_top = SUMMARY_CUMULATIVE_CARD_TOP
    cum_width = CARD_WIDTH
    cum_gap = CARD_GAP

    for i, item in enumerate(summary["cumulative_metrics"]):
        add_metric_card(
            slide,
            item["label"],
            item["value"],
            cum_left + (cum_width + cum_gap) * i,
            cum_top,
            cum_width,
            CARD_HEIGHT,
            frequency=item.get("frequency"),
            reach_rate=item.get("reach_rate"),
        )

    # 表示場所分析
    placement = report.get("placement")

    if placement is not None and not placement.empty:

        add_section_title(
            slide,
            "表示場所分析",
            PAGE_LEFT,
            SUMMARY_PLACEMENT_TITLE_TOP,
            Inches(3),
            Inches(0.3),
        )

        table_cols = list(placement.columns)

        add_table(
            slide,
            placement[table_cols],
            PAGE_LEFT,
            SUMMARY_PLACEMENT_TABLE_TOP,
            SUMMARY_PLACEMENT_TABLE_WIDTH,
            SUMMARY_PLACEMENT_TABLE_HEIGHT,
        )

    return slide