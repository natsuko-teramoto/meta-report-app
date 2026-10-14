import streamlit as st
import pandas as pd
from ui.report_config import BASIC_INFO_ITEMS
from ui.report_common import build_report_period_label

def _render_basic_info_section(
    ad_row,
    report_period,
):
    """
    配信基本情報と広告設定を表示する。
    表示対象だけで列を組み直し、
    非表示項目の空白は残さない。
    """

    corporation_name = str(
        ad_row.get(
            "案件名",
            "",
        )
        or ""
    ).strip()

    facility_name = str(
        ad_row.get(
            "施設名",
            "",
        )
        or ""
    ).strip()

    if (
        facility_name
        and facility_name != corporation_name
    ):
        customer_name = (
            corporation_name
            + " "
            + facility_name
        ).strip()
    else:
        customer_name = (
            corporation_name
            or facility_name
            or "-"
        )

    # レガシー広告は最初の配信開始日を優先
    start_value = ad_row.get("レポート配信開始日")

    start_date = pd.to_datetime(
        start_value,
        errors="coerce",
    )

    # 通常広告は従来の配信開始日を使用
    if pd.isna(start_date):
        start_date = pd.to_datetime(
            ad_row.get("配信開始"),
            errors="coerce",
        )

    publication_start = (
        start_date.strftime("%Y/%m/%d")
        if pd.notna(start_date)
        else "-"
    )

    appeal = (
        ad_row.get(
            "訴求内容",
            "",
        )
        or "-"
    )

    area = (
        ad_row.get(
            "エリア",
            "",
        )
        or "-"
    )

    age = (
        ad_row.get(
            "年齢",
            "",
        )
        or "-"
    )

    gender = (
        ad_row.get(
            "性別",
            "",
        )
        or "-"
    )

    cumulative_days = "-"

    if report_period is not None:

        # レガシー広告は最初の配信開始日から計算
        if pd.notna(start_date):
            cumulative_start = start_date.date()
        else:
            cumulative_start = report_period.cumulative_start

        cumulative_days = max(
            (
                report_period.cumulative_end
                - cumulative_start
            ).days + 1,
            0,
        )

    report_period_label = (
        build_report_period_label(
            report_period
        )
    )

    # ------------------------------
    # 顧客名
    # ------------------------------
    if st.session_state.get(
        "report_basic_customer_name",
        True,
    ):
        st.caption(
            "顧客名"
        )

        st.markdown(
            f"### {customer_name}"
        )

    # ------------------------------
    # 1段目
    # 配信開始日 / 累計配信日数 /
    # レポート集計期間
    # ------------------------------
    first_row_items = []

    if st.session_state.get(
        "report_basic_publication_start",
        True,
    ):
        first_row_items.append(
            (
                "配信開始日",
                publication_start,
            )
        )

    if st.session_state.get(
        "report_basic_cumulative_days",
        True,
    ):
        first_row_items.append(
            (
                "累計配信日数",
                f"{cumulative_days}日",
            )
        )

    if st.session_state.get(
        "report_basic_report_period",
        True,
    ):
        first_row_items.append(
            (
                "レポート集計期間",
                report_period_label,
            )
        )

    if first_row_items:
        first_row_columns = st.columns(
            len(first_row_items)
        )

        for column, (
            label,
            value,
        ) in zip(
            first_row_columns,
            first_row_items,
        ):
            column.caption(
                label
            )

            column.markdown(
                f"""
                <div style="
                    font-size:1.5rem;
                    font-weight:400;
                ">
                    {value}
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ------------------------------
    # 2段目
    # 訴求内容 / 配信エリア /
    # 年齢 / 性別
    # ------------------------------
    second_row_items = []

    if st.session_state.get(
        "report_basic_appeal",
        True,
    ):
        second_row_items.append(
            (
                "訴求内容",
                appeal,
            )
        )

    if st.session_state.get(
        "report_basic_area",
        True,
    ):
        second_row_items.append(
            (
                "配信エリア",
                area,
            )
        )

    if st.session_state.get(
        "report_basic_age",
        True,
    ):
        second_row_items.append(
            (
                "年齢",
                age,
            )
        )

    if st.session_state.get(
        "report_basic_gender",
        True,
    ):
        second_row_items.append(
            (
                "性別",
                gender,
            )
        )

    if second_row_items:
        second_row_columns = st.columns(
            len(second_row_items)
        )

        for column, (
            label,
            value,
        ) in zip(
            second_row_columns,
            second_row_items,
        ):
            column.caption(
                label
            )

            column.markdown(
                f"""
                <div style="
                    font-size:1.5rem;
                    font-weight:400;
                ">
                    {value}
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ------------------------------
    # 基本情報が全部非表示なら
    # 区切り線も表示しない
    # ------------------------------
    basic_info_visible = any(
        st.session_state.get(
            f"report_basic_{item_key}",
            True,
        )
        for item_key, _
        in BASIC_INFO_ITEMS
    )

    if basic_info_visible:
        st.divider()
