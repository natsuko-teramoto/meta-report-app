import streamlit as st
from ui.report_sidebar import render_report_sidebar
from ui.report_basic_info import _render_basic_info_section
from ui.report_metrics import _render_period_result_section, _render_cumulative_result_section
from ui.report_age_gender import _render_period_age_gender_section, _render_cumulative_age_gender_section
from ui.report_placement import _render_placement_section
from ui.report_daily import _render_daily_trend_section
from ui.report_monthly import _render_monthly_trend_section
from ui.report_cumulative import _render_reach_impression_gap_section

def _render_single_report(ad_row, report_period, period_result, report_key="report"):
    if ad_row is None: return
    _render_basic_info_section(ad_row, report_period)
    _render_period_result_section(period_result, report_period)
    _render_cumulative_result_section(period_result)
    _render_period_age_gender_section(period_result, report_period, report_key=report_key)
    _render_placement_section(period_result, report_period, report_key=report_key)
    _render_daily_trend_section(period_result, report_period, report_key=report_key)
    _render_cumulative_age_gender_section(period_result, report_key=report_key)
    _render_reach_impression_gap_section(period_result, report_key=report_key)
    _render_monthly_trend_section(period_result, report_key=report_key)

def render_report_view(report_1_ad, report_2_ad, report_1_period, report_2_period, report_1_period_result, report_2_period_result):
    render_report_sidebar()
    st.title("Meta広告レポート")
    if st.button("← 広告検索に戻る", key="back_to_ad_search"):
        st.session_state.api_view_mode="search"; st.rerun()
    st.divider()
    if report_1_ad is not None and report_2_ad is not None:
        c1,c2=st.columns(2,gap="large")
        with c1: _render_single_report(report_1_ad,report_1_period,report_1_period_result,report_key="report_1")
        with c2: _render_single_report(report_2_ad,report_2_period,report_2_period_result,report_key="report_2")
        return
    ad=report_1_ad if report_1_ad is not None else report_2_ad
    period=report_1_period if report_1_ad is not None else report_2_period
    result=report_1_period_result if report_1_ad is not None else report_2_period_result
    if ad is None:
        st.warning("レポート対象の広告が選択されていません。"); return
    _render_single_report(ad,period,result,report_key="report_1")
