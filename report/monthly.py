from pptx.util import Inches

from ppt.api_pages.common import (
    add_info_card,
    add_metric_card,
    add_section_label,
    add_title,
)
from services.report_export_service import (
    build_basic_info,
    build_metric_rows,
)


def add_api_summary_slide(
    prs,
    ad_row,
    report_period,
    period_result,
    visibility,
):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(slide, "Meta広告レポート")

    basic_items = build_basic_info(
        ad_row, report_period, visibility
    )

    if basic_items:
        add_section_label(
            slide, "基本情報",
            Inches(0.55), Inches(0.95), Inches(3)
        )

        columns = min(4, max(1, len(basic_items)))
        usable_width = 12.15
        gap = 0.12
        card_width = (usable_width - gap * (columns - 1)) / columns

        for index, (label, value) in enumerate(basic_items):
            row = index // columns
            col = index % columns
            left = Inches(
                0.55 + col * (card_width + gap)
            )
            top = Inches(
                1.30 + row * 0.86
            )
            add_info_card(
                slide,
                label,
                value,
                left,
                top,
                Inches(card_width),
            )

        info_rows = (
            len(basic_items) + columns - 1
        ) // columns

        metrics_top = Inches(
            1.30 + info_rows * 0.86 + 0.25
        )
    else:
        metrics_top = Inches(1.05)

    metrics = build_metric_rows(
        (period_result or {}).get("target", {}),
        visibility,
        include_change=True,
        comparison=(period_result or {}).get("comparison", {}),
    )

    if metrics:
        add_section_label(
            slide,
            "設定期間 配信結果",
            Inches(0.55),
            metrics_top,
            Inches(3),
        )
        _add_metric_row(
            slide,
            metrics,
            metrics_top + Inches(0.35),
        )

        cumulative = build_metric_rows(
            (period_result or {}).get("cumulative", {}),
            visibility,
        )

        if cumulative:
            cumulative_top = metrics_top + Inches(1.45)
            add_section_label(
                slide,
                "配信開始からの累計",
                Inches(0.55),
                cumulative_top,
                Inches(3.5),
            )
            _add_metric_row(
                slide,
                cumulative,
                cumulative_top + Inches(0.35),
            )

    return slide


def _add_metric_row(slide, items, top):
    count = len(items)
    if not count:
        return

    usable_width = 12.15
    gap = 0.12
    width = (
        usable_width - gap * (count - 1)
    ) / count

    for index, item in enumerate(items):
        left = Inches(
            0.55 + index * (width + gap)
        )
        add_metric_card(
            slide,
            item,
            left,
            top,
            Inches(width),
        )
