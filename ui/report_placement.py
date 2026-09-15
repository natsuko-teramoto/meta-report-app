import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from ui.report_config import is_metric_visible, is_placement_visible, any_metric_visible
from ui.report_common import build_report_period_label

PLACEMENT_COLORS = {
    "Instagramフィード": "#F58529",
    "Instagramストーリーズ": "#DD2A7B",
    "Instagramリール": "#8134AF",
    "Instagram発見ホーム": "#515BD4",
    "Facebookフィード": "#1877F2",
    "Facebookストーリーズ": "#42A5F5",
    "Facebookリール": "#5B7CFA",
    "その他": "#BDBDBD",
}


def _format_placement_name(
    publisher_platform,
    platform_position,
):
    publisher_platform = (
        str(publisher_platform or "")
        .strip()
        .lower()
    )

    platform_position = (
        str(platform_position or "")
        .strip()
        .lower()
    )

    if publisher_platform == "instagram":
        mapping = {
            "feed": "Instagramフィード",
            "story": "Instagramストーリーズ",
            "stories": "Instagramストーリーズ",
            "instagram_stories": "Instagramストーリーズ",
            "reels": "Instagramリール",
            "instagram_reels": "Instagramリール",
            "explore": "Instagram発見",
            "explore_home": "Instagram発見ホーム",
        }

        return mapping.get(
            platform_position,
            (
                f"Instagram "
                f"{platform_position}"
                if platform_position
                else "Instagram"
            ),
        )

    if publisher_platform == "facebook":
        mapping = {
            "feed": "Facebookフィード",
            "story": "Facebookストーリーズ",
            "stories": "Facebookストーリーズ",
            "reels": "Facebookリール",
        }

        return mapping.get(
            platform_position,
            (
                f"Facebook "
                f"{platform_position}"
                if platform_position
                else "Facebook"
            ),
        )

    if publisher_platform:
        return (
            f"{publisher_platform} "
            f"{platform_position}"
        ).strip()

    return "その他"


def _build_placement_dataframe(
    placement_rows,
):
    if not placement_rows:
        return pd.DataFrame()

    df = pd.DataFrame(
        placement_rows
    )

    if df.empty:
        return df

    df["配置"] = df.apply(
        lambda row: _format_placement_name(
            row.get(
                "publisher_platform",
                "",
            ),
            row.get(
                "platform_position",
                "",
            ),
        ),
        axis=1,
    )

    numeric_columns = [
        "impressions",
        "reach",
        "frequency",
        "clicks",
        "click_rate",
        "link_clicks",
        "link_click_rate",
        "landing_page_views",
        "landing_page_view_rate",
    ]

    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            ).fillna(0)

    return df


def _render_placement_bar_chart(
    df,
    metric_key,
    metric_label,
    chart_key,
):
    if df.empty:
        st.info(
            "表示場所データがありません。"
        )
        return

    chart_df = (
        df.groupby(
            "配置",
            as_index=False,
        )[metric_key]
        .sum()
        .sort_values(
            metric_key,
            ascending=True,
        )
    )

    chart_df = chart_df[
        chart_df[metric_key] > 0
    ]

    if chart_df.empty:
        st.info(
            f"{metric_label}のデータがありません。"
        )
        return

    chart_df["色"] = chart_df["配置"].map(
        PLACEMENT_COLORS
    ).fillna(
        PLACEMENT_COLORS["その他"]
    )

    fig = go.Figure()

    for _, row in chart_df.iterrows():
        fig.add_trace(
            go.Bar(
                x=[row[metric_key]],
                y=[row["配置"]],
                orientation="h",
                marker_color=row["色"],
                text=[
                    f"{int(row[metric_key]):,}"
                ],
                textposition="outside",
                showlegend=False,
                hovertemplate=(
                    f"{row['配置']}"
                    "<br>"
                    f"{metric_label}: "
                    "%{x:,}"
                    "<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        height=320,
        margin=dict(
            l=10,
            r=30,
            t=10,
            b=10,
        ),
        xaxis_title="",
        yaxis_title="",
        bargap=0.30,
    )

    fig.update_xaxes(
        showgrid=True,
        zeroline=False,
    )

    fig.update_yaxes(
        categoryorder="total ascending",
    )

    st.markdown(
        f"**{metric_label}**"
    )

    st.plotly_chart(
        fig,
        width="stretch",
        key=chart_key,
    )


def _render_placement_table(
    df,
):
    if df.empty:
        st.info(
            "表示場所データがありません。"
        )
        return

    table_df = df.copy()

    # 表示順を固定
    placement_order = {
        "Instagramフィード": 1,
        "Instagramストーリーズ": 2,
        "Instagramリール": 3,
    }

    table_df["表示順"] = (
        table_df["配置"]
        .map(placement_order)
        .fillna(999)
    )

    table_df = (
        table_df
        .sort_values(
            [
                "表示順",
                "配置",
            ]
        )
        .reset_index(drop=True)
    )

    # Meta APIから取得した frequency をそのまま使用
    table_df["frequency"] = pd.to_numeric(
        table_df["frequency"],
        errors="coerce",
    ).fillna(0)

    # 各率はリーチを分母に計算
    table_df["クリック率"] = table_df.apply(
        lambda row: (
            row["clicks"]
            / row["reach"]
            * 100
            if row["reach"] > 0
            else 0.0
        ),
        axis=1,
    )

    table_df["リンククリック率"] = table_df.apply(
        lambda row: (
            row["link_clicks"]
            / row["reach"]
            * 100
            if row["reach"] > 0
            else 0.0
        ),
        axis=1,
    )

    table_df["LPビュー率"] = table_df.apply(
        lambda row: (
            row["landing_page_views"]
            / row["reach"]
            * 100
            if row["reach"] > 0
            else 0.0
        ),
        axis=1,
    )

    table_df["インプレッション"] = table_df.apply(
        lambda row: (
            f"{int(row['impressions']):,}"
            f" ({row['frequency']:.2f})"
        ),
        axis=1,
    )

    table_df["リーチ"] = (
        table_df["reach"]
        .map(
            lambda value: f"{int(value):,}"
        )
    )

    table_df["クリック（すべて）"] = table_df.apply(
        lambda row: (
            f"{int(row['clicks']):,}"
            f" ({row['クリック率']:.2f}%)"
        ),
        axis=1,
    )

    table_df["リンククリック"] = table_df.apply(
        lambda row: (
            f"{int(row['link_clicks']):,}"
            f" ({row['リンククリック率']:.2f}%)"
        ),
        axis=1,
    )

    table_df["LPビュー"] = table_df.apply(
        lambda row: (
            f"{int(row['landing_page_views']):,}"
            f" ({row['LPビュー率']:.2f}%)"
        ),
        axis=1,
    )

    display_columns = ["配置"]
    metric_columns = [
        ("impressions", "インプレッション"), ("reach", "リーチ"),
        ("clicks", "クリック（すべて）"), ("link_clicks", "リンククリック"),
        ("landing_page_views", "LPビュー"),
    ]
    display_columns += [label for key, label in metric_columns if is_metric_visible(key)]
    if len(display_columns) == 1:
        return
    display_df = table_df[display_columns]

    st.dataframe(
        display_df,
        hide_index=True,
        width="stretch",
    )

def _render_placement_section(period_result, report_period, report_key="report"):
    show_chart = is_placement_visible("chart")
    show_detail = is_placement_visible("detail") and any_metric_visible()
    if not show_chart and not show_detail:
        return
    rows = period_result.get("target_placement", []) if period_result else []
    df = _build_placement_dataframe(rows)
    label = build_report_period_label(report_period)
    st.subheader(f"表示場所分析：{label}")
    if show_chart:
        charts=[("impressions","インプレッション"),("reach","リーチ"),("clicks","クリック（すべて）")]
        cols=st.columns(len(charts))
        for col,(key,title) in zip(cols,charts):
            with col: _render_placement_bar_chart(df,key,title,chart_key=f"{report_key}_placement_{key}")
    if show_detail:
        st.markdown("**詳細**")
        _render_placement_table(df)
    st.divider()
