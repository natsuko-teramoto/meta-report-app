import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from dateutil.relativedelta import relativedelta
from report.report_builder import (
    build_report,
    build_summary_metrics,
    build_detail_columns,
    build_place_columns,
    build_awareness_chart_columns,
    build_action_chart_columns,
    build_cumulative_awareness_chart_columns,
    build_cumulative_action_chart_columns,
    build_analysis_metrics,
)
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
from charts.line_chart import (
    create_awareness_chart,
    create_action_chart,
)
from charts.placement_chart import create_placement_summary

st.set_page_config(
    page_title="Meta広告レポート",
    layout="wide"
)

st.title("Meta広告レポート")

MONTHLY_DIR = Path("data/monthly")
MONTHLY_PLACE_DIR = Path("data/monthly_place")
DAILY_AGE_GENDER_DIR = Path("data/daily_age_gender")

def get_month_label(file_name):
    import re
    match = re.search(r"【(\d{4}年\d{1,2}月)】", file_name)
    if match:
        return match.group(1)
    return None

def sort_month_label(month_label):
    year = int(month_label.split("年")[0])
    month = int(month_label.split("年")[1].replace("月", ""))
    return year, month

@st.cache_data
def read_excel_file(file_path):
    df = pd.read_excel(file_path)
    df["取込ファイル"] = file_path.name
    return df

monthly_files = list(MONTHLY_DIR.glob("*.xlsx"))

month_options = []

for file in monthly_files:
    month_label = get_month_label(file.name)
    if month_label:
        month_options.append(month_label)

month_options = sorted(
    list(set(month_options)),
    key=sort_month_label
)

st.sidebar.header("条件選択")
if st.sidebar.button("キャッシュクリア"):
    st.cache_data.clear()
    st.rerun()

selected_month = st.sidebar.selectbox(
    "対象月",
    month_options,
    index=len(month_options) - 1
)

monthly_file = next(
    file for file in MONTHLY_DIR.glob("*.xlsx")
    if selected_month in file.name
)

monthly_place_file = next(
    file for file in MONTHLY_PLACE_DIR.glob("*.xlsx")
    if selected_month in file.name
)

daily_age_gender_file = next(
    file for file in DAILY_AGE_GENDER_DIR.glob("*.xlsx")
    if selected_month in file.name
)

monthly_df = read_excel_file(monthly_file)
monthly_place_df = read_excel_file(monthly_place_file)
daily_df = read_excel_file(daily_age_gender_file)

@st.cache_data
def read_excel_files(files):
    dfs = []
    for file in files:
        df = pd.read_excel(file)
        df["取込ファイル"] = file.name
        dfs.append(df)

    if not dfs:
        return pd.DataFrame()

    return pd.concat(dfs, ignore_index=True)

monthly_all_df = read_excel_files(monthly_files)

monthly_place_files = list(MONTHLY_PLACE_DIR.glob("*.xlsx"))
monthly_place_all_df = read_excel_files(monthly_place_files)

daily_age_gender_files = list(DAILY_AGE_GENDER_DIR.glob("*.xlsx"))
daily_all_df = read_excel_files(daily_age_gender_files)

monthly_all_df.columns = monthly_all_df.columns.str.strip()
monthly_place_all_df.columns = monthly_place_all_df.columns.str.strip()
daily_all_df.columns = daily_all_df.columns.str.strip()

monthly_df.columns = monthly_df.columns.str.strip()
monthly_place_df.columns = monthly_place_df.columns.str.strip()
daily_df.columns = daily_df.columns.str.strip()

campaigns = sorted(monthly_df["キャンペーン名"].dropna().astype(str).unique())

selected_campaign = st.sidebar.selectbox(
    "医院・キャンペーンを選択",
    campaigns
)

st.sidebar.markdown("---")
st.sidebar.markdown("## 表示設定")

st.sidebar.markdown("### 広告概要")
show_campaign_name = st.sidebar.checkbox(
    "キャンペーン名を表示",
    value=True
)

show_start_date = st.sidebar.checkbox(
    "掲載開始日を表示",
    value=True
)

show_elapsed_days = st.sidebar.checkbox(
    "累計掲載日数を表示",
    value=True
)

st.sidebar.markdown("### 配信結果数値")
show_summary_impression = st.sidebar.checkbox(
    "インプレッション",
    value=True
)

show_summary_reach = st.sidebar.checkbox(
    "リーチ",
    value=True
)

show_summary_click = st.sidebar.checkbox(
    "クリック(すべて)",
    value=True
)

show_summary_link_click = st.sidebar.checkbox(
    "リンククリック",
    value=True
)

show_summary_lp = st.sidebar.checkbox(
    "LPビュー",
    value=True
)

selected_summary_metrics = []

if show_summary_impression:
    selected_summary_metrics.append("インプレッション")

if show_summary_reach:
    selected_summary_metrics.append("リーチ")

if show_summary_click:
    selected_summary_metrics.append("クリック(すべて)")

if show_summary_link_click:
    selected_summary_metrics.append("リンククリック")

if show_summary_lp:
    selected_summary_metrics.append("ランディングページビュー")

st.sidebar.markdown("### 年齢・性別分析グラフ")

st.sidebar.caption("表示範囲")

show_cumulative_analysis = st.sidebar.checkbox(
    "単月に加えて累計も表示",
    value=True,
    key="show_cumulative_analysis",
)

st.sidebar.caption("表示指標")
show_analysis_impression = st.sidebar.checkbox(
    "インプレッション",
    value=True,
    key="analysis_impression",
)

show_analysis_reach = st.sidebar.checkbox(
    "リーチ",
    value=True,
    key="analysis_reach",
)

show_analysis_click = st.sidebar.checkbox(
    "クリック(すべて)",
    value=True,
    key="analysis_click",
)

show_analysis_link_click = st.sidebar.checkbox(
    "リンククリック",
    value=True,
    key="analysis_link_click",
)

show_analysis_lp = st.sidebar.checkbox(
    "LPビュー",
    value=True,
    key="analysis_lp",
)

analysis_metrics = build_analysis_metrics(
    show_analysis_impression,
    show_analysis_reach,
    show_analysis_click,
    show_analysis_link_click,
    show_analysis_lp,
)

st.sidebar.markdown("### 表示場所")
show_place_table = st.sidebar.checkbox(
    "表示場所分析を表示",
    value=True
)

st.sidebar.markdown("### 掲載開始からの詳細")
show_detail_table = st.sidebar.checkbox(
    "掲載開始からの詳細を表示",
    value=True
)

st.sidebar.markdown("### デイリー推移グラフ")

show_awareness = st.sidebar.checkbox(
    "デイリー認知推移グラフを表示",
    value=True
)

show_action = st.sidebar.checkbox(
    "デイリー行動推移グラフを表示",
    value=True
)



st.sidebar.markdown("### 累計推移グラフ")
show_cumulative_awareness = st.sidebar.checkbox(
    "累計認知推移グラフを表示",
    value=True
)

show_cumulative_action = st.sidebar.checkbox(
    "累計行動推移グラフを表示",
    value=True
)

report_settings = {
    "ad_info": {},
    "metrics": {},
    "details": {},
    "graphs": {},
    "analysis": {},
}

analysis_metric_options = {
    "インプレッション": "インプレッション",
    "リーチ": "リーチ",
    "クリック(すべて)": "クリックすべて",
    "リンククリック": "リンククリック",
    "ランディングページビュー":"LPビュー",
}

monthly_df["レポート開始日"] = pd.to_datetime(
    monthly_df["レポート開始日"],
    errors="coerce"
)
monthly_df["レポート終了日"] = pd.to_datetime(
    monthly_df["レポート終了日"],
    errors="coerce"
)
monthly_df = monthly_df.dropna(
    subset=["レポート開始日", "レポート終了日"]
)

monthly_all_df["レポート開始日"] = pd.to_datetime(
    monthly_all_df["レポート開始日"],
    errors="coerce"
)
monthly_all_df["レポート終了日"] = pd.to_datetime(
    monthly_all_df["レポート終了日"],
    errors="coerce"
)
monthly_all_df = monthly_all_df.dropna(
    subset=["レポート開始日", "レポート終了日"]
)

daily_df["レポート開始日"] = pd.to_datetime(
    daily_df["レポート開始日"],
    errors="coerce"
)
daily_df = daily_df.dropna(
    subset=["レポート開始日"]
)

daily_all_df["レポート開始日"] = pd.to_datetime(
    daily_all_df["レポート開始日"],
    errors="coerce"
)
daily_all_df = daily_all_df.dropna(
    subset=["レポート開始日"]
)

# =========================
# 選択キャンペーンの分析用データ準備
# =========================

# 選択月の月次実績
filtered_df = monthly_df[
    monthly_df["キャンペーン名"] == selected_campaign
].copy()

# 選択月の年齢・性別・日別実績
daily_filtered_df = daily_df[
    daily_df["キャンペーン名"] == selected_campaign
].copy()

# 選択月の終了日
end_date = monthly_df["レポート終了日"].max().date()

# 選択キャンペーンの全期間日別データ
adset_daily_all_df = daily_all_df[
    daily_all_df["キャンペーン名"] == selected_campaign
].copy()

if adset_daily_all_df.empty:
    st.error("選択した広告セットのデイリーデータがありません。")
    st.stop()

# 掲載開始日と累計掲載日数
start_from_first = (
    adset_daily_all_df["レポート開始日"]
    .min()
    .date()
)

days_from_start = (end_date - start_from_first).days + 1

# 掲載開始から選択月終了日までの月次実績
cumulative_df = monthly_all_df[
    (monthly_all_df["キャンペーン名"] == selected_campaign)
    & (monthly_all_df["レポート終了日"].dt.date <= end_date)
].copy()

# 掲載開始から選択月終了日までの年齢・性別・日別実績
cumulative_analysis_df = adset_daily_all_df[
    (adset_daily_all_df["レポート開始日"].dt.date >= start_from_first)
    & (adset_daily_all_df["レポート開始日"].dt.date <= end_date)
].copy()

# 前月比較用データ
current_month_start = monthly_df["レポート開始日"].min()
prev_month_start = current_month_start - relativedelta(months=1)
prev_month_end = current_month_start - relativedelta(days=1)

prev_df = monthly_all_df[
    (monthly_all_df["キャンペーン名"] == selected_campaign)
    & (
        monthly_all_df["レポート開始日"].dt.date
        >= prev_month_start.date()
    )
    & (
        monthly_all_df["レポート終了日"].dt.date
        <= prev_month_end.date()
    )
].copy()

def total(df, col):
    if col not in df.columns:
        return 0
    return df[col].fillna(0).sum()

def diff_rate(current, prev):
    if prev == 0:
        return None
    return ((current - prev) / prev) * 100

# =========================
# 抽出条件
# =========================

st.subheader("抽出条件")

condition_items = []

if show_campaign_name:
    condition_items.append(("広告セット", selected_campaign))

if show_start_date:
    condition_items.append(("掲載開始日", str(start_from_first)))

if show_elapsed_days:
    condition_items.append(("累計掲載日数", f"{days_from_start} 日"))

if condition_items:
    cond_cols = st.columns(len(condition_items))

    for col, (label, value) in zip(cond_cols, condition_items):
        with col:
            st.metric(label, value)

# =========================
# 当月実績（対象期間）
# =========================

st.subheader(
    f"配信結果：{selected_month}"
)

metrics = build_summary_metrics(
    filtered_df,
    prev_df,
    selected_summary_metrics,
)

if metrics:
    cols = st.columns(len(metrics))

    for col_box, item in zip(cols, metrics):

        display_value = f'{item["value"]:,.0f}'

        if item["frequency"] is not None:
            display_value = (
                f'{item["value"]:,.0f} '
                f'({item["frequency"]:.2f})'
            )

        elif item["reach_rate"] is not None:
            display_value = (
                f'{item["value"]:,.0f} '
                f'({item["reach_rate"]:.2f}%)'
            )

        delta = None

        if item["change"] is not None:
            if item["change"] > 0:
                delta = f"前月比 ▲{item['change']:.1f}%"
            elif item["change"] < 0:
                delta = f"前月比 ▼{abs(item['change']):.1f}%"
            else:
                delta = "前月比 ±0.0%"

        col_box.metric(
            label=item["label"],
            value=display_value,
            delta=delta,
        )

else:
    st.info("配信結果の表示項目が選択されていません。")

# =========================
# 掲載開始からの累計
# =========================

st.subheader("掲載開始からの累計配信結果")

cumulative_metrics = build_summary_metrics(
    cumulative_df,
    None,
    selected_summary_metrics,
)

if cumulative_metrics:
    cum_cols = st.columns(len(cumulative_metrics))

    for col_box, item in zip(cum_cols, cumulative_metrics):

        display_value = f'{item["value"]:,.0f}'

        if item["frequency"] is not None:
            display_value = (
                f'{item["value"]:,.0f} '
                f'({item["frequency"]:.2f})'
            )

        elif item["reach_rate"] is not None:
            display_value = (
                f'{item["value"]:,.0f} '
                f'({item["reach_rate"]:.2f}%)'
            )

        col_box.metric(
            label=item["label"],
            value=display_value,
        )

else:
    st.info("累計配信結果の表示項目が選択されていません。")

st.divider()
st.subheader(
    f"年齢・性別分析：{selected_month}"
)

# PowerPointへ貼るグラフの登録場所
# ブラウザ表示用に作ったFigureを再利用する
ppt_chart_figures = {}

# =========================
# 共通設定
# =========================
awareness_metrics = [
    ("インプレッション", "インプレッション"),
    ("リーチ", "リーチ"),
]

action_metrics = [
    ("クリック（すべて）", "クリック(すべて)"),
    ("リンククリック", "リンククリック"),
    ("LPビュー","ランディングページビュー"),
]

def show_metric_analysis(
    section_title,
    metrics,
    analysis_df,
    chart_key_prefix,
):
    st.markdown(f"### {section_title}")

    for display_name, metric in metrics:

        if metric not in analysis_metrics:
            continue

        if metric not in analysis_df.columns:
            st.warning(f"{metric} 列がありません")
            continue

        st.markdown(f"**{display_name}**")

        col_age, col_gender = st.columns([7, 3])

        age_fig = create_age_chart(
            analysis_df,
            metric,
            display_name,
            AGE_ORDER,
            GENDER_COLOR_MAP,
        )

        with col_age:
            st.plotly_chart(
                age_fig,
                width="stretch",
                key=f"{chart_key_prefix}_age_{metric}",
            )

        gender_fig = create_gender_chart(
            analysis_df,
            metric,
            GENDER_LABEL_MAP,
            GENDER_COLOR_MAP,
        )

        with col_gender:
            st.plotly_chart(
                gender_fig,
                width="stretch",
                key=f"{chart_key_prefix}_gender_{metric}",
            )

        ppt_chart_figures[f"{chart_key_prefix}_age_{metric}"] = {
            "fig": age_fig,
            "width": 800,
            "height": 450,
            "scale": 3,
        }

        ppt_chart_figures[f"{chart_key_prefix}_gender_{metric}"] = {
            "fig": gender_fig,
            "width": 650,
            "height": 450,
            "scale": 3,
        }

show_metric_analysis(
    section_title="認知指標",
    metrics=awareness_metrics,
    analysis_df=daily_filtered_df,
    chart_key_prefix="monthly",
)

show_metric_analysis(
    section_title="行動指標",
    metrics=action_metrics,
    analysis_df=daily_filtered_df,
    chart_key_prefix="monthly",
)

# =========================
# 日別推移用データ
# =========================

daily_summary = daily_filtered_df.groupby(
    "レポート開始日",
    as_index=False
).agg({
    "インプレッション": "sum",
    "リーチ": "sum",
    "クリック(すべて)": "sum",
    "リンククリック": "sum",
    "ランディングページビュー": "sum"
})

awareness_chart_columns = build_awareness_chart_columns(
    selected_summary_metrics
)

action_chart_columns = build_action_chart_columns(
    selected_summary_metrics
)

def show_daily_trend_charts(
    daily_summary,
    awareness_chart_columns,
    action_chart_columns,
    show_awareness,
    show_action,
    ppt_chart_figures,
):
    if daily_summary.empty:
        st.info(
            "このキャンペーンは対象月の"
            "デイリー推移データがありません。"
        )
        return

    if show_awareness:
        fig_awareness = create_awareness_chart(
            daily_summary,
            awareness_chart_columns,
        )

        if fig_awareness is not None:
            ppt_chart_figures["awareness"] = {
                "fig": fig_awareness,
                "width": 1200,
                "height": 700,
                "scale": 2,
            }

            st.plotly_chart(
                fig_awareness,
                width="stretch",
                key="monthly_daily_awareness",
            )

    if show_action:
        fig_action = create_action_chart(
            daily_summary,
            action_chart_columns,
        )

        if fig_action is not None:
            ppt_chart_figures["action"] = {
                "fig": fig_action,
                "width": 1200,
                "height": 700,
                "scale": 2,
            }

            st.plotly_chart(
                fig_action,
                width="stretch",
                key="monthly_daily_action",
            )

place_summary = create_placement_summary(
    monthly_place_df,
    selected_campaign,
)

place_cols = build_place_columns(
    selected_summary_metrics
)

if show_place_table:
    st.subheader(
        f"表示場所分析：{selected_month}"
    )

    st.dataframe(
        place_summary[place_cols],
        width="stretch",
        hide_index=True
    )

# =========================
# 掲載開始からの詳細（月次）
# =========================


detail_df = cumulative_df.copy()

detail_df["期間No"] = (
    detail_df["レポート開始日"].dt.year * 100
    + detail_df["レポート開始日"].dt.month
)

detail_df["期間開始日"] = detail_df["レポート開始日"].dt.date
detail_df["期間終了日"] = detail_df["レポート終了日"].dt.date

detail_df["期間"] = (
    detail_df["期間開始日"].astype(str)
    + " 〜 "
    + detail_df["期間終了日"].astype(str)
)

detail_summary = (
    detail_df
    .groupby(["期間No", "期間"], as_index=False)
    .agg({
        "インプレッション": "sum",
        "リーチ": "sum",
        "クリック(すべて)": "sum",
        "リンククリック": "sum",
        "ランディングページビュー": "sum"
    })
)

# リーチ比を追加
detail_summary["リンククリック（すべて）"] = detail_summary.apply(
    lambda row: (
        f'{row["クリック(すべて)"]:,.0f} ({row["クリック(すべて)"] / row["リーチ"] * 100:.2f}%)'
        if row["リーチ"] > 0 else f'{row["クリック(すべて)"]:,.0f}'
    ),
    axis=1
)

detail_summary["リンククリック"] = detail_summary.apply(
    lambda row: (
        f'{row["リンククリック"]:,.0f} ({row["リンククリック"] / row["リーチ"] * 100:.2f}%)'
        if row["リーチ"] > 0 else f'{row["リンククリック"]:,.0f}'
    ),
    axis=1
)

detail_summary["LPビュー"] = detail_summary.apply(
    lambda row: (
        f'{row["ランディングページビュー"]:,.0f} ({row["ランディングページビュー"] / row["リーチ"] * 100:.2f}%)'
        if row["リーチ"] > 0 else f'{row["ランディングページビュー"]:,.0f}'
    ),
    axis=1
)

# 表示用の数値整形
# インプレッションにフリークエンシーを追加
detail_summary["インプレッション"] = detail_summary.apply(
    lambda row: (
        f'{row["インプレッション"]:,.0f} ({row["インプレッション"] / row["リーチ"]:.2f})'
        if row["リーチ"] > 0 else f'{row["インプレッション"]:,.0f}'
    ),
    axis=1
)

# リーチは通常表示
detail_summary["リーチ"] = detail_summary["リーチ"].map(lambda x: f"{x:,.0f}")

detail_summary = detail_summary.sort_values("期間No", ascending=False)

detail_cols = build_detail_columns(
    selected_summary_metrics
)

if show_detail_table:
    st.subheader("掲載開始からの詳細")

    st.dataframe(
        detail_summary[detail_cols],
        width="stretch",
        hide_index=True
    )
# =========================
# 累計の男女・年齢分析
# =========================

if show_cumulative_analysis:
    st.divider()
    st.subheader("年齢・性別分析：累計")
    

    if cumulative_analysis_df.empty:
        st.info("掲載開始から選択月までの年齢・性別データがありません。")
    else:
        show_metric_analysis(
            section_title="認知指標",
            metrics=awareness_metrics,
            analysis_df=cumulative_analysis_df,
            chart_key_prefix="cumulative",
        )

        show_metric_analysis(
            section_title="行動指標",
            metrics=action_metrics,
            analysis_df=cumulative_analysis_df,
            chart_key_prefix="cumulative",
        )

# =========================
# 選択月のデイリー推移
# =========================

show_daily_trend_charts(
    daily_summary=daily_summary,
    awareness_chart_columns=awareness_chart_columns,
    action_chart_columns=action_chart_columns,
    show_awareness=show_awareness,
    show_action=show_action,
    ppt_chart_figures=ppt_chart_figures,
)
        
# =========================
# 掲載開始からの累計推移
# =========================

cumulative_trend = daily_df[
    (daily_df["キャンペーン名"] == selected_campaign)
    & (daily_df["レポート開始日"].dt.date >= start_from_first)
    & (daily_df["レポート開始日"].dt.date <= end_date)
].copy()

cumulative_trend = (
    cumulative_trend
    .groupby("レポート開始日", as_index=False)
    .agg({
        "インプレッション": "sum",
        "リーチ": "sum",
        "クリック(すべて)": "sum",
        "リンククリック": "sum",
        "ランディングページビュー": "sum"
    })
)

cumulative_trend = cumulative_trend.sort_values("レポート開始日")

cumulative_trend["累計インプレッション"] = cumulative_trend["インプレッション"].cumsum()
cumulative_trend["累計リーチ"] = cumulative_trend["リーチ"].cumsum()
cumulative_trend["累計クリック(すべて)"] = cumulative_trend["クリック(すべて)"].cumsum()
cumulative_trend["累計リンククリック"] = cumulative_trend["リンククリック"].cumsum()
cumulative_trend["累計LPビュー"] = cumulative_trend["ランディングページビュー"].cumsum()

if cumulative_trend.empty:
    st.info("このキャンペーンはデイリー推移データがないため、累計推移グラフは表示できません。")
else:

    if show_cumulative_awareness:
        # 認知累計
        cum_awareness_y = build_cumulative_awareness_chart_columns(
            selected_summary_metrics
        )

        if cum_awareness_y:
            fig_cum_awareness = px.line(
                cumulative_trend,
                x="レポート開始日",
                y=cum_awareness_y,
                markers=True,
                title="累計認知推移"
            )

            fig_cum_awareness.update_traces(line=dict(width=3))

            color_map = {
                "累計インプレッション": "#4F81BD",
                "累計リーチ": "#1F497D",
            }

            for trace in fig_cum_awareness.data:
                if trace.name in color_map:
                    trace.line.color = color_map[trace.name]

            st.plotly_chart(fig_cum_awareness, width="stretch")

    if show_cumulative_action:
        # 行動累計
        cum_action_y = build_cumulative_action_chart_columns(
            selected_summary_metrics
        )

        if not cum_action_y:
            fig_cum_action = None
        else:
            
            fig_cum_action = px.line(
                cumulative_trend,
                x="レポート開始日",
                y=cum_action_y,
                markers=True,
                title="累計行動推移"
            )

            fig_cum_action.update_traces(line=dict(width=3))

            color_map = {
                "累計クリック(すべて)": "#808080",
                "累計リンククリック": "#F79646",
                "累計LPビュー": "#00B050",
            }

            for trace in fig_cum_action.data:
                if trace.name in color_map:
                    trace.line.color = color_map[trace.name]

            st.plotly_chart(fig_cum_action, width="stretch")

# =========================
# PowerPoint用 年齢・性別分析セクション
# =========================

def build_analysis_section(
    period_key,
    period_label,
    analysis_df,
    metrics,
):
    metric_items = {}

    for metric in metrics:
        metric_items[metric] = {
            "age_image_key": f"{period_key}_age_{metric}",
            "gender_image_key": f"{period_key}_gender_{metric}",
            "table": build_age_gender_table_df(
                analysis_df,
                metric,
                AGE_ORDER,
            ),
        }

    return {
        "period_key": period_key,
        "period_label": period_label,
        "metrics": metric_items,
    }


analysis_sections = [
    build_analysis_section(
        period_key="monthly",
        period_label=selected_month,
        analysis_df=daily_filtered_df,
        metrics=analysis_metrics,
    ),
]

if show_cumulative_analysis:
    analysis_sections.append(
        build_analysis_section(
            period_key="cumulative",
            period_label="累計",
            analysis_df=cumulative_analysis_df,
            metrics=analysis_metrics,
        )
    )



report = build_report(
    selected_month=selected_month,
    selected_campaign=selected_campaign,
    start_from_first=start_from_first,
    days_from_start=days_from_start,
    filtered_df=filtered_df,
    cumulative_df=cumulative_df,
    prev_df=prev_df,
    place_summary=place_summary[place_cols],
    detail_summary=detail_summary[detail_cols].head(12),
    analysis_sections=analysis_sections,
    selected_summary_metrics=selected_summary_metrics,
    show_place=show_place_table,
    show_awareness=show_awareness,
    show_action=show_action,
    show_detail=show_detail_table,
)

st.divider()
st.subheader("PowerPoint出力")

# 条件変更後に、以前作成したPowerPointを誤って表示しないための識別情報
current_ppt_signature = (
    selected_month,
    selected_campaign,
    tuple(selected_summary_metrics),
    tuple(analysis_metrics),
    show_cumulative_analysis,
    show_awareness,
    show_action,
    show_place_table,
    show_detail_table,
)

if (
    st.session_state.get("ppt_signature") is not None
    and st.session_state["ppt_signature"] != current_ppt_signature
):
    st.session_state.pop("ppt_data", None)
    st.session_state.pop("ppt_file_name", None)
    st.session_state.pop("ppt_signature", None)


if st.button("PowerPoint作成", type="primary"):

    with st.spinner("グラフ画像とPowerPointを作成しています..."):

        # この実行ですでに作成したFigureをPNG化
        generate_ppt_images(ppt_chart_figures)

        # PNGを貼り付けてPowerPointを作成
        ppt_path = create_meta_report_ppt(report)

        # ダウンロード用データを保持
        st.session_state["ppt_data"] = Path(ppt_path).read_bytes()
        st.session_state["ppt_file_name"] = ppt_path.name
        st.session_state["ppt_signature"] = current_ppt_signature

    st.success("PowerPointを作成しました。")


if st.session_state.get("ppt_data") is not None:
    st.download_button(
        label="PowerPointをダウンロード",
        data=st.session_state["ppt_data"],
        file_name=st.session_state["ppt_file_name"],
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "presentationml.presentation"
        ),
    )