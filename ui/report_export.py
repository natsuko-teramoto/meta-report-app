import streamlit as st

from ppt.create_api_ppt import create_api_meta_report_ppt, get_api_ppt_filename
from ui.report_config import get_report_view_snapshot


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

    st.markdown(f"**レポート{report_number}**")

    def generate_ppt_bytes():
        path = create_api_meta_report_ppt(
            ad_row=ad_row,
            report_period=report_period,
            period_result=period_result,
            visibility=visibility,
            report_key=f"report_{report_number}",
        )
        return path.read_bytes()

    st.download_button(
        "PPTをダウンロード",
        data=generate_ppt_bytes,
        file_name=get_api_ppt_filename(ad_row, report_period),
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        key=f"download_api_ppt_{report_number}",
        on_click="ignore",
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
