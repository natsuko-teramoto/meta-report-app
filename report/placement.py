from utils.chart_export import save_chart
from ppt.pages.metric_analysis import add_metric_analysis_slide
from services.report_export_service import (
    METRIC_CONFIG,
    build_age_gender_figures,
)


def add_api_age_gender_slides(
    prs,
    rows,
    visibility,
    section_label,
    image_prefix,
):
    if not rows:
        return

    for metric_key, config in METRIC_CONFIG.items():
        if not visibility.get(
            "metrics", {}
        ).get(metric_key, True):
            continue

        bar, pie, table_df = build_age_gender_figures(
            rows,
            metric_key,
        )

        if bar is None:
            continue

        age_path = save_chart(
            bar,
            f"{image_prefix}_{metric_key}_age",
            width=1500,
            height=850,
            scale=2,
        )

        gender_path = age_path
        if pie is not None:
            gender_path = save_chart(
                pie,
                f"{image_prefix}_{metric_key}_gender",
                width=850,
                height=850,
                scale=2,
            )

        add_metric_analysis_slide(
            prs,
            f"{config['label']}分析：{section_label}",
            {
                "age_image": age_path,
                "gender_image": gender_path,
                "table": table_df,
            },
        )
