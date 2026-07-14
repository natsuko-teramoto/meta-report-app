from pptx.util import Inches
from ppt.common.layout import add_blank_slide
from ppt.common.text import add_textbox
from ppt.common.table import add_table
from ppt.common.theme import (
    PAGE_LEFT,
    PAGE_TOP,
    SLIDE_TITLE_SIZE,

    DETAIL_TITLE_WIDTH,
    DETAIL_TITLE_HEIGHT,

    DETAIL_EMPTY_LEFT,
    DETAIL_EMPTY_TOP,
    DETAIL_EMPTY_WIDTH,
    DETAIL_EMPTY_HEIGHT,

    DETAIL_TABLE_LEFT,
    DETAIL_TABLE_TOP,
    DETAIL_TABLE_WIDTH,
    DETAIL_TABLE_HEIGHT,
)


def add_detail_slide(prs, report):
    slide = add_blank_slide(prs)

    add_textbox(
        slide,
        "掲載開始からの詳細",
        PAGE_LEFT,
        PAGE_TOP,
        DETAIL_TITLE_WIDTH,
        DETAIL_TITLE_HEIGHT,
        font_size=SLIDE_TITLE_SIZE,
        bold=True,
)

    detail = report.get("detail")

    if detail is None or detail.empty:
        add_textbox(
            slide,
            "詳細データがありません",
            DETAIL_EMPTY_LEFT,
            DETAIL_EMPTY_TOP,
            DETAIL_EMPTY_WIDTH,
            DETAIL_EMPTY_HEIGHT,
        )
        return slide

    add_table(
        slide,
        detail,
        DETAIL_TABLE_LEFT,
        DETAIL_TABLE_TOP,
        DETAIL_TABLE_WIDTH,
        DETAIL_TABLE_HEIGHT,
        max_rows=12,
    )
    return slide
