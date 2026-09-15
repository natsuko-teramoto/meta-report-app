import streamlit as st
from ui.report_config import (REPORT_SECTIONS, BASIC_INFO_ITEMS, REPORT_METRIC_ITEMS, PLACEMENT_ITEMS, initialize_report_view_state)

def _set_all_report_items(value):
    for prefix, items in (("report_basic_", BASIC_INFO_ITEMS), ("report_metric_", REPORT_METRIC_ITEMS),
                          ("report_section_", REPORT_SECTIONS), ("report_placement_", PLACEMENT_ITEMS)):
        for key, _ in items:
            st.session_state[f"{prefix}{key}"] = value

def render_report_sidebar():
    initialize_report_view_state()
    with st.sidebar:
        st.header("表示項目")
        if st.button(
            "すべて表示",
            use_container_width=True,
            key="show_all_report_items",
        ):
            _set_all_report_items(True)
            st.rerun()
        st.divider()
        st.markdown("**基本情報**")
        for key, label in BASIC_INFO_ITEMS: st.checkbox(label, key=f"report_basic_{key}")
        st.divider(); st.markdown("**数値指標**")
        for key, label in REPORT_METRIC_ITEMS: st.checkbox(label, key=f"report_metric_{key}")
        st.divider(); st.markdown("**年齢・性別**")
        st.checkbox("年齢・性別分析グラフ", key="report_section_period_age_gender")
        st.checkbox("累計 年齢・性別分析グラフ", key="report_section_cumulative_age_gender")
        st.divider(); st.markdown("**表示場所**")
        st.checkbox("配置分析グラフ", key="report_placement_chart")
        st.checkbox("詳細", key="report_placement_detail")
        st.divider(); st.markdown("**その他のグラフ**")
        st.checkbox("デイリー推移グラフ", key="report_section_daily_trend")
        st.checkbox("累計 リーチ・インプレッショングラフ", key="report_section_reach_impression_gap")
        st.checkbox("配信からの月次推移グラフ", key="report_section_monthly_trend")

