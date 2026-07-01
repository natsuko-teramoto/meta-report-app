import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from dateutil.relativedelta import relativedelta

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

show_lp = st.sidebar.checkbox(
    "LPビューを表示",
    value=True
)

show_detail_table = st.sidebar.checkbox(
    "掲載開始からの詳細を表示",
    value=True
)

show_cumulative_awareness = st.sidebar.checkbox(
    "累計認知推移を表示",
    value=True
)

show_cumulative_action = st.sidebar.checkbox(
    "累計行動推移を表示",
    value=True
)

show_awareness = st.sidebar.checkbox(
    "認知推移を表示",
    value=True
)

show_action = st.sidebar.checkbox(
    "行動推移を表示",
    value=True
)

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

filtered_df = monthly_df[
    monthly_df["キャンペーン名"] == selected_campaign
].copy()

daily_filtered_df = daily_df[
    daily_df["キャンペーン名"] == selected_campaign
].copy()

end_date = monthly_df["レポート終了日"].max().date()

cumulative_df = monthly_all_df[
    (monthly_all_df["キャンペーン名"] == selected_campaign)
    & (monthly_all_df["レポート終了日"].dt.date <= end_date)
].copy()

adset_daily_all_df = daily_all_df[
    daily_all_df["キャンペーン名"] == selected_campaign
].copy()

start_from_first = adset_daily_all_df["レポート開始日"].min().date()

days_from_start = (end_date - start_from_first).days + 1

start_date = cumulative_df["レポート開始日"].min().date()

prev_df = pd.DataFrame()

def total(df, col):
    if col not in df.columns:
        return 0
    return df[col].fillna(0).sum()

def diff_rate(current, prev):
    if prev == 0:
        return None
    return ((current - prev) / prev) * 100

# 掲載開始日・累計掲載日数
adset_daily_all_df = daily_all_df[
    daily_all_df["キャンペーン名"] == selected_campaign
].copy()

start_from_first = adset_daily_all_df["レポート開始日"].min().date()

days_from_start = (end_date - start_from_first).days + 1
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
    f"数値実績（{selected_month}）"
)

metrics = [
    ("インプレッション", "インプレッション"),
    ("リーチ", "リーチ"),
    ("リンククリック（すべて）", "クリック(すべて)"),
    ("リンククリック", "リンククリック"),
]

if show_lp:
    metrics.append(
        ("LPビュー", "ランディングページビュー")
    )

cols = st.columns(len(metrics))

reach_total = total(filtered_df, "リーチ")

for col_box, (label, col_name) in zip(cols, metrics):
    current_val = total(filtered_df, col_name)
    prev_val = total(prev_df, col_name)
    rate = diff_rate(current_val, prev_val)

    delta_text = "-" if rate is None else f"前月比 {rate:.1f}%"

    display_value = f"{current_val:,.0f}"

    if col_name == "インプレッション":
        if reach_total > 0:
            frequency = current_val / reach_total

            display_value = (
                f"{current_val:,.0f}"
                f" ({frequency:.2f})"
            )

    if col_name in [
        "クリック(すべて)",
        "リンククリック",
        "ランディングページビュー"
    ]:
        if reach_total > 0:
            reach_rate = current_val / reach_total * 100
            display_value = (
                f"{current_val:,.0f}"
                f" ({reach_rate:.2f}%)"
            )

    col_box.metric(
        label=label,
        value=display_value,
        delta=delta_text
    )
    reach_rate = None

    if col_name in [
        "クリック(すべて)",
        "リンククリック",
        "ランディングページビュー"
    ]:
        if reach_total > 0:
            reach_rate = current_val / reach_total * 100


# =========================
# 掲載開始からの累計
# =========================


st.subheader("掲載開始からの累計")

cum_cols = st.columns(5)

cum_reach_total = total(cumulative_df, "リーチ")

cum_cols = st.columns(len(metrics))

for col_box, (label, col_name) in zip(cum_cols, metrics):

    cum_val = total(cumulative_df, col_name)

    display_value = f"{cum_val:,.0f}"

    if col_name == "インプレッション":
        if cum_reach_total > 0:
            frequency = cum_val / cum_reach_total
            display_value = f"{cum_val:,.0f} ({frequency:.2f})"

    elif col_name in [
        "クリック(すべて)",
        "リンククリック",
        "ランディングページビュー"
    ]:
        if cum_reach_total > 0:
            reach_rate = cum_val / cum_reach_total * 100
            display_value = f"{cum_val:,.0f} ({reach_rate:.2f}%)"

    col_box.metric(
        label=label,
        value=display_value
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
        fig_cum_awareness = px.line(
            cumulative_trend,
            x="レポート開始日",
            y=[
                "累計インプレッション",
                "累計リーチ"
            ],
            markers=True,
            title="累計推移：インプレッション・リーチ"
        )

        fig_cum_awareness.update_traces(line=dict(width=3))

        fig_cum_awareness.data[0].line.color = "#4F81BD"
        fig_cum_awareness.data[1].line.color = "#1F497D"

        st.plotly_chart(fig_cum_awareness, width="stretch")

    if show_cumulative_action:
        # 行動累計
        cum_action_y = [
            "累計クリック(すべて)",
            "累計リンククリック",
        ]

        if show_lp:
            cum_action_y.append("累計LPビュー")

        fig_cum_action = px.line(
            cumulative_trend,
            x="レポート開始日",
            y=cum_action_y,
            markers=True,
            title="累計推移：クリック・LPビュー"
        )

        fig_cum_action.update_traces(line=dict(width=3))

        fig_cum_action.data[0].line.color = "#808080"
        fig_cum_action.data[1].line.color = "#F79646"

        if show_lp and len(fig_cum_action.data) >= 3:
            fig_cum_action.data[2].line.color = "#00B050"

        st.plotly_chart(fig_cum_action, width="stretch")

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

detail_cols = [
    "期間",
    "インプレッション",
    "リーチ",
    "リンククリック（すべて）",
    "リンククリック",
]

if show_lp:
    detail_cols.append("LPビュー")

if show_detail_table:
    st.subheader("掲載開始からの詳細")

    st.dataframe(
        detail_summary[detail_cols],
        width="stretch",
        hide_index=True
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

if daily_summary.empty:
    st.info("このキャンペーンは対象月のデイリー推移データがありません。")
else:

    if show_awareness:
        # ==================
        # 認知
        # ==================

        fig1 = px.line(
            daily_summary,
            x="レポート開始日",
            y=["インプレッション", "リーチ"],
            markers=True,
            title="認知推移"
        )

        fig1.update_traces(line=dict(width=3))

        fig1.data[0].line.color = "#4F81BD"
        fig1.data[1].line.color = "#1F497D"

        st.plotly_chart(fig1, width="stretch")

    if show_action:
        # ==================
        # 行動
        # ==================

        action_y = [
            "クリック(すべて)",
            "リンククリック"
        ]

        if show_lp:
            action_y.append("ランディングページビュー")

        fig2 = px.line(
            daily_summary,
            x="レポート開始日",
            y=action_y,
            markers=True,
            title="行動推移"
        )

        fig2.update_traces(line=dict(width=3))

        fig2.data[0].line.color = "#808080"
        fig2.data[1].line.color = "#F79646"

        if show_lp and len(fig2.data) >= 3:
            fig2.data[2].line.color = "#00B050"

        st.plotly_chart(fig2, width="stretch")

st.subheader("男女・年齢分析")

# =========================
# 共通設定
# =========================

gender_label_map = {
    "male": "男性",
    "female": "女性",
    "unknown": "不明",
}

age_order = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]

awareness_metrics = [
    ("インプレッション", "インプレッション"),
    ("リーチ", "リーチ"),
]

action_metrics = [
    ("クリック（すべて）", "クリック(すべて)"),
    ("リンククリック", "リンククリック"),
]

if show_lp:
    action_metrics.append(
        ("LPビュー", "ランディングページビュー")
    )


# =========================
# 男女別分析：円グラフ
# =========================

def show_gender_pies(title, metrics, col_count):
    st.markdown(f"#### {title}")

    cols = st.columns(col_count)

    for chart_col, (display_name, metric) in zip(cols, metrics):
        if metric not in daily_filtered_df.columns:
            with chart_col:
                st.warning(f"{metric} 列がありません")
            continue

        gender_df = (
            daily_filtered_df
            .groupby("性別", as_index=False)[metric]
            .sum()
        )

        gender_df["性別"] = gender_df["性別"].replace(gender_label_map)

        with chart_col:
            fig = px.pie(
                gender_df,
                names="性別",
                values=metric,
                title=f"{display_name} 男女比",
                hole=0
            )

            fig.update_traces(
                textposition="inside",
                textinfo="percent+label"
            )

            st.plotly_chart(fig, width="stretch")


st.subheader("男女別分析")

show_gender_pies(
    title="認知指標",
    metrics=awareness_metrics,
    col_count=2
)

show_gender_pies(
    title="行動指標",
    metrics=action_metrics,
    col_count=len(action_metrics)
)


# =========================
# 年齢別分析：積み上げ棒グラフ
# =========================

def show_age_gender_bars(title, metrics, col_count):
    st.markdown(f"#### {title}")

    cols = st.columns(col_count)

    for chart_col, (display_name, metric) in zip(cols, metrics):
        if metric not in daily_filtered_df.columns:
            with chart_col:
                st.warning(f"{metric} 列がありません")
            continue

        age_gender_df = (
            daily_filtered_df
            .groupby(["年齢", "性別"], as_index=False)[metric]
            .sum()
        )

        total_value = age_gender_df[metric].sum()

        if total_value > 0:
            age_gender_df["割合"] = age_gender_df[metric] / total_value * 100
        else:
            age_gender_df["割合"] = 0

        age_gender_df["性別"] = age_gender_df["性別"].replace(
            {
                "male": "男性",
                "female": "女性",
                "unknown": "不明",
            }
        )

        age_gender_df["年齢"] = pd.Categorical(
            age_gender_df["年齢"],
            categories=age_order,
            ordered=True
        )

        age_gender_df = age_gender_df.sort_values(["年齢", "性別"])

        age_gender_df["表示"] = age_gender_df.apply(
            lambda row: f'{row[metric]:,.0f}<br>{row["割合"]:.1f}%',
            axis=1
        )

        with chart_col:
            fig = px.bar(
                age_gender_df,
                x="年齢",
                y=metric,
                color="性別",
                title=f"{display_name} 年齢別",
                barmode="stack",
                text="表示",
                category_orders={
                    "年齢": age_order,
                    "性別": ["女性", "男性", "不明"],
                },
            )

            fig.update_layout(
                yaxis_title=display_name,
                xaxis_title="",
                legend_title_text="性別",
            )

            fig.update_traces(
                textposition="inside"
            )

            st.plotly_chart(fig, width="stretch")


st.subheader("年齢別分析")

show_age_gender_bars(
    title="認知指標",
    metrics=awareness_metrics,
    col_count=2
)

show_age_gender_bars(
    title="行動指標",
    metrics=action_metrics,
    col_count=len(action_metrics)
)

st.subheader("表示場所分析")

place_filtered = monthly_place_df[
    monthly_place_df["キャンペーン名"] == selected_campaign
].copy()

place_summary = (
    place_filtered
    .groupby(
        ["配置", "キャンペーンの配信", "アトリビューション設定"],
        as_index=False
    )
    .agg({
        "インプレッション": "sum",
        "リーチ": "sum",
        "クリック(すべて)": "sum",
        "リンククリック": "sum",
        "ランディングページビュー": "sum"
    })
)

place_summary = place_summary.rename(
    columns={
        "キャンペーンの配信": "配信",
        "ランディングページビュー": "LPビュー",
        "クリック(すべて)": "クリック(すべて)"
    }
)
# =========================
# リーチ比追加
# =========================

place_summary["クリック(すべて)"] = place_summary.apply(
    lambda row: (
        f'{row["クリック(すべて)"]:,.0f} ({row["クリック(すべて)"] / row["リーチ"] * 100:.2f}%)'
        if row["リーチ"] > 0 else f'{row["クリック(すべて)"]:,.0f}'
    ),
    axis=1
)

place_summary["リンククリック"] = place_summary.apply(
    lambda row: (
        f'{row["リンククリック"]:,.0f} ({row["リンククリック"] / row["リーチ"] * 100:.2f}%)'
        if row["リーチ"] > 0 else f'{row["リンククリック"]:,.0f}'
    ),
    axis=1
)

place_summary["LPビュー"] = place_summary.apply(
    lambda row: (
        f'{row["LPビュー"]:,.0f} ({row["LPビュー"] / row["リーチ"] * 100:.2f}%)'
        if row["リーチ"] > 0 else f'{row["LPビュー"]:,.0f}'
    ),
    axis=1
)

# インプレッションにフリークエンシーを追加
place_summary["インプレッション"] = place_summary.apply(
    lambda row: (
        f'{row["インプレッション"]:,.0f} ({row["インプレッション"] / row["リーチ"]:.2f})'
        if row["リーチ"] > 0 else f'{row["インプレッション"]:,.0f}'
    ),
    axis=1
)

# リーチは通常表示
place_summary["リーチ"] = place_summary["リーチ"].map(
    lambda x: f"{x:,.0f}"
)

place_cols = [
    "配置",
    "配信",
    "アトリビューション設定",
    "インプレッション",
    "リーチ",
    "クリック(すべて)",
    "リンククリック",
]

if show_lp:
    place_cols.append("LPビュー")

st.dataframe(
    place_summary[place_cols],
    width="stretch",
    hide_index=True
)