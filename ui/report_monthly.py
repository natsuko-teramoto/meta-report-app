import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ui.report_config import is_section_visible, is_metric_visible

MONTHLY_METRIC_CONFIG = {
    "impressions": {
        "label": "インプレッション",
        "group": "awareness",
        "color": "#FF6B00",
    },
    "reach": {
        "label": "リーチ",
        "group": "awareness",
        "color": "#7B2CFF",
    },
    "clicks": {
        "label": "クリック（すべて）",
        "group": "action",
        "color": "#FF2D8D",
    },
    "link_clicks": {
        "label": "リンククリック",
        "group": "action",
        "color": "#009BFC",
    },
    "landing_page_views": {
        "label": "LPビュー",
        "group": "action",
        "color": "#00B894",
    },
}


def _build_monthly_dataframe(
    period_result,
):
    rows = period_result.get(
        "cumulative_monthly",
        [],
    )

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    df["date_start"] = pd.to_datetime(
        df["date_start"],
        errors="coerce",
    )

    df = df.dropna(
        subset=["date_start"]
    )

    numeric_columns = [
        "impressions",
        "reach",
        "frequency",
        "clicks",
        "link_clicks",
        "landing_page_views",
    ]

    for column in numeric_columns:
        if column not in df.columns:
            df[column] = 0

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        ).fillna(0)

    df = df.sort_values(
        "date_start"
    ).reset_index(
        drop=True
    )

    # 表示は最大12か月
    if len(df) > 12:
        df = df.tail(
            12
        ).reset_index(
            drop=True
        )

    df["month_label"] = (
        df["date_start"]
        .dt.strftime("%Y/%m")
    )

    return df


def _add_monthly_trace(
    fig,
    df,
    metric_key,
    row,
):
    config = MONTHLY_METRIC_CONFIG[
        metric_key
    ]

    fig.add_trace(
        go.Scatter(
            x=df["month_label"],
            y=df[metric_key],
            mode="lines+markers",
            name=config["label"],
            line={
                "color": config["color"],
                "width": 3,
            },
            marker={
                "color": config["color"],
                "size": 7,
            },
        ),
        row=row,
        col=1,
    )


def _render_monthly_trend_chart(
    df,
    visible_metrics,
    report_key="report",
):
    awareness_metrics = [
        metric_key
        for metric_key in visible_metrics
        if MONTHLY_METRIC_CONFIG[
            metric_key
        ]["group"] == "awareness"
    ]

    action_metrics = [
        metric_key
        for metric_key in visible_metrics
        if MONTHLY_METRIC_CONFIG[
            metric_key
        ]["group"] == "action"
    ]

    has_awareness = bool(
        awareness_metrics
    )
    has_action = bool(
        action_metrics
    )

    if has_awareness and has_action:
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.10,
            row_heights=[
                0.58,
                0.42,
            ],
        )

        for metric_key in awareness_metrics:
            _add_monthly_trace(
                fig=fig,
                df=df,
                metric_key=metric_key,
                row=1,
            )

        for metric_key in action_metrics:
            _add_monthly_trace(
                fig=fig,
                df=df,
                metric_key=metric_key,
                row=2,
            )

        fig.update_yaxes(
            title_text="認知指標",
            rangemode="tozero",
            fixedrange=True,
            row=1,
            col=1,
        )

        fig.update_yaxes(
            title_text="行動指標",
            rangemode="tozero",
            fixedrange=True,
            row=2,
            col=1,
        )

        fig.add_hline(
            y=0,
            line_dash="dot",
            line_color="#D9D9D9",
            row=2,
            col=1,
        )

    else:
        fig = make_subplots(
            rows=1,
            cols=1,
        )

        metrics = (
            awareness_metrics
            if has_awareness
            else action_metrics
        )

        for metric_key in metrics:
            _add_monthly_trace(
                fig=fig,
                df=df,
                metric_key=metric_key,
                row=1,
            )

        axis_title = (
            "認知指標"
            if has_awareness
            else "行動指標"
        )

        fig.update_yaxes(
            title_text=axis_title,
            rangemode="tozero",
            fixedrange=True,
            row=1,
            col=1,
        )

    fig.update_layout(
        height=560,
        margin=dict(
            l=20,
            r=20,
            t=30,
            b=20,
        ),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
        ),
        paper_bgcolor="white",
        plot_bgcolor="white",
    )

    fig.update_xaxes(
        type="category",
        fixedrange=True,
    )

    fig.update_yaxes(
        fixedrange=True,
        gridcolor="#EAEAEA",
    )

    st.plotly_chart(
        fig,
        width="stretch",
        key=f"{report_key}_monthly_trend_chart",
        config={
            "displayModeBar": False,
            "scrollZoom": False,
        },
    )


def _format_monthly_count(
    value,
):
    return f"{int(value):,}"


def _format_monthly_frequency(
    impressions,
    frequency,
):
    return (
        f"{int(impressions):,}"
        f"（{float(frequency):.2f}）"
    )


def _format_monthly_rate(
    value,
    reach,
):
    value = int(value)
    reach = int(reach)

    if reach <= 0:
        return f"{value:,}（―）"

    rate = (
        value
        / reach
        * 100
    )

    return (
        f"{value:,}"
        f"（{rate:.2f}%）"
    )


def _render_monthly_trend_table(
    df,
    visible_metrics,
):
    table_rows = []

    for metric_key in visible_metrics:
        config = MONTHLY_METRIC_CONFIG[
            metric_key
        ]

        row = {
            "指標": config["label"],
        }

        for _, data_row in df.iterrows():
            month_label = data_row[
                "month_label"
            ]

            if metric_key == "impressions":
                value = (
                    _format_monthly_frequency(
                        impressions=data_row[
                            "impressions"
                        ],
                        frequency=data_row[
                            "frequency"
                        ],
                    )
                )

            elif metric_key in {
                "clicks",
                "link_clicks",
                "landing_page_views",
            }:
                value = (
                    _format_monthly_rate(
                        value=data_row[
                            metric_key
                        ],
                        reach=data_row[
                            "reach"
                        ],
                    )
                )

            else:
                value = (
                    _format_monthly_count(
                        data_row[
                            metric_key
                        ]
                    )
                )

            row[
                month_label
            ] = value

        table_rows.append(row)

    table_df = pd.DataFrame(
        table_rows
    )

    st.dataframe(
        table_df,
        hide_index=True,
        width="stretch",
    )


def _render_monthly_trend_section(
    period_result,
    report_key="report",
):
    if not is_section_visible(
        "monthly_trend"
    ):
        return

    df = _build_monthly_dataframe(
        period_result
    )

    if df.empty:
        return

    visible_metrics = [
        metric_key
        for metric_key
        in MONTHLY_METRIC_CONFIG
        if is_metric_visible(
            metric_key
        )
    ]

    if not visible_metrics:
        return

    st.subheader(
        "配信からの月次推移"
    )

    st.caption(
        "配信開始からの各指標を月単位で表示しています。"
        "表示期間は最大12か月です。"
    )

    _render_monthly_trend_chart(
        df=df,
        visible_metrics=visible_metrics,
        report_key=report_key,
    )

    _render_monthly_trend_table(
        df=df,
        visible_metrics=visible_metrics,
    )

    st.divider()
