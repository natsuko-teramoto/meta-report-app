from pathlib import Path

import pandas as pd
import streamlit as st
import time

# =========================================================
# データフォルダ
# =========================================================

PROJECT_DIR = Path(__file__).resolve().parents[1]

MONTHLY_DIR = (
    PROJECT_DIR
    / "data"
    / "monthly"
)

MONTHLY_PLACE_DIR = (
    PROJECT_DIR
    / "data"
    / "monthly_place"
)

DAILY_AGE_GENDER_DIR = (
    PROJECT_DIR
    / "data"
    / "daily_age_gender"
)


# =========================================================
# 数値列
# =========================================================

NUMERIC_COLUMNS = [
    "インプレッション",
    "リーチ",
    "クリック(すべて)",
    "リンククリック",
    "ランディングページビュー",
]


# =========================================================
# Excel読込
# =========================================================

@st.cache_data(show_spinner=False)
def _read_excel_files(directory):
    """
    指定フォルダ内のExcelをすべて読み込む。
    """

    files = sorted(
        directory.glob("*.xlsx")
    )

    dfs = []

    for file_path in files:

        df = pd.read_excel(file_path)

        df.columns = (
            df.columns
            .astype(str)
            .str.strip()
        )

        df["取込ファイル"] = (
            file_path.name
        )

        dfs.append(df)

    if not dfs:
        return pd.DataFrame()

    return pd.concat(
        dfs,
        ignore_index=True,
    )


# =========================================================
# 数値正規化
# =========================================================

def _normalize_numeric_columns(df):

    df = df.copy()

    for col in NUMERIC_COLUMNS:

        if col not in df.columns:
            continue

        values = (
            df[col]
            .astype(str)
            .str.replace(
                ",",
                "",
                regex=False,
            )
            .str.replace(
                "%",
                "",
                regex=False,
            )
            .str.strip()
        )

        df[col] = pd.to_numeric(
            values,
            errors="coerce",
        ).fillna(0)

    return df


# =========================================================
# 日付正規化
# =========================================================

def _normalize_dates(df):

    df = df.copy()

    for col in [
        "レポート開始日",
        "レポート終了日",
    ]:

        if col in df.columns:

            df[col] = pd.to_datetime(
                df[col],
                errors="coerce",
            )

    return df


# =========================================================
# キャンペーン抽出
# =========================================================

def _normalize_campaign_name(value):
    """
    キャンペーン名の照合専用。

    改行・タブ・連続する空白など、
    表記上の差だけを吸収する。
    元データ自体は変更しない。
    """

    if pd.isna(value):
        return ""

    return " ".join(
        str(value).split()
    )


def _filter_campaign(
    df,
    campaign_name,
):

    if df.empty:
        return df.copy()

    if "キャンペーン名" not in df.columns:
        return pd.DataFrame()

    target_name = (
        _normalize_campaign_name(
            campaign_name
        )
    )

    normalized_names = (
        df["キャンペーン名"]
        .map(_normalize_campaign_name)
    )

    return df[
        normalized_names == target_name
    ].copy()


# =========================================================
# 合計
# =========================================================

def _total(
    df,
    column,
):

    if df.empty:
        return 0

    if column not in df.columns:
        return 0

    return int(
        pd.to_numeric(
            df[column],
            errors="coerce",
        )
        .fillna(0)
        .sum()
    )


# =========================================================
# 率
# =========================================================

def _reach_rate(
    value,
    reach,
):

    if not reach:
        return 0.0

    return (
        value
        / reach
        * 100
    )


# =========================================================
# 新レポート形式へ変換
# =========================================================

def _build_metric_result(df):

    impressions = _total(
        df,
        "インプレッション",
    )

    reach = _total(
        df,
        "リーチ",
    )

    clicks = _total(
        df,
        "クリック(すべて)",
    )

    link_clicks = _total(
        df,
        "リンククリック",
    )

    landing_page_views = _total(
        df,
        "ランディングページビュー",
    )

    frequency = (
        impressions / reach
        if reach
        else 0.0
    )

    return {
        "impressions": impressions,
        "reach": reach,
        "frequency": frequency,

        "clicks": clicks,
        "click_rate": _reach_rate(
            clicks,
            reach,
        ),

        "link_clicks": link_clicks,
        "link_click_rate": _reach_rate(
            link_clicks,
            reach,
        ),

        "landing_page_views":
            landing_page_views,

        "landing_page_view_rate":
            _reach_rate(
                landing_page_views,
                reach,
            ),
    }


# =========================================================
# 年齢・性別
# =========================================================

def _build_age_gender_rows(df):

    if df.empty:
        return []

    required = [
        "年齢",
        "性別",
    ]

    if not all(
        col in df.columns
        for col in required
    ):
        return []

    gender_map = {
        "女性": "female",
        "男性": "male",
        "不明": "unknown",
        "female": "female",
        "male": "male",
        "unknown": "unknown",
    }

    work = df.copy()

    work["gender"] = (
        work["性別"]
        .astype(str)
        .map(gender_map)
        .fillna(
            work["性別"].astype(str)
        )
    )

    work["age"] = (
        work["年齢"]
        .astype(str)
    )

    group_columns = [
        "age",
        "gender",
    ]

    available_metrics = [
        col
        for col in NUMERIC_COLUMNS
        if col in work.columns
    ]

    if not available_metrics:
        return []

    grouped = (
        work.groupby(
            group_columns,
            dropna=False,
        )[available_metrics]
        .sum()
        .reset_index()
    )

    rows = []

    for _, row in grouped.iterrows():

        rows.append({
            "age":
                row["age"],

            "gender":
                row["gender"],

            "impressions":
                float(
                    row.get(
                        "インプレッション",
                        0,
                    )
                ),

            "reach":
                float(
                    row.get(
                        "リーチ",
                        0,
                    )
                ),

            "clicks":
                float(
                    row.get(
                        "クリック(すべて)",
                        0,
                    )
                ),

            "link_clicks":
                float(
                    row.get(
                        "リンククリック",
                        0,
                    )
                ),

            "landing_page_views":
                float(
                    row.get(
                        "ランディングページビュー",
                        0,
                    )
                ),
        })

    return rows

def _normalize_legacy_placement(
    publisher_platform,
    platform_position,
):
    """
    旧Excelの日本語配置名を
    Meta API側と同じ値へ揃える。
    """

    publisher = str(
        publisher_platform or ""
    ).strip().lower()

    position = str(
        platform_position or ""
    ).strip().lower()

    combined = (
        f"{publisher} {position}"
    )

    # -------------------------
    # プラットフォーム
    # -------------------------

    if "instagram" in combined:
        publisher = "instagram"

    elif "facebook" in combined:
        publisher = "facebook"

    # -------------------------
    # 配置
    # -------------------------

    if (
        "フィード" in position
        or "feed" in position
    ):
        position = "feed"

    elif (
        "ストーリー" in position
        or "story" in position
        or "stories" in position
    ):
        position = "story"

    elif (
        "リール" in position
        or "reel" in position
    ):
        position = "reels"

    elif (
        "発見ホーム" in position
        or "explore_home" in position
    ):
        position = "explore_home"

    elif (
        "発見" in position
        or "explore" in position
    ):
        position = "explore"

    return (
        publisher,
        position,
    )

# =========================================================
# 表示場所
# =========================================================

def _build_placement_rows(df):

    if df.empty:
        return []

    rows = []

    for _, row in df.iterrows():

        impressions = float(
            row.get(
                "インプレッション",
                0,
            )
            or 0
        )

        reach = float(
            row.get(
                "リーチ",
                0,
            )
            or 0
        )

        clicks = float(
            row.get(
                "クリック(すべて)",
                0,
            )
            or 0
        )

        link_clicks = float(
            row.get(
                "リンククリック",
                0,
            )
            or 0
        )

        landing_page_views = float(
            row.get(
                "ランディングページビュー",
                0,
            )
            or 0
        )

        frequency = (
            impressions / reach
            if reach
            else 0.0
        )

        publisher_platform, platform_position = (
            _normalize_legacy_placement(
                row.get(
                    "プラットフォーム",
                    "",
                ),
                row.get(
                    "配置",
                    "",
                ),
            )
        )

        rows.append({
            "publisher_platform":
                publisher_platform,

            "platform_position":
                platform_position,

            "impressions":
                impressions,

            "reach":
                reach,

            "frequency":
                frequency,

            "clicks":
                clicks,

            "click_rate":
                _reach_rate(
                    clicks,
                    reach,
                ),

            "link_clicks":
                link_clicks,

            "link_click_rate":
                _reach_rate(
                    link_clicks,
                    reach,
                ),

            "landing_page_views":
                landing_page_views,

            "landing_page_view_rate":
                _reach_rate(
                    landing_page_views,
                    reach,
                ),
        })

    return rows


# =========================================================
# デイリー推移
# =========================================================

def _build_daily_rows(df):

    if df.empty:
        return []

    if "レポート開始日" not in df.columns:
        return []

    rows = []

    grouped = df.groupby(
        "レポート開始日",
        dropna=False,
    )

    for report_date, group in grouped:

        if pd.isna(report_date):
            continue

        rows.append({
            "date":
                report_date.strftime(
                    "%Y-%m-%d"
                ),

            "impressions":
                _total(
                    group,
                    "インプレッション",
                ),

            "reach":
                _total(
                    group,
                    "リーチ",
                ),

            "clicks":
                _total(
                    group,
                    "クリック(すべて)",
                ),

            "link_clicks":
                _total(
                    group,
                    "リンククリック",
                ),

            "landing_page_views":
                _total(
                    group,
                    "ランディングページビュー",
                ),
        })

    return rows

# =========================================================
# 月次推移
# =========================================================

def _build_monthly_rows(df):

    if df.empty:
        return []

    if "レポート開始日" not in df.columns:
        return []

    work = df.copy()

    work["month"] = (
        work["レポート開始日"]
        .dt.to_period("M")
    )

    rows = []

    for month, group in work.groupby(
        "month"
    ):

        if pd.isna(month):
            continue

        impressions = _total(
            group,
            "インプレッション",
        )

        reach = _total(
            group,
            "リーチ",
        )

        clicks = _total(
            group,
            "クリック(すべて)",
        )

        link_clicks = _total(
            group,
            "リンククリック",
        )

        landing_page_views = _total(
            group,
            "ランディングページビュー",
        )

        frequency = (
            impressions / reach
            if reach
            else 0.0
        )

        rows.append({
            "date_start":
                month.start_time.strftime(
                    "%Y-%m-%d"
                ),

            "date_stop":
                month.end_time.strftime(
                    "%Y-%m-%d"
                ),

            "impressions":
                impressions,

            "reach":
                reach,

            "frequency":
                frequency,

            "clicks":
                clicks,

            "link_clicks":
                link_clicks,

            "landing_page_views":
                landing_page_views,
        })

    return rows

def _read_daily_excel_files_fast(directory):
    """
    daily_age_gender専用。

    Excel群に変更がなければ、
    前回作成したPickleを読み込む。
    Excelが追加・更新された場合だけ
    全Excelを読み直してPickleを作り直す。
    """

    files = sorted(
        directory.glob("*.xlsx")
    )

    if not files:
        return pd.DataFrame()

    cache_path = (
        directory
        / "_daily_cache.pkl"
    )

    signature_path = (
        directory
        / "_daily_cache_signature.txt"
    )

    current_signature = "\n".join(
        f"{file_path.name}|"
        f"{file_path.stat().st_mtime_ns}|"
        f"{file_path.stat().st_size}"
        for file_path in files
    )

    if (
        cache_path.exists()
        and signature_path.exists()
    ):
        saved_signature = (
            signature_path.read_text(
                encoding="utf-8"
            )
        )

        if (
            saved_signature
            == current_signature
        ):
            return pd.read_pickle(
                cache_path
            )

    # Excelに変更があったときだけ
    # 全件読み直す
    df = _read_excel_files(
        directory
    )

    df.to_pickle(
        cache_path
    )

    signature_path.write_text(
        current_signature,
        encoding="utf-8",
    )

    return df

# =========================================================
# レガシーレポート本体
# =========================================================

def build_legacy_period_result(
    ad_row,
    report_period=None,
):
    """
    旧Excelデータから、
    新report_service.build_period_result()
    と同じ構造のデータを返す。

    レガシー広告では自由期間指定を使わず、
    そのキャンペーンの最新月を対象月とする。
    """

    if ad_row is None:
        raise ValueError(
            "広告情報がありません。"
        )

    campaign_name = str(
        ad_row.get(
            "キャンペーン名",
            "",
        )
        or ""
    ).strip()

    if not campaign_name:
        raise ValueError(
            "レガシー広告の"
            "キャンペーン名がありません。"
        )

    # -----------------------------------------------------
    # 指定月
    # -----------------------------------------------------

    if report_period is None:
        raise ValueError(
            "レポート期間がありません。"
        )

    target_year = report_period.target_start.year
    target_month = report_period.target_start.month

    target_month_end = (
        pd.Timestamp(
            year=target_year,
            month=target_month,
            day=1,
        )
        + pd.offsets.MonthEnd(1)
    )

    target_month_label = (
        f"{target_year}年{target_month}月"
    )

    # -----------------------------------------------------
    # まずファイル名だけで対象月の存在確認
    # Excelはまだ開かない
    # -----------------------------------------------------

    monthly_files = list(
        MONTHLY_DIR.glob("*.xlsx")
    )

    has_target_month = any(
        f"【{target_month_label}】"
        in file_path.name
        for file_path in monthly_files
    )

    if not has_target_month:
        raise ValueError(
            f"{target_month_label}の"
            "レガシーデータがありません。"
        )
    
    t0 = time.perf_counter()

    # -----------------------------------------------------
    # 全Excel読込＋正規化
    # -----------------------------------------------------

    monthly_all = _read_excel_files(
        MONTHLY_DIR
    )
    print(
        f"[LEGACY] monthly読込: "
        f"{time.perf_counter() - t0:.2f}秒"
    )

    t1 = time.perf_counter()

    placement_all = _read_excel_files(
        MONTHLY_PLACE_DIR
    )
    print(
        f"[LEGACY] placement読込: "
        f"{time.perf_counter() - t1:.2f}秒"
    )

    t2 = time.perf_counter()

    daily_all = _read_daily_excel_files_fast(
        DAILY_AGE_GENDER_DIR
    )
    print(
        f"[LEGACY] daily読込: "
        f"{time.perf_counter() - t2:.2f}秒"
    )

    t3 = time.perf_counter()

    monthly_all = (
        _normalize_numeric_columns(
            _normalize_dates(
                monthly_all
            )
        )
    )

    placement_all = (
        _normalize_numeric_columns(
            _normalize_dates(
                placement_all
            )
        )
    )

    daily_all = (
        _normalize_numeric_columns(
            _normalize_dates(
                daily_all
            )
        )
    )

    print(
        f"[LEGACY] 3データ正規化: "
        f"{time.perf_counter() - t3:.2f}秒"
    )

    # -----------------------------------------------------
    # キャンペーン完全一致
    # -----------------------------------------------------

    monthly_campaign = (
        _filter_campaign(
            monthly_all,
            campaign_name,
        )
    )

    placement_campaign = (
        _filter_campaign(
            placement_all,
            campaign_name,
        )
    )

    daily_campaign = (
        _filter_campaign(
            daily_all,
            campaign_name,
        )
    )

    if monthly_campaign.empty:
        raise ValueError(
            "旧Excelにキャンペーンが"
            "見つかりません："
            f"{campaign_name}"
        )

    # -----------------------------------------------------
    # 指定された月を対象月にする
    # -----------------------------------------------------

    if report_period is None:
        raise ValueError(
            "レポート期間がありません。"
        )

    target_year = (
        report_period.target_start.year
    )

    target_month = (
        report_period.target_start.month
    )

    target_monthly = (
        monthly_campaign[
            (
                monthly_campaign[
                    "レポート開始日"
                ].dt.year
                == target_year
            )
            &
            (
                monthly_campaign[
                    "レポート開始日"
                ].dt.month
                == target_month
            )
        ].copy()
    )

    if target_monthly.empty:
        raise ValueError(
            f"{target_year}年{target_month}月の"
            "レガシーデータがありません。"
        )


    # -----------------------------------------------------
    # 前月
    # -----------------------------------------------------

    previous_month = (
        target_month_end.to_period("M")
        - 1
    )

    comparison_monthly = (
        monthly_campaign[
            monthly_campaign[
                "レポート開始日"
            ].dt.to_period("M")
            == previous_month
        ].copy()
    )

    # -----------------------------------------------------
    # 累計
    # -----------------------------------------------------

    cumulative_monthly = (
        monthly_campaign[
            monthly_campaign[
                "レポート開始日"
            ]
            <= target_month_end
        ].copy()
    )

    # -----------------------------------------------------
    # 対象月の日次
    # -----------------------------------------------------

    target_daily = (
        daily_campaign[
            (
                daily_campaign[
                    "レポート開始日"
                ].dt.year
                == target_year
            )
            &
            (
                daily_campaign[
                    "レポート開始日"
                ].dt.month
                == target_month
            )
        ].copy()
        if not daily_campaign.empty
        else pd.DataFrame()
    )

    # -----------------------------------------------------
    # 累計の日次
    # -----------------------------------------------------

    cumulative_daily = (
        daily_campaign[
            daily_campaign[
                "レポート開始日"
            ]
            <= target_month_end
        ].copy()
        if not daily_campaign.empty
        else pd.DataFrame()
    )

    # -----------------------------------------------------
    # 対象月の配置
    # -----------------------------------------------------

    target_placement = (
        placement_campaign[
            (
                placement_campaign[
                    "レポート開始日"
                ].dt.year
                == target_year
            )
            &
            (
                placement_campaign[
                    "レポート開始日"
                ].dt.month
                == target_month
            )
        ].copy()
        if not placement_campaign.empty
        else pd.DataFrame()
    )

    # -----------------------------------------------------
    # 新レポートと同じ構造で返す
    # -----------------------------------------------------

    return {
        "target":
            _build_metric_result(
                target_monthly
            ),

        "comparison":
            _build_metric_result(
                comparison_monthly
            ),

        "cumulative":
            _build_metric_result(
                cumulative_monthly
            ),

        "target_age_gender":
            _build_age_gender_rows(
                target_daily
            ),

        "cumulative_age_gender":
            _build_age_gender_rows(
                cumulative_daily
            ),

        "target_placement":
            _build_placement_rows(
                target_placement
            ),

        "target_daily":
            _build_daily_rows(
                target_daily
            ),

        "cumulative_monthly":
            _build_monthly_rows(
                cumulative_monthly
            ),

        # レガシー専用情報
        "legacy": True,

        "legacy_target_month":
            f"{target_year}年"
            f"{target_month}月",
    }