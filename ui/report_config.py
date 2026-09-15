import json
import streamlit as st

REPORT_SECTIONS = [
    ("period_age_gender", "年齢・性別分析グラフ"),
    ("cumulative_age_gender", "累計 年齢・性別分析グラフ"),
    ("daily_trend", "デイリー推移グラフ"),
    ("reach_impression_gap", "累計 リーチ・インプレッショングラフ"),
    ("monthly_trend", "配信からの月次推移グラフ"),
]

BASIC_INFO_ITEMS = [
    ("customer_name", "顧客名"),
    ("publication_start", "配信開始日"),
    ("cumulative_days", "累計配信日数"),
    ("report_period", "レポート集計期間"),
    ("appeal", "訴求内容"),
    ("area", "配信エリア"),
    ("age", "年齢"),
    ("gender", "性別"),
]

REPORT_METRIC_ITEMS = [
    ("impressions", "インプレッション"),
    ("reach", "リーチ"),
    ("clicks", "クリック"),
    ("link_clicks", "リンククリック"),
    ("landing_page_views", "LPビュー"),
]

PLACEMENT_ITEMS = [
    ("chart", "配置分析グラフ"),
    ("detail", "詳細"),
]


def initialize_report_view_state():
    for prefix, items in (
        ("report_basic_", BASIC_INFO_ITEMS),
        ("report_metric_", REPORT_METRIC_ITEMS),
        ("report_section_", REPORT_SECTIONS),
        ("report_placement_", PLACEMENT_ITEMS),
    ):
        for key, _ in items:
            st.session_state.setdefault(f"{prefix}{key}", True)


def is_section_visible(section_key):
    return st.session_state.get(f"report_section_{section_key}", True)


def is_metric_visible(metric_key):
    return st.session_state.get(f"report_metric_{metric_key}", True)


def is_basic_visible(item_key):
    return st.session_state.get(f"report_basic_{item_key}", True)


def is_placement_visible(item_key):
    return st.session_state.get(f"report_placement_{item_key}", True)


def any_metric_visible():
    return any(is_metric_visible(key) for key, _ in REPORT_METRIC_ITEMS)


def get_report_view_snapshot():
    initialize_report_view_state()
    return {
        "basic": {
            key: is_basic_visible(key)
            for key, _ in BASIC_INFO_ITEMS
        },
        "metrics": {
            key: is_metric_visible(key)
            for key, _ in REPORT_METRIC_ITEMS
        },
        "sections": {
            key: is_section_visible(key)
            for key, _ in REPORT_SECTIONS
        },
        "placement": {
            key: is_placement_visible(key)
            for key, _ in PLACEMENT_ITEMS
        },
    }


def get_report_view_signature():
    return json.dumps(
        get_report_view_snapshot(),
        ensure_ascii=False,
        sort_keys=True,
    )
