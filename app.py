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

DAILY_DIR = Path("data/daily")
PLACE_DIR = Path("data/place")

def read_excel_folder(folder):
    files = list(folder.glob("*.xlsx"))

    dfs = []
    for file in files:
        df = pd.read_excel(file)
        df["取込ファイル"] = file.name
        dfs.append(df)

    if not dfs:
        return pd.DataFrame()

    return pd.concat(dfs, ignore_index=True)

daily_df = read_excel_folder(DAILY_DIR)
place_df = read_excel_folder(PLACE_DIR)

st.sidebar.header("条件選択")

adsets = sorted(daily_df["広告セット名"].dropna().unique())

selected_adset = st.sidebar.selectbox(
    "医院・広告セットを選択",
    adsets
)

daily_df["レポート開始日"] = pd.to_datetime(daily_df["レポート開始日"])

min_date = daily_df["レポート開始日"].min().date()
max_date = daily_df["レポート開始日"].max().date()

start_date = st.sidebar.date_input("開始日", min_date)
end_date = st.sidebar.date_input("終了日", max_date)

filtered_df = daily_df[
    (daily_df["広告セット名"] == selected_adset)
    & (daily_df["レポート開始日"].dt.date >= start_date)
    & (daily_df["レポート開始日"].dt.date <= end_date)
].copy()

prev_start_date = start_date - relativedelta(months=1)
prev_end_date = end_date - relativedelta(months=1)

prev_df = daily_df[
    (daily_df["広告セット名"] == selected_adset)
    & (daily_df["レポート開始日"].dt.date >= prev_start_date)
    & (daily_df["レポート開始日"].dt.date <= prev_end_date)
].copy()

def total(df, col):
    if col not in df.columns:
        return 0
    return df[col].fillna(0).sum()

def diff_rate(current, prev):
    if prev == 0:
        return None
    return ((current - prev) / prev) * 100

# 抽出条件の表示
st.subheader("抽出条件")

col1, col2 = st.columns(2)

with col1:
    st.metric("広告セット", selected_adset)

with col2:
    st.metric("対象期間", f"{start_date} 〜 {end_date}")


st.subheader("前月比較")

metrics = [
    ("インプレッション", "インプレッション"),
    ("リーチ", "リーチ"),
    ("リンククリック（すべて）", "クリック(すべて)"),
    ("リンククリック", "リンククリック"),
    ("LPビュー", "ランディングページビュー"),
]

cols = st.columns(5)
for col_box, (label, col_name) in zip(cols, metrics):
    current_val = total(filtered_df, col_name)
    prev_val = total(prev_df, col_name)
    rate = diff_rate(current_val, prev_val)

    delta_text = "-" if rate is None else f"{rate:.1f}%"

    col_box.metric(
        label=label,
        value=f"{current_val:,.0f}",
        delta=delta_text
    )

st.caption(f"比較対象期間：{prev_start_date} 〜 {prev_end_date}")

st.subheader("日別推移")

daily_summary = filtered_df.groupby(
    "レポート開始日",
    as_index=False
).agg({
    "インプレッション": "sum",
    "リーチ": "sum",
    "クリック(すべて)": "sum",
    "リンククリック": "sum",
    "ランディングページビュー": "sum"
})

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

# ==================
# 行動
# ==================

fig2 = px.line(
    daily_summary,
    x="レポート開始日",
    y=[
        "クリック(すべて)",
        "リンククリック",
        "ランディングページビュー"
    ],
    markers=True,
    title="行動推移"
)

fig2.update_traces(line=dict(width=3))

fig2.data[0].line.color = "#808080"
fig2.data[1].line.color = "#F79646"
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
    ("LPビュー", "ランディングページビュー"),
]


# =========================
# 男女別分析：円グラフ
# =========================

def show_gender_pies(title, metrics, col_count):
    st.markdown(f"#### {title}")

    cols = st.columns(col_count)

    for chart_col, (display_name, metric) in zip(cols, metrics):
        if metric not in filtered_df.columns:
            with chart_col:
                st.warning(f"{metric} 列がありません")
            continue

        gender_df = (
            filtered_df
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
    col_count=3
)


# =========================
# 年齢別分析：積み上げ棒グラフ
# =========================

def show_age_gender_bars(title, metrics, col_count):
    st.markdown(f"#### {title}")

    cols = st.columns(col_count)

    for chart_col, (display_name, metric) in zip(cols, metrics):
        if metric not in filtered_df.columns:
            with chart_col:
                st.warning(f"{metric} 列がありません")
            continue

        age_gender_df = (
            filtered_df
            .groupby(["年齢", "性別"], as_index=False)[metric]
            .sum()
        )

        total_value = age_gender_df[metric].sum()

        if total_value > 0:
            age_gender_df["割合"] = age_gender_df[metric] / total_value * 100
        else:
            age_gender_df["割合"] = 0

        age_gender_pivot = age_gender_df.pivot_table(
            index="年齢",
            columns="性別",
            values="割合",
            aggfunc="sum",
            fill_value=0
        ).reset_index()

        for gender in ["male", "female"]:
            if gender not in age_gender_pivot.columns:
                age_gender_pivot[gender] = 0

        age_gender_pivot["年齢"] = pd.Categorical(
            age_gender_pivot["年齢"],
            categories=age_order,
            ordered=True
        )

        age_gender_pivot = age_gender_pivot.sort_values("年齢")

        age_gender_pivot = age_gender_pivot.rename(
            columns={
                "male": "男性",
                "female": "女性"
            }
        )

        with chart_col:
            fig = px.bar(
                age_gender_pivot,
                x="年齢",
                y=["女性", "男性"],
                title=f"{display_name} 年齢別比率",
                barmode="stack",
                text_auto=".1f"
            )

            fig.update_layout(
                yaxis_title="割合",
                xaxis_title="",
                legend_title_text="性別",
                yaxis_ticksuffix="%"
            )

            fig.update_traces(
                texttemplate="%{y:.1f}%",
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
    col_count=3
)

st.subheader("表示場所分析")
place_df["レポート開始日"] = pd.to_datetime(place_df["レポート開始日"])

place_filtered = place_df[
    (place_df["キャンペーン名"] == selected_adset)
    & (place_df["レポート開始日"].dt.date >= start_date)
    & (place_df["レポート開始日"].dt.date <= end_date)
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

st.dataframe(
    place_summary[
        [
            "配置",
            "配信",
            "アトリビューション設定",
            "インプレッション",
            "リーチ",
            "クリック(すべて)",
            "リンククリック",
            "LPビュー"
        ]
    ],
    width="stretch",
    hide_index=True
)