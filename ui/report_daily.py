import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ui.report_config import is_section_visible, is_metric_visible
from ui.report_common import build_report_period_label

DAILY_METRIC_CONFIG = {
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


def _build_daily_dataframe(
    daily_rows,
):
    if not daily_rows:
        return pd.DataFrame()

    df = pd.DataFrame(
        daily_rows
    )

    if df.empty:
        return df

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce",
    )

    df = df.dropna(
        subset=["date"]
    )

    metric_columns = [
        "impressions",
        "reach",
        "clicks",
        "link_clicks",
        "landing_page_views",
    ]

    for column in metric_columns:
        if column not in df.columns:
            df[column] = 0

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        ).fillna(0)

    return (
        df
        .sort_values("date")
        .reset_index(drop=True)
    )


def _add_daily_trace(
    fig,
    df,
    metric_key,
    row_number,
):
    config = DAILY_METRIC_CONFIG[
        metric_key
    ]

    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df[metric_key],
            mode="lines+markers",
            name=config["label"],
            line=dict(
                color=config["color"],
                width=3,
            ),
            marker=dict(
                color=config["color"],
                size=7,
            ),
            hovertemplate=(
                "%{x|%Y/%m/%d}"
                "<br>"
                f"{config['label']}: "
                "%{y:,.0f}"
                "<extra></extra>"
            ),
        ),
        row=row_number,
        col=1,
    )


def _render_daily_trend_section(
    period_result,
    report_period,
    report_key="report",
):
    if not is_section_visible(
        "daily_trend"
    ):
        return

    daily_rows = (
        period_result.get(
            "target_daily",
            [],
        )
        if period_result
        else []
    )

    df = _build_daily_dataframe(
        daily_rows
    )

    if df.empty:
        return

    awareness_metrics = [
        metric_key
        for metric_key in [
            "impressions",
            "reach",
        ]
        if is_metric_visible(
            metric_key
        )
    ]

    action_metrics = [
        metric_key
        for metric_key in [
            "clicks",
            "link_clicks",
            "landing_page_views",
        ]
        if is_metric_visible(
            metric_key
        )
    ]

    # 5項目すべてOFFなら、
    # デイリー推移セクション自体を表示しない
    if (
        not awareness_metrics
        and not action_metrics
    ):
        return

    period_label = (
        build_report_period_label(
            report_period
        )
    )

    st.subheader(
        f"デイリー推移：{period_label}"
    )

    has_awareness = bool(
        awareness_metrics
    )
    has_action = bool(
        action_metrics
    )

    # ------------------------------
    # 認知＋行動
    # 上下2段を1つのFigureで表示
    # ------------------------------
    if (
        has_awareness
        and has_action
    ):
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
            _add_daily_trace(
                fig,
                df,
                metric_key,
                row_number=1,
            )

        for metric_key in action_metrics:
            _add_daily_trace(
                fig,
                df,
                metric_key,
                row_number=2,
            )

        fig.update_yaxes(
            title_text="認知指標",
            row=1,
            col=1,
            rangemode="tozero",
            gridcolor="rgba(180,180,180,0.20)",
        )

        fig.update_yaxes(
            title_text="行動指標",
            row=2,
            col=1,
            rangemode="tozero",
            gridcolor="rgba(180,180,180,0.20)",
        )

        # 認知と行動の境界
        fig.add_shape(
            type="line",
            xref="paper",
            yref="paper",
            x0=0,
            x1=1,
            y0=0.46,
            y1=0.46,
            line=dict(
                color="rgba(120,120,120,0.50)",
                width=2,
                dash="dot",
            ),
        )

    # ------------------------------
    # 認知だけ
    # 全面表示
    # ------------------------------
    elif has_awareness:
        fig = make_subplots(
            rows=1,
            cols=1,
        )

        for metric_key in awareness_metrics:
            _add_daily_trace(
                fig,
                df,
                metric_key,
                row_number=1,
            )

        fig.update_yaxes(
            title_text="認知指標",
            row=1,
            col=1,
            rangemode="tozero",
            gridcolor="rgba(180,180,180,0.20)",
        )

    # ------------------------------
    # 行動だけ
    # 全面表示
    # ------------------------------
    else:
        fig = make_subplots(
            rows=1,
            cols=1,
        )

        for metric_key in action_metrics:
            _add_daily_trace(
                fig,
                df,
                metric_key,
                row_number=1,
            )

        fig.update_yaxes(
            title_text="行動指標",
            row=1,
            col=1,
            rangemode="tozero",
            gridcolor="rgba(180,180,180,0.20)",
        )

    fig.update_xaxes(
        tickformat="%m/%d",
        showgrid=False,
    )

    fig.update_layout(
        height=560,
        margin=dict(
            l=30,
            r=30,
            t=20,
            b=30,
        ),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )

    fig.update_xaxes(
        fixedrange=True,
    )

    fig.update_yaxes(
        fixedrange=True,
    )

    st.plotly_chart(
        fig,
        width="stretch",
        key=f"{report_key}_daily_trend_chart",
        config={
            "displayModeBar": False,
            "scrollZoom": False,
        },
    )

    st.divider()
