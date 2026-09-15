from ppt.pages.chart_page import add_chart_slide
from services.report_export_service import (
    build_daily_dataframe,
    build_trend_figure,
    visible_metric_keys,
)
from utils.chart_export import save_chart


def add_api_daily_slide(
    prs,
    period_result,
    visibility,
    image_prefix,
    period_label,
):
    if not visibility.get(
        "sections", {}
    ).get("daily_trend", True):
        return None

    metrics = visible_metric_keys(visibility)
    if not metrics:
        return None

    df = build_daily_dataframe(
        (period_result or {}).get("target_daily", [])
    )
    if df.empty:
        return None

    fig = build_trend_figure(
        df,
        metrics,
        x_column="date",
        x_tickformat="%m/%d",
    )
    if fig is None:
        return None

    path = save_chart(
        fig,
        f"{image_prefix}_daily",
        width=1600,
        height=900,
        scale=2,
    )

    return add_chart_slide(
        prs,
        f"デイリー推移：{period_label}",
        path,
    )
