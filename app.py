import streamlit as st

from services.ad_search import (
    build_ad_search_data,
    find_ad_by_key,
)
from ui.ad_search_view import render_ad_search_view
from ui.report_view import render_report_view
from ui.report_export import render_api_ppt_export_controls
from datetime import datetime
from time import perf_counter

from services.period import build_report_period
from services.report_service import build_period_result
from services.legacy_report_service import build_legacy_period_result
from data_sources.master_source import (
    load_change_requests,
    load_change_request_details,
)
from services.change_request_service import (
    apply_completed_changes_to_ad_data,
)

# =========================================================
# 速度計測
# =========================================================

APP_START_TIME = perf_counter()

st.set_page_config(
    page_title="Meta広告レポート",
    page_icon="📊",
    layout="wide",
)


@st.cache_data(ttl=300)
def load_ad_data():
    return build_ad_search_data()



def parse_publication_start(value):
    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    for date_format in [
        "%Y/%m/%d",
        "%Y-%m-%d",
    ]:
        try:
            return datetime.strptime(
                value,
                date_format,
            ).date()
        except ValueError:
            continue

    return None


def build_confirmed_period(ad_row, period_input):
    if ad_row is None:
        return None

    if period_input is None:
        return None

    publication_start = parse_publication_start(
        ad_row.get("配信開始")
    )

    if publication_start is None:
        raise ValueError(
            "広告の掲載開始日を取得できません。"
        )

    mode = period_input["mode"]

    if mode == "month":
        return build_report_period(
            mode=mode,
            publication_start=publication_start,
            year=period_input["year"],
            month=period_input["month"],
        )

    return build_report_period(
        mode=mode,
        publication_start=publication_start,
        target_start=period_input["target_start"],
        target_end=period_input["target_end"],
    )


def build_report_cache_key(ad_row, report_period):
    if ad_row is None or report_period is None:
        return None

    ad_id = str(ad_row.get("ad_id", ""))

    return (
        ad_id,
        str(report_period.target_start),
        str(report_period.target_end),
        str(report_period.comparison_start),
        str(report_period.comparison_end),
        str(report_period.cumulative_start),
        str(report_period.cumulative_end),
    )


def get_report_period_result(
    report_number,
    ad_row,
    report_period,
):
    if ad_row is None or report_period is None:
        return None

    cache_key = build_report_cache_key(
        ad_row,
        report_period,
    )

    state_key = f"report_{report_number}_period_result"
    cache_key_state = f"report_{report_number}_period_result_cache_key"

    cached_key = st.session_state.get(cache_key_state)
    cached_result = st.session_state.get(state_key)

    if cached_key == cache_key and cached_result is not None:
        return cached_result

    _t0 = perf_counter()
    
    data_type = str(
        ad_row.get("データ種別", "")
    ).strip().upper()

    if data_type == "LEGACY":
        period_result = build_legacy_period_result(
            ad_row,
            report_period,
        )
    else:
        period_result = build_period_result(
            ad_row,
            report_period,
        )
    print(f"[SPEED] report {report_number} build_period_result: {perf_counter()-_t0:.2f}s")

    st.session_state[state_key] = period_result
    st.session_state[cache_key_state] = cache_key

    return period_result


if "api_view_mode" not in st.session_state:
    st.session_state.api_view_mode = "search"


try:
    # =====================================================
    # 広告元データ
    # =====================================================

    _t0 = perf_counter()

    base_ad_data = load_ad_data()

    print(
        "[SPEED] ① 広告元データ取得: "
        f"{perf_counter() - _t0:.2f}秒"
    )


    # =====================================================
    # 変更依頼 親
    # =====================================================

    _t0 = perf_counter()

    change_requests = load_change_requests()

    print(
        "[SPEED] ② 変更依頼・親取得: "
        f"{perf_counter() - _t0:.2f}秒"
    )


    # =====================================================
    # 変更依頼 明細
    # =====================================================

    _t0 = perf_counter()

    change_request_details = (
        load_change_request_details()
    )

    print(
        "[SPEED] ③ 変更依頼・明細取得: "
        f"{perf_counter() - _t0:.2f}秒"
    )


    # =====================================================
    # 完了済み変更を現在設定へ反映
    # =====================================================

    _t0 = perf_counter()

    ad_data = apply_completed_changes_to_ad_data(
        base_ad_data,
        parent_df=change_requests,
        detail_df=change_request_details,
    )

    print(
        "[SPEED] ④ 完了済み変更反映: "
        f"{perf_counter() - _t0:.2f}秒"
    )

except Exception as exc:
    st.error(
        "Googleスプレッドシートのデータ取得に失敗しました。"
    )
    st.exception(exc)
    st.stop()


if st.session_state.api_view_mode == "search":

    move_to_report = render_ad_search_view(
        ad_data,
        base_ad_data,
    )

    print(
        "[SPEED] アプリ開始 → 検索画面表示完了: "
        f"{perf_counter() - APP_START_TIME:.2f}秒"
    )

    if move_to_report:
        st.session_state.api_view_mode = "report"
        st.rerun()


elif st.session_state.api_view_mode == "report":

    report_1_ad = find_ad_by_key(
        ad_data,
        st.session_state.get("selected_ad_1_id"),
    )

    report_2_ad = find_ad_by_key(
        ad_data,
        st.session_state.get("selected_ad_2_id"),
    )

    try:
        report_1_period = build_confirmed_period(
            report_1_ad,
            st.session_state.get("report_1_period"),
        )

        report_2_period = build_confirmed_period(
            report_2_ad,
            st.session_state.get("report_2_period"),
        )

    except ValueError as exc:
        st.error(str(exc))

        if st.button(
            "← 広告検索に戻る",
            key="period_error_back",
        ):
            st.session_state.api_view_mode = "search"
            st.rerun()

        st.stop()

    try:
        report_1_period_result = get_report_period_result(
            report_number=1,
            ad_row=report_1_ad,
            report_period=report_1_period,
        )

        report_2_period_result = (
            get_report_period_result(
                report_number=2,
                ad_row=report_2_ad,
                report_period=report_2_period,
            )
            if (
                report_2_ad is not None
                and report_2_period is not None
            )
            else None
        )

    except (ValueError, RuntimeError) as exc:
        st.error(
            "Meta広告データの取得に"
            f"失敗しました：{exc}"
        )

        if st.button(
            "← 広告検索に戻る",
            key="meta_api_error_back",
        ):
            st.session_state.api_view_mode = "search"
            st.rerun()

        st.stop()

    _t0 = perf_counter()
    render_report_view(
        report_1_ad=report_1_ad,
        report_2_ad=report_2_ad,
        report_1_period=report_1_period,
        report_2_period=report_2_period,
        report_1_period_result=report_1_period_result,
        report_2_period_result=report_2_period_result,
    )

    print(f"[SPEED] render_report_view: {perf_counter()-_t0:.2f}s")

    _t0 = perf_counter()
    render_api_ppt_export_controls(
        report_1_ad=report_1_ad,
        report_1_period=report_1_period,
        report_1_period_result=report_1_period_result,
        report_2_ad=report_2_ad,
        report_2_period=report_2_period,
        report_2_period_result=report_2_period_result,
    )
    print(f"[SPEED] render_api_ppt_export_controls: {perf_counter()-_t0:.2f}s")


else:
    st.session_state.api_view_mode = "search"
    st.rerun()
