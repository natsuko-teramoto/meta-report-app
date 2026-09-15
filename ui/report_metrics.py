import streamlit as st
from ui.report_config import is_metric_visible, any_metric_visible
from ui.report_common import build_report_period_label

def _calculate_comparison_delta(
    current_value,
    previous_value,
):
    """
    前期間比を計算する。
    """

    if previous_value == 0:

        if current_value == 0:
            return 0.0

        return None

    return (
        (
            current_value
            - previous_value
        )
        / previous_value
        * 100
    )


def _render_comparison_delta(
    column,
    current_value,
    previous_value,
):
    """
    指標下部に前期間比を色付きで表示する。
    """

    delta = _calculate_comparison_delta(
        current_value,
        previous_value,
    )

    if delta is None:

        column.markdown(
            """
            <div style="
                color:#8a8a8a;
                font-size:0.85rem;
                margin-top:-0.3rem;
            ">
                前期間実績なし
            </div>
            """,
            unsafe_allow_html=True,
        )

        return

    if delta > 0:

        column.markdown(
            f"""
            <div style="
                color:#16a34a;
                font-size:0.85rem;
                font-weight:600;
                margin-top:-0.3rem;
            ">
                ↑ 前期間比 {delta:.1f}%
            </div>
            """,
            unsafe_allow_html=True,
        )

        return

    if delta < 0:

        column.markdown(
            f"""
            <div style="
                color:#dc2626;
                font-size:0.85rem;
                font-weight:600;
                margin-top:-0.3rem;
            ">
                ↓ 前期間比 {abs(delta):.1f}%
            </div>
            """,
            unsafe_allow_html=True,
        )

        return

    column.markdown(
        """
        <div style="
            color:#8a8a8a;
            font-size:0.85rem;
            margin-top:-0.3rem;
        ">
            前期間比 0.0%
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# 5指標共通表示
# =========================================================

def _render_metric_row(
    metric_result,
    comparison_result=None,
):
    """
    表示対象の基本指標だけを横並びで表示する。
    非表示項目の空き列は残さない。
    """

    metric_items = [
        {
            "key": "impressions",
            "label": "インプレッション",
            "value": (
                f"{metric_result['impressions']:,} "
                f"({metric_result['frequency']:.2f})"
            ),
            "raw_value": metric_result[
                "impressions"
            ],
        },
        {
            "key": "reach",
            "label": "リーチ",
            "value": (
                f"{metric_result['reach']:,}"
            ),
            "raw_value": metric_result[
                "reach"
            ],
        },
        {
            "key": "clicks",
            "label": "クリック",
            "value": (
                f"{metric_result['clicks']:,} "
                f"({metric_result['click_rate']:.2f}%)"
            ),
            "raw_value": metric_result[
                "clicks"
            ],
        },
        {
            "key": "link_clicks",
            "label": "リンククリック",
            "value": (
                f"{metric_result['link_clicks']:,} "
                f"({metric_result['link_click_rate']:.2f}%)"
            ),
            "raw_value": metric_result[
                "link_clicks"
            ],
        },
        {
            "key": "landing_page_views",
            "label": "LPビュー",
            "value": (
                f"{metric_result['landing_page_views']:,} "
                f"({metric_result['landing_page_view_rate']:.2f}%)"
            ),
            "raw_value": metric_result[
                "landing_page_views"
            ],
        },
    ]

    # ------------------------------
    # ONの指標だけ残す
    # ------------------------------
    visible_items = [
        item
        for item in metric_items
        if is_metric_visible(
            item["key"]
        )
    ]

    # 全指標OFFなら何も描画しない
    if not visible_items:
        return

    # ------------------------------
    # 表示数に応じて列を作る
    # ------------------------------
    columns = st.columns(
        len(visible_items)
    )

    for column, item in zip(
        columns,
        visible_items,
    ):
        column.metric(
            item["label"],
            item["value"],
        )

        if comparison_result is not None:
            _render_comparison_delta(
                column,
                item["raw_value"],
                comparison_result[
                    item["key"]
                ],
            )

# =========================================================
# 設定期間配信結果
# =========================================================

def _render_period_result_section(
    period_result,
    report_period,
):
    """
    設定期間配信結果を表示する。
    """

    if not any_metric_visible():
        return

    report_period_label = (
        build_report_period_label(
            report_period
        )
    )

    st.subheader(
        f"配信結果：{report_period_label}"
    )

    if period_result is None:

        st.warning(
            "設定期間の配信結果を"
            "取得できません。"
        )

        return

    target = period_result.get(
        "target"
    )

    comparison = period_result.get(
        "comparison"
    )

    if target is None:

        st.warning(
            "設定期間の配信結果を"
            "取得できません。"
        )

        return

    _render_metric_row(
        target,
        comparison_result=comparison,
    )

    st.divider()


# =========================================================
# 累計配信結果
# =========================================================

def _render_cumulative_result_section(
    period_result,
):
    """
    配信開始から対象期間終了日までの
    累計配信結果を表示する。
    """

    if not any_metric_visible():
        return

    st.subheader(
        "配信開始からの累計配信結果"
    )

    if period_result is None:

        st.warning(
            "累計配信結果を"
            "取得できません。"
        )

        return

    cumulative = period_result.get(
        "cumulative"
    )

    if cumulative is None:

        st.warning(
            "累計配信結果を"
            "取得できません。"
        )

        return

    _render_metric_row(
        cumulative
    )

    st.divider()
