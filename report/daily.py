from ppt.pages.chart_page import add_chart_slide
from services.report_export_service import build_cumulative_gap_figure
from utils.chart_export import save_chart


def add_api_cumulative_gap_slide(
    prs,
    period_result,
    visibility,
    image_prefix,
):
    if not visibility.get(
        "sections", {}
    ).get("reach_impression_gap", True):
        return None

    fig = build_cumulative_gap_figure(
        (period_result or {}).get("cumulative", {}),
        visibility,
    )
    if fig is None:
        return None

    path = save_chart(
        fig,
        f"{image_prefix}_cumulative_reach_impressions",
        width=1500,
        height=650,
        scale=2,
    )

    return add_chart_slide(
        prs,
        "累計 リーチ・インプレッション",
        path,
    )
