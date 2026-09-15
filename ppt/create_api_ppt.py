from pathlib import Path

from ppt.common.layout import create_presentation
from ppt.api_pages.summary import add_api_summary_slide
from ppt.api_pages.metric_analysis import add_api_age_gender_slides
from ppt.api_pages.placement import add_api_placement_slide
from ppt.api_pages.daily import add_api_daily_slide
from ppt.api_pages.cumulative import add_api_cumulative_gap_slide
from services.report_export_service import (
    format_period_label,
    value_from_ad,
    customer_name_from_ad,
)

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def create_api_meta_report_ppt(
    ad_row,
    report_period,
    period_result,
    visibility,
    report_key="report",
):
    if ad_row is None:
        raise ValueError("広告データがありません。")
    if report_period is None:
        raise ValueError("レポート期間がありません。")
    if period_result is None:
        raise ValueError("Meta API取得結果がありません。")

    prs = create_presentation()

    ad_id = value_from_ad(ad_row, "ad_id", default="ad")
    safe_ad_id = (
        str(ad_id)
        .replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
    )

    image_prefix = f"api_{report_key}_{safe_ad_id}"
    period_label = format_period_label(report_period)

    add_api_summary_slide(
        prs,
        ad_row,
        report_period,
        period_result,
        visibility,
    )

    if visibility.get("sections", {}).get("period_age_gender", True):
        add_api_age_gender_slides(
            prs,
            period_result.get("target_age_gender", []),
            visibility,
            section_label=period_label,
            image_prefix=f"{image_prefix}_period",
        )

    add_api_placement_slide(
        prs,
        period_result,
        visibility,
        image_prefix,
        period_label,
    )

    add_api_daily_slide(
        prs,
        period_result,
        visibility,
        image_prefix,
        period_label,
    )

    if visibility.get("sections", {}).get("cumulative_age_gender", True):
        add_api_age_gender_slides(
            prs,
            period_result.get("cumulative_age_gender", []),
            visibility,
            section_label="累計",
            image_prefix=f"{image_prefix}_cumulative",
        )

    add_api_cumulative_gap_slide(
        prs,
        period_result,
        visibility,
        image_prefix,
    )


    customer_name = customer_name_from_ad(ad_row, default="Meta広告")
    safe_customer_name = (
        str(customer_name)
        .replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
    )

    appeal = value_from_ad(ad_row, "訴求内容", "appeal", default="広告")
    def _safe_filename_part(value):
        text = str(value or "").strip()
        for ch in '<>:"/\\|?*':
            text = text.replace(ch, "_")
        return text.rstrip(". ")
    safe_appeal = _safe_filename_part(appeal)
    file_period = (
        f"{report_period.target_start.year}年{report_period.target_start.month}月{report_period.target_start.day}日～"
        f"{report_period.target_end.year}年{report_period.target_end.month}月{report_period.target_end.day}日"
    )
    file_name = f"【Instagram広告レポート】{safe_customer_name} 様_{safe_appeal}（{file_period}）.pptx"

    save_path = OUTPUT_DIR / file_name
    prs.save(save_path)

    return save_path
