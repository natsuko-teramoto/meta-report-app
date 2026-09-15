from pathlib import Path
import re
import shutil

import pandas as pd
from dateutil.relativedelta import relativedelta

from report.report_builder import (
    build_report,
    build_detail_columns,
    build_place_columns,
)
from report.report_config import DELIVERY_REPORT_CONFIG
from ppt.create_ppt import create_meta_report_ppt
from utils.chart_export import generate_ppt_images
from charts.age_chart import (
    create_age_chart,
    build_age_gender_table_df,
)
from charts.gender_chart import create_gender_chart
from charts.chart_theme import (
    GENDER_LABEL_MAP,
    GENDER_COLOR_MAP,
    AGE_ORDER,
)
from charts.placement_chart import create_placement_summary


PROJECT_DIR = Path(__file__).resolve().parents[1]

MONTHLY_DIR = PROJECT_DIR / "data" / "monthly"
MONTHLY_PLACE_DIR = PROJECT_DIR / "data" / "monthly_place"
DAILY_AGE_GENDER_DIR = PROJECT_DIR / "data" / "daily_age_gender"

NUMERIC_COLUMNS = [
    "インプレッション",
    "リーチ",
    "クリック(すべて)",
    "リンククリック",
    "ランディングページビュー",
]

# 同じ月の複数医院を処理するとき、Excelを毎回読み直さない
_REPORT_DATA_CACHE = {}


def normalize_campaign_name(value) -> str:
    """キャンペーン名の改行・タブ・連続空白を1つの半角スペースに統一する。"""
    if pd.isna(value):
        return ""
    return " ".join(str(value).split())


def get_month_label(file_name: str) -> str | None:
    match = re.search(r"【(\d{4}年\d{1,2}月)】", file_name)
    if match:
        return match.group(1)
    return None


def sort_month_label(month_label: str) -> tuple[int, int]:
    year = int(month_label.split("年")[0])
    month = int(month_label.split("年")[1].replace("月", ""))
    return year, month


def get_latest_month_label() -> str:
    labels = []

    for file_path in MONTHLY_DIR.glob("*.xlsx"):
        month_label = get_month_label(file_path.name)
        if month_label:
            labels.append(month_label)

    if not labels:
        raise RuntimeError("data/monthly に対象月を判定できるExcelがありません。")

    return sorted(labels, key=sort_month_label)[-1]


def read_excel_file(file_path: Path) -> pd.DataFrame:
    df = pd.read_excel(file_path)
    df["取込ファイル"] = file_path.name
    df.columns = df.columns.astype(str).str.strip()
    return df


def read_excel_files(files: list[Path]) -> pd.DataFrame:
    dfs = []

    for file_path in files:
        dfs.append(read_excel_file(file_path))

    if not dfs:
        return pd.DataFrame()

    result = pd.concat(dfs, ignore_index=True)
    result.columns = result.columns.astype(str).str.strip()
    return result


def normalize_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for col in NUMERIC_COLUMNS:
        if col not in df.columns:
            continue

        values = (
            df[col]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.replace("%", "", regex=False)
            .str.strip()
        )

        df[col] = pd.to_numeric(
            values,
            errors="coerce",
        ).fillna(0)

    return df


def load_report_data(selected_month: str):
    if selected_month in _REPORT_DATA_CACHE:
        return _REPORT_DATA_CACHE[selected_month]

    monthly_files = list(MONTHLY_DIR.glob("*.xlsx"))
    monthly_place_files = list(MONTHLY_PLACE_DIR.glob("*.xlsx"))
    daily_age_gender_files = list(DAILY_AGE_GENDER_DIR.glob("*.xlsx"))

    monthly_file = next(
        file_path
        for file_path in monthly_files
        if selected_month in file_path.name
    )

    monthly_place_file = next(
        file_path
        for file_path in monthly_place_files
        if selected_month in file_path.name
    )

    daily_age_gender_file = next(
        file_path
        for file_path in daily_age_gender_files
        if selected_month in file_path.name
    )

    monthly_df = normalize_numeric_columns(
        read_excel_file(monthly_file)
    )

    monthly_place_df = normalize_numeric_columns(
        read_excel_file(monthly_place_file)
    )

    daily_df = normalize_numeric_columns(
        read_excel_file(daily_age_gender_file)
    )

    monthly_all_df = normalize_numeric_columns(
        read_excel_files(monthly_files)
    )

    daily_all_df = normalize_numeric_columns(
        read_excel_files(daily_age_gender_files)
    )

    for df in [monthly_df, monthly_all_df]:
        df["レポート開始日"] = pd.to_datetime(
            df["レポート開始日"],
            errors="coerce",
        )
        df["レポート終了日"] = pd.to_datetime(
            df["レポート終了日"],
            errors="coerce",
        )
        df.dropna(
            subset=["レポート開始日", "レポート終了日"],
            inplace=True,
        )

    for df in [daily_df, daily_all_df]:
        df["レポート開始日"] = pd.to_datetime(
            df["レポート開始日"],
            errors="coerce",
        )
        df.dropna(
            subset=["レポート開始日"],
            inplace=True,
        )

    result = {
        "monthly_df": monthly_df,
        "monthly_place_df": monthly_place_df,
        "daily_df": daily_df,
        "monthly_all_df": monthly_all_df,
        "daily_all_df": daily_all_df,
    }

    _REPORT_DATA_CACHE[selected_month] = result
    return result


def build_analysis_section(
    period_key: str,
    period_label: str,
    analysis_df: pd.DataFrame,
    metrics: list[str],
    ppt_chart_figures: dict,
):
    metric_items = {}

    for metric in metrics:
        if metric not in analysis_df.columns:
            continue

        age_key = f"{period_key}_age_{metric}"
        gender_key = f"{period_key}_gender_{metric}"

        age_fig = create_age_chart(
            analysis_df,
            metric,
            metric,
            AGE_ORDER,
            GENDER_COLOR_MAP,
        )

        gender_fig = create_gender_chart(
            analysis_df,
            metric,
            GENDER_LABEL_MAP,
            GENDER_COLOR_MAP,
        )

        ppt_chart_figures[age_key] = {
            "fig": age_fig,
            "width": 800,
            "height": 450,
            "scale": 3,
        }

        ppt_chart_figures[gender_key] = {
            "fig": gender_fig,
            "width": 650,
            "height": 450,
            "scale": 3,
        }

        metric_items[metric] = {
            "age_image_key": age_key,
            "gender_image_key": gender_key,
            "table": build_age_gender_table_df(
                analysis_df,
                metric,
                AGE_ORDER,
            ),
        }

    if not metric_items:
        return None

    return {
        "period_key": period_key,
        "period_label": period_label,
        "metrics": metric_items,
    }


def build_ppt_report_for_campaign(
    selected_month: str,
    selected_campaign: str,
):
    selected_campaign = normalize_campaign_name(selected_campaign)
    data = load_report_data(selected_month)

    monthly_df = data["monthly_df"]
    monthly_place_df = data["monthly_place_df"]
    daily_df = data["daily_df"]
    monthly_all_df = data["monthly_all_df"]
    daily_all_df = data["daily_all_df"]

    # 配信用固定仕様
    selected_summary_metrics = list(
        DELIVERY_REPORT_CONFIG["summary_metrics"]
    )

    analysis_metrics = list(
        DELIVERY_REPORT_CONFIG["analysis_metrics"]
    )

    filtered_df = monthly_df[
        monthly_df["キャンペーン名"].map(normalize_campaign_name) == selected_campaign
    ].copy()

    daily_filtered_df = daily_df[
        daily_df["キャンペーン名"].map(normalize_campaign_name) == selected_campaign
    ].copy()

    if filtered_df.empty:
        raise RuntimeError(
            f"対象月データにキャンペーンが見つかりません: {selected_campaign}"
        )

    end_date = monthly_df["レポート終了日"].max().date()

    cumulative_df = monthly_all_df[
        (monthly_all_df["キャンペーン名"].map(normalize_campaign_name) == selected_campaign)
        & (monthly_all_df["レポート終了日"].dt.date <= end_date)
    ].copy()

    adset_daily_all_df = daily_all_df[
        daily_all_df["キャンペーン名"].map(normalize_campaign_name) == selected_campaign
    ].copy()

    if adset_daily_all_df.empty:
        raise RuntimeError(
            f"デイリー累計データにキャンペーンが見つかりません: {selected_campaign}"
        )

    start_from_first = (
        adset_daily_all_df["レポート開始日"]
        .min()
        .date()
    )

    days_from_start = (
        end_date - start_from_first
    ).days + 1

    current_month_start = monthly_df["レポート開始日"].min()
    prev_month_start = current_month_start - relativedelta(months=1)
    prev_month_end = current_month_start - relativedelta(days=1)

    prev_df = monthly_all_df[
        (monthly_all_df["キャンペーン名"].map(normalize_campaign_name) == selected_campaign)
        & (
            monthly_all_df["レポート開始日"].dt.date
            >= prev_month_start.date()
        )
        & (
            monthly_all_df["レポート終了日"].dt.date
            <= prev_month_end.date()
        )
    ].copy()

    # -----------------------------
    # 表示場所
    # -----------------------------
    place_summary = create_placement_summary(
        monthly_place_df,
        selected_campaign,
    )

    place_cols = build_place_columns(
        selected_summary_metrics
    )

    # -----------------------------
    # 掲載開始からの詳細
    # -----------------------------
    detail_df = cumulative_df.copy()

    detail_df["期間No"] = (
        detail_df["レポート開始日"].dt.year * 100
        + detail_df["レポート開始日"].dt.month
    )

    detail_df["期間開始日"] = (
        detail_df["レポート開始日"].dt.date
    )

    detail_df["期間終了日"] = (
        detail_df["レポート終了日"].dt.date
    )

    detail_df["期間"] = (
        detail_df["期間開始日"].astype(str)
        + " 〜 "
        + detail_df["期間終了日"].astype(str)
    )

    detail_summary = (
        detail_df
        .groupby(
            ["期間No", "期間"],
            as_index=False,
        )
        .agg({
            "インプレッション": "sum",
            "リーチ": "sum",
            "クリック(すべて)": "sum",
            # 元データ上は保持するが、配信用表示列には使わない
            "リンククリック": "sum",
            "ランディングページビュー": "sum",
        })
    )

    # クリック（すべて）の表示値
    detail_summary["リンククリック（すべて）"] = detail_summary.apply(
        lambda row: (
            f'{row["クリック(すべて)"]:,.0f} '
            f'({row["クリック(すべて)"] / row["リーチ"] * 100:.2f}%)'
            if row["リーチ"] > 0
            else f'{row["クリック(すべて)"]:,.0f}'
        ),
        axis=1,
    )

    detail_summary["インプレッション"] = detail_summary.apply(
        lambda row: (
            f'{row["インプレッション"]:,.0f} '
            f'({row["インプレッション"] / row["リーチ"]:.2f})'
            if row["リーチ"] > 0
            else f'{row["インプレッション"]:,.0f}'
        ),
        axis=1,
    )

    detail_summary["リーチ"] = detail_summary["リーチ"].map(
        lambda x: f"{x:,.0f}"
    )

    detail_summary = detail_summary.sort_values(
        "期間No",
        ascending=False,
    )

    detail_cols = build_detail_columns(
        selected_summary_metrics
    )

    # -----------------------------
    # 年齢・性別分析
    # 必要な3指標だけ生成
    # -----------------------------
    ppt_chart_figures = {}
    analysis_sections = []

    monthly_section = build_analysis_section(
        period_key="monthly",
        period_label=selected_month,
        analysis_df=daily_filtered_df,
        metrics=analysis_metrics,
        ppt_chart_figures=ppt_chart_figures,
    )

    if monthly_section is not None:
        analysis_sections.append(monthly_section)

    if DELIVERY_REPORT_CONFIG["show_cumulative_analysis"]:
        cumulative_analysis_df = adset_daily_all_df[
            (
                adset_daily_all_df["レポート開始日"].dt.date
                >= start_from_first
            )
            & (
                adset_daily_all_df["レポート開始日"].dt.date
                <= end_date
            )
        ].copy()

        cumulative_section = build_analysis_section(
            period_key="cumulative",
            period_label="累計",
            analysis_df=cumulative_analysis_df,
            metrics=analysis_metrics,
            ppt_chart_figures=ppt_chart_figures,
        )

        if cumulative_section is not None:
            analysis_sections.append(cumulative_section)

    # -----------------------------
    # レポート本体
    # -----------------------------
    report = build_report(
        selected_month=selected_month,
        selected_campaign=selected_campaign,
        start_from_first=start_from_first,
        days_from_start=days_from_start,
        filtered_df=filtered_df,
        cumulative_df=cumulative_df,
        prev_df=prev_df,
        place_summary=(
            place_summary[place_cols]
            if DELIVERY_REPORT_CONFIG["show_place"]
            else None
        ),
        detail_summary=(
            detail_summary[detail_cols].head(12)
            if DELIVERY_REPORT_CONFIG["show_detail"]
            else None
        ),
        analysis_sections=analysis_sections,
        show_place=DELIVERY_REPORT_CONFIG["show_place"],
        show_awareness=DELIVERY_REPORT_CONFIG["show_awareness"],
        show_action=DELIVERY_REPORT_CONFIG["show_action"],
        show_gender=True,
        show_age=True,
        show_detail=DELIVERY_REPORT_CONFIG["show_detail"],
        selected_summary_metrics=selected_summary_metrics,
    )

    # 年齢・性別グラフだけ画像化
    # 推移グラフは作らない
    generate_ppt_images(ppt_chart_figures)

    ppt_path = Path(
        create_meta_report_ppt(report)
    )

    if not ppt_path.is_absolute():
        ppt_path = PROJECT_DIR / ppt_path

    return ppt_path


def create_report_ppt_for_campaign(
    selected_month: str,
    selected_campaign: str,
    output_ppt_path: Path | None = None,
) -> Path:
    ppt_path = build_ppt_report_for_campaign(
        selected_month=selected_month,
        selected_campaign=selected_campaign,
    )

    if output_ppt_path is None:
        return ppt_path

    output_ppt_path = Path(output_ppt_path)
    output_ppt_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    shutil.copy2(
        ppt_path,
        output_ppt_path,
    )

    return output_ppt_path

