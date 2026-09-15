import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from ui.report_config import is_section_visible, is_metric_visible, any_metric_visible
from ui.report_common import build_report_period_label
GENDER_COLORS={"女性":"#009BFC","男性":"#4000B8","不明":"#BDBDBD"}

def _build_age_gender_dataframe(
    age_gender_rows,
    metric_key,
):
    """
    Metaの年齢・性別breakdownを
    グラフ表示用DataFrameに変換する。
    """

    if not age_gender_rows:
        return pd.DataFrame()

    df = pd.DataFrame(age_gender_rows)

    if df.empty:
        return df

    gender_labels = {
        "female": "女性",
        "male": "男性",
        "unknown": "不明",
    }

    df["性別"] = (
        df["gender"]
        .map(gender_labels)
        .fillna(df["gender"])
    )

    df["年齢"] = df["age"]

    df["値"] = pd.to_numeric(
        df[metric_key],
        errors="coerce",
    ).fillna(0)

    total_value = df["値"].sum()

    if total_value > 0:
        df["割合"] = (
            df["値"]
            / total_value
            * 100
        )
    else:
        df["割合"] = 0.0

    return df


def _render_age_gender_bar_chart(
    df,
    chart_key,
):
    if df.empty:
        st.info(
            "年齢・性別データがありません。"
        )
        return

    fig = px.bar(
        df,
        x="年齢",
        y="値",
        color="性別",
        barmode="group",
        text=df.apply(
            lambda row: (
                f"{int(row['値']):,}"
                f"<br>{row['割合']:.1f}%"
            ),
            axis=1,
        ),
        category_orders={
            "性別": [
                "女性",
                "男性",
                "不明",
            ],
        },
        color_discrete_map=GENDER_COLORS,
    )

    fig.update_traces(
        textposition="outside",
        cliponaxis=False,
    )

    fig.update_layout(
        height=420,
        margin=dict(
            l=20,
            r=20,
            t=20,
            b=20,
        ),
        xaxis_title="",
        yaxis_title="",
        legend_title_text="性別",
    )

    st.plotly_chart(
        fig,
        width="stretch",
        key=chart_key,
    )

def _render_gender_pie_chart(
    df,
    chart_key,
):
    if df.empty:
        st.info(
            "性別データがありません。"
        )
        return

    gender_df = (
        df.groupby(
            "性別",
            as_index=False,
        )["値"]
        .sum()
    )

    gender_df = gender_df[
        gender_df["値"] > 0
    ]

    if gender_df.empty:
        st.info(
            "性別データがありません。"
        )
        return

    fig = go.Figure(
        data=[
            go.Pie(
                labels=gender_df["性別"],
                values=gender_df["値"],
                marker=dict(
                    colors=[
                        GENDER_COLORS.get(
                            gender,
                            "#BDBDBD",
                        )
                        for gender
                        in gender_df["性別"]
                    ]
                ),
                texttemplate=(
                    "%{label}"
                    "<br>%{value:,}"
                    "<br>%{percent:.1%}"
                ),
                textposition="inside",
            )
        ]
    )

    fig.update_layout(
        height=420,
        margin=dict(
            l=20,
            r=20,
            t=20,
            b=20,
        ),
        showlegend=True,
    )

    st.plotly_chart(
        fig,
        width="stretch",
        key=chart_key,
    )

def _render_age_gender_metric(
    age_gender_rows,
    metric_key,
    metric_label,
    section_key,
):
    """
    年齢・性別分析の1指標を表示する。
    左：年齢×性別の縦棒グラフ
    右：全体の男女比円グラフ
    """

    st.markdown(
        f"**{metric_label}**"
    )

    df = _build_age_gender_dataframe(
        age_gender_rows,
        metric_key,
    )

    chart_col, pie_col = st.columns(
        [3, 1]
    )

    with chart_col:
        _render_age_gender_bar_chart(
            df,
            chart_key=(
                f"{section_key}_"
                f"{metric_key}_bar"
            ),
        )

    with pie_col:
        _render_gender_pie_chart(
            df,
            chart_key=(
                f"{section_key}_"
                f"{metric_key}_pie"
            ),
        )


def _render_age_gender_analysis(age_gender_rows, section_key, report_key="report"):
    awareness = [("impressions", "インプレッション"), ("reach", "リーチ")]
    action = [("clicks", "クリック"), ("link_clicks", "リンククリック"), ("landing_page_views", "LPビュー")]
    awareness = [(k,l) for k,l in awareness if is_metric_visible(k)]
    action = [(k,l) for k,l in action if is_metric_visible(k)]
    if awareness:
        st.markdown("### 認知指標")
        for k,l in awareness: _render_age_gender_metric(age_gender_rows, k, l, f"{report_key}_{section_key}")
    if action:
        st.markdown("### 行動指標")
        for k,l in action: _render_age_gender_metric(age_gender_rows, k, l, f"{report_key}_{section_key}")

def _render_period_age_gender_section(
    period_result,
    report_period,
    report_key="report",
):
    if not is_section_visible(
        "period_age_gender"
    ):
        return

    if not any_metric_visible():
        return

    age_gender_rows = (
        period_result.get(
            "target_age_gender",
            [],
        )
        if period_result
        else []
    )

    period_label = (
        build_report_period_label(
            report_period
        )
    )

    st.subheader(
        f"設定期間の年齢・性別分析："
        f"{period_label}"
    )

    _render_age_gender_analysis(
        age_gender_rows,
        section_key="period",
        report_key=report_key,
    )

    st.divider()

def _render_cumulative_age_gender_section(
    period_result,
    report_key="report",
):
    if not is_section_visible(
        "cumulative_age_gender"
    ):
        return

    if not any_metric_visible():
        return

    age_gender_rows = (
        period_result.get(
            "cumulative_age_gender",
            [],
        )
        if period_result
        else []
    )

    st.subheader(
        "配信開始からの累計 年齢・性別分析"
    )

    _render_age_gender_analysis(
        age_gender_rows,
        section_key="cumulative",
        report_key=report_key,
    )

    st.divider()
