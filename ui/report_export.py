import streamlit as st

from ppt.create_api_ppt import create_api_meta_report_ppt
from ui.report_config import (
    get_report_view_signature,
    get_report_view_snapshot,
)


def _render_one_export(
    report_number,
    ad_row,
    report_period,
    period_result,
):
    if (
        ad_row is None
        or report_period is None
        or period_result is None
    ):
        return

    visibility = get_report_view_snapshot()
    visibility_signature = get_report_view_signature()

    bytes_key = f"api_ppt_bytes_{report_number}"
    name_key = f"api_ppt_name_{report_number}"
    signature_key = f"api_ppt_visibility_{report_number}"

    st.markdown(f"**レポート{report_number}**")

    if st.button(
        "PPTを作成",
        key=f"create_api_ppt_{report_number}",
        use_container_width=True,
    ):
        with st.spinner("PowerPointを作成しています..."):
            path = create_api_meta_report_ppt(
                ad_row=ad_row,
                report_period=report_period,
                period_result=period_result,
                visibility=visibility,
                report_key=f"report_{report_number}",
            )

            st.session_state[bytes_key] = path.read_bytes()
            st.session_state[name_key] = path.name
            st.session_state[signature_key] = visibility_signature

    if (
        st.session_state.get(bytes_key)
        and st.session_state.get(signature_key) == visibility_signature
    ):
        st.download_button(
            "PPTをダウンロード",
            data=st.session_state[bytes_key],
            file_name=st.session_state[name_key],
            mime=(
                "application/"
                "vnd.openxmlformats-officedocument."
                "presentationml.presentation"
            ),
            key=f"download_api_ppt_{report_number}",
            use_container_width=True,
        )


def render_api_ppt_export_controls(
    report_1_ad,
    report_1_period,
    report_1_period_result,
    report_2_ad=None,
    report_2_period=None,
    report_2_period_result=None,
):
    st.divider()
    st.subheader("PowerPoint出力")

    if (
        report_2_ad is not None
        and report_2_period is not None
        and report_2_period_result is not None
    ):
        left, right = st.columns(2)

        with left:
            _render_one_export(
                1,
                report_1_ad,
                report_1_period,
                report_1_period_result,
            )

        with right:
            _render_one_export(
                2,
                report_2_ad,
                report_2_period,
                report_2_period_result,
            )
    else:
        _render_one_export(
            1,
            report_1_ad,
            report_1_period,
            report_1_period_result,
        )
