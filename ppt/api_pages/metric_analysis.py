from pathlib import Path

from utils.chart_export import save_chart
from ppt.common.layout import add_blank_slide
from ppt.common.text import add_textbox, add_section_title
from ppt.common.metric_table import add_metric_table
from ppt.common.theme import (
    PAGE_LEFT, PAGE_TOP, TITLE_SIZE,
    METRIC_TITLE_WIDTH, METRIC_TITLE_HEIGHT,
    METRIC_GENDER_LEFT, METRIC_AGE_LEFT, METRIC_AGE_TOP, METRIC_GENDER_TOP,
    METRIC_AGE_WIDTH, METRIC_GENDER_WIDTH,
    METRIC_TABLE_LEFT, METRIC_TABLE_TOP, METRIC_TABLE_WIDTH, METRIC_TABLE_HEIGHT,
    METRIC_TABLE_TITLE_TOP, METRIC_TABLE_TITLE_WIDTH, METRIC_TABLE_TITLE_HEIGHT,
)
from services.report_export_service import METRIC_CONFIG, build_age_gender_figures

def _add_api_metric_analysis_slide(prs, title, age_image, gender_image, table_df):
    slide = add_blank_slide(prs)
    add_textbox(slide, title, PAGE_LEFT, PAGE_TOP, METRIC_TITLE_WIDTH, METRIC_TITLE_HEIGHT, font_size=TITLE_SIZE, bold=True)
    slide.shapes.add_picture(str(Path(age_image)), METRIC_AGE_LEFT, METRIC_AGE_TOP, width=METRIC_AGE_WIDTH)
    slide.shapes.add_picture(str(Path(gender_image)), METRIC_GENDER_LEFT, METRIC_GENDER_TOP, width=METRIC_GENDER_WIDTH)
    if table_df is not None and not table_df.empty:
        add_section_title(slide, "年齢・性別分析", PAGE_LEFT, METRIC_TABLE_TITLE_TOP, METRIC_TABLE_TITLE_WIDTH, METRIC_TABLE_TITLE_HEIGHT)
        add_metric_table(slide, table_df, METRIC_TABLE_LEFT, METRIC_TABLE_TOP, METRIC_TABLE_WIDTH, METRIC_TABLE_HEIGHT)
    return slide

def add_api_age_gender_slides(prs, rows, visibility, section_label, image_prefix):
    if not rows:
        return
    for metric_key, config in METRIC_CONFIG.items():
        if not visibility.get("metrics", {}).get(metric_key, True):
            continue
        bar, pie, table_df = build_age_gender_figures(rows, metric_key)
        if bar is None:
            continue
        # Excel版 app.py と同じ画像出力サイズ
        age_path = save_chart(bar, f"{image_prefix}_{metric_key}_age", width=800, height=450, scale=3)
        gender_path = age_path
        if pie is not None:
            gender_path = save_chart(pie, f"{image_prefix}_{metric_key}_gender", width=650, height=450, scale=3)
        _add_api_metric_analysis_slide(prs, f"{config['label']}分析：{section_label}", age_path, gender_path, table_df)
