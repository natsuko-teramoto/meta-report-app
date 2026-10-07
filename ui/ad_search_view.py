from datetime import date
from time import perf_counter
import pandas as pd
import streamlit as st

from data_sources.master_source import load_applicant_master
from services.ad_search import (
    get_search_options,
    search_ads,
    build_customer_results,
    get_customer_ads,
)
from services.change_request_service import (
    get_pending_change_requests,
    build_ad_change_history_with_before_after,
)
from services.period import (
    PERIOD_MODE_MONTH,
    PERIOD_MODE_CUSTOM,
)
from ui.change_request_view import (
    render_change_request_view,
)


def _inject_change_request_style():
    """
    変更・停止依頼ボタン専用スタイル。
    """

    st.markdown(
        """
        <style>
        div[class*="st-key-change-request-button-"] button {
            background-color: #fff4cc !important;
            border-color: #e3c45b !important;
            color: #4a3b00 !important;
        }

        .st-key-change-request-button button:hover {
            background-color: #ffe99a !important;
            border-color: #c9a72d !important;
            color: #332800 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# =========================================================
# 変更・停止依頼：未完了一覧
# =========================================================

def _render_pending_change_requests(
    ad_data,
):
    """
    未対応の変更・停止依頼を
    1依頼 = 1行で表示する。
    """

    try:
        pending_df = get_pending_change_requests(
            ad_data=ad_data,
        )

    except Exception as exc:
        st.error(
            "変更・停止依頼の取得に失敗しました。"
        )
        st.exception(exc)
        return

    if pending_df.empty:
        return

    st.divider()

    st.subheader(
        f"変更・停止依頼　 {len(pending_df)}件"
    )

    # =====================================================
    # ヘッダー
    # =====================================================

    header_cols = st.columns(
        [1.5, 2.4, 1.3, 1.2, 1.5, 3.0, 2.0, 1.0],
        gap="small",
    )

    headers = [
        "依頼日時",
        "施設名",
        "訴求内容",
        "申請者",
        "依頼内容",
        "申請内容詳細",
        "掲載アカウント",
        "対応状況",
    ]

    for col, header in zip(
        header_cols,
        headers,
    ):
        with col:
            st.markdown(
                f"**{header}**"
            )

    # =====================================================
    # 依頼一覧
    # =====================================================

    for _, row in pending_df.iterrows():

        request_id = str(
            row.get(
                "依頼ID",
                "",
            )
        ).strip()

        row_cols = st.columns(
            [1.5, 2.4, 1.3, 1.2, 1.5, 3.0, 2.0, 1.0],
            gap="small",
            vertical_alignment="center",
        )

        with row_cols[0]:
            st.write(
                row.get(
                    "依頼日時",
                    "",
                )
            )

        with row_cols[1]:
            st.write(
                row.get(
                    "施設名",
                    "",
                )
            )

        with row_cols[2]:
            st.write(
                row.get(
                    "訴求内容",
                    "",
                )
            )

        with row_cols[3]:
            st.write(
                row.get(
                    "申請者",
                    "",
                )
            )

        with row_cols[4]:
            st.write(
                row.get(
                    "依頼内容",
                    "",
                )
            )

        with row_cols[5]:
            st.write(
                row.get(
                    "申請内容詳細",
                    "",
                )
            )

        with row_cols[6]:
            st.write(
                row.get(
                    "広告アカウント名",
                    "",
                )
            )

        with row_cols[7]:

            status = str(
                row.get(
                    "対応状況",
                    "",
                ) or ""
            ).strip()

            st.write(
                status
            )

# =========================================================
# 変更履歴
# =========================================================

def _render_change_history(
    ad_data,
    base_ad_data,
):
    """
    選択した広告の変更・停止依頼履歴を表示する。
    """

    ad_key = st.session_state.get(
        "change_history_ad_key"
    )

    if not ad_key:
        return

    selected_ad = _find_selected_ad(
        ad_data,
        ad_key,
    )

    if selected_ad is None:
        st.error(
            "対象広告が見つかりません。"
        )
        return

    base_ad = _find_selected_ad(
        base_ad_data,
        ad_key,
    )

    if base_ad is None:
        st.error(
            "対象広告の初期設定が見つかりません。"
        )
        return

    history_df = (
        build_ad_change_history_with_before_after(
            base_ad,
            ad_key,
        )
    )

    st.divider()

    # =====================================================
    # 見出し
    # =====================================================

    title_col, close_col = st.columns(
        [5, 1],
        vertical_alignment="center",
    )

    with title_col:

        facility_name = _display_value(
            selected_ad,
            "施設名",
        )

        appeal = _display_value(
            selected_ad,
            "訴求内容",
        )

        st.subheader(
            "変更履歴"
        )

        st.caption(
            f"{facility_name}｜{appeal}"
        )

    with close_col:

        if st.button(
            "閉じる",
            key="close_change_history",
            use_container_width=True,
        ):

            st.session_state[
                "change_history_open"
            ] = False

            st.session_state[
                "change_history_ad_key"
            ] = None

            st.rerun()


    # =====================================================
    # 履歴なし
    # =====================================================

    if history_df.empty:

        st.info(
            "変更履歴はありません。"
        )

        return


    # =====================================================
    # 履歴一覧
    # =====================================================

    st.caption(
        f"全 {len(history_df)}件"
    )

    header_cols = st.columns(
        [1.5, 1.2, 1.6, 3.0, 1.0, 1.5],
        gap="small",
    )

    headers = [
        "申請日時",
        "申請者",
        "依頼内容",
        "申請内容詳細",
        "対応状況",
        "対応完了日時",
    ]

    for col, header in zip(
        header_cols,
        headers,
    ):

        with col:
            st.markdown(
                f"**{header}**"
            )


    for _, row in history_df.iterrows():

        row_cols = st.columns(
            [1.5, 1.2, 1.6, 3.0, 1.0, 1.5],
            gap="small",
            vertical_alignment="center",
        )

        values = [
            row.get(
                "依頼日時",
                "",
            ),
            row.get(
                "申請者",
                "",
            ),
            row.get(
                "依頼内容",
                "",
            ),
            row.get(
                "申請内容詳細",
                "",
            ),
            row.get(
                "対応状況",
                "",
            ),
            row.get(
                "対応完了日時",
                "",
            ),
        ]

        for col, value in zip(
            row_cols,
            values,
        ):

            with col:
                st.write(
                    value
                )

# =========================================================
# 定数
# =========================================================

SELECT_PLACEHOLDER = "選択してください"


# =========================================================
# Session State
# =========================================================

SEARCH_DEFAULTS = {
    # 比較検索②
    "compare_search_enabled": False,

    # 検索結果
    "ad_search_1_results": None,
    "ad_search_2_results": None,

    # 選択広告
    "selected_ad_1_id": None,
    "selected_ad_2_id": None,

    # 期間設定エリア
    "report_period_open": False,

    # 確定した期間条件
    "report_1_period": None,
    "report_2_period": None,

    # 1件だけ作る確認
    "confirm_single_report": False,

    # 変更履歴
    "change_history_open": False,
    "change_history_ad_key": None,

    # 検索メッセージ
    "ad_search_1_message": "",
    "ad_search_2_message": "",
    
    # 速度計測
    "speed_search_start": None,
    "speed_report_period_start": None,
}

def initialize_ad_search_state():
    """
    広告検索画面で使用するSession Stateを初期化する。
    """

    for key, default_value in SEARCH_DEFAULTS.items():

        if key not in st.session_state:
            st.session_state[key] = default_value


# =========================================================
# 検索条件 共通
# =========================================================

def _normalize_search_value(value):
    """
    「選択してください」を検索条件なしとして扱う。
    """

    if value == SELECT_PLACEHOLDER:
        return ""

    return str(value).strip()


def _has_search_condition(form_values):
    """
    検索条件が1つ以上設定されているか。
    """

    return any(
        _normalize_search_value(value)
        for value in form_values.values()
    )


# =========================================================
# 検索条件UI
# =========================================================

def _render_search_form(
    title,
    prefix,
    options,
):
    """
    1つ分の広告検索条件を表示する。
    """

    with st.container(border=True):

        st.subheader(title)

        customer = st.selectbox(
            "顧客名",
            [SELECT_PLACEHOLDER]
            + options["customers"],
            key=f"{prefix}_customer",
        )

        prefecture = st.selectbox(
            "都道府県",
            [SELECT_PLACEHOLDER]
            + options["prefectures"],
            key=f"{prefix}_prefecture",
        )

        staff = st.selectbox(
            "営業担当・アポ担当",
            [SELECT_PLACEHOLDER]
            + options["staff"],
            key=f"{prefix}_staff",
        )

        industry = st.selectbox(
            "業種",
            [SELECT_PLACEHOLDER]
            + options["industries"],
            key=f"{prefix}_industry",
        )

        appeal = st.selectbox(
            "訴求内容",
            [SELECT_PLACEHOLDER]
            + options["appeals"],
            key=f"{prefix}_appeal",
        )

    return {
        "customer": customer,
        "prefecture": prefecture,
        "staff": staff,
        "industry": industry,
        "appeal": appeal,
    }


# =========================================================
# 検索実行
# =========================================================

def _execute_one_search(
    ad_data,
    form_values,
    result_state_key,
    message_state_key,
):
    """
    1枠分の検索を実行する。

    条件なしでは全件検索しない。
    """

    if not _has_search_condition(
        form_values
    ):

        st.session_state[
            result_state_key
        ] = None

        st.session_state[
            message_state_key
        ] = (
            "検索条件を1つ以上"
            "選択してください。"
        )

        return

    result = search_ads(
        ad_data,
        customer=_normalize_search_value(
            form_values["customer"]
        ),
        prefecture=_normalize_search_value(
            form_values["prefecture"]
        ),
        staff=_normalize_search_value(
            form_values["staff"]
        ),
        industry=_normalize_search_value(
            form_values["industry"]
        ),
        appeal=_normalize_search_value(
            form_values["appeal"]
        ),
    )

    st.session_state[
        result_state_key
    ] = result

    st.session_state[
        message_state_key
    ] = ""


# =========================================================
# 検索クリア
# =========================================================

def _clear_search(prefix):
    """
    指定した広告検索枠だけ初期化する。
    """

    for suffix in [
        "customer",
        "prefecture",
        "staff",
        "industry",
        "appeal",
    ]:

        key = f"{prefix}_{suffix}"

        if key in st.session_state:
            del st.session_state[key]

    if prefix == "ad_search_1":

        st.session_state.ad_search_1_results = None
        st.session_state.ad_search_1_message = ""
        st.session_state.selected_ad_1_id = None

    elif prefix == "ad_search_2":

        st.session_state.ad_search_2_results = None
        st.session_state.ad_search_2_message = ""
        st.session_state.selected_ad_2_id = None

    st.session_state.report_period_open = False
    st.session_state.confirm_single_report = False


# =========================================================
# 広告キー
# =========================================================

def _get_ad_key(row):
    """
    API広告・レガシー広告の両方で使える一意キーを返す。

    API広告:
        api:<ad_id>

    レガシー広告:
        legacy:<案件ID>:<キャンペーン名>
    """

    ad_id = str(row.get("ad_id", "") or "").strip()

    if ad_id:
        return f"api:{ad_id}"

    case_id = str(row.get("案件ID", "") or "").strip()
    campaign_name = str(
        row.get("キャンペーン名", "") or ""
    ).strip()

    if case_id or campaign_name:
        return f"legacy:{case_id}:{campaign_name}"

    return ""


# =========================================================
# 広告選択
# =========================================================

def _select_ad(
    ad_key,
    slot_number,
):
    """
    広告①または広告②を選択する。
    """

    st.session_state[
        f"selected_ad_{slot_number}_id"
    ] = str(ad_key)

    # 広告を選び直したら期間設定は閉じる
    st.session_state.report_period_open = False
    st.session_state.confirm_single_report = False


def _remove_selected_ad(
    slot_number,
):
    """
    選択中広告を解除する。
    """

    st.session_state[
        f"selected_ad_{slot_number}_id"
    ] = None

    st.session_state.report_period_open = False
    st.session_state.confirm_single_report = False


# =========================================================
# 広告カード
# =========================================================

def _display_value(
    row,
    column_name,
):
    """
    空欄表示を統一する。
    """

    value = row.get(
        column_name,
        "",
    )

    if value is None:
        return "―"

    value = str(value).strip()

    return value if value else "―"


def _render_ad_card(
    row,
    slot_number,
):
    """
    1広告をコンパクトな1列形式で表示する。
    """

    ad_key = _get_ad_key(row)

    selected_state_key = (
        f"selected_ad_{slot_number}_id"
    )

    selected_ad_key = st.session_state.get(
        selected_state_key
    )

    is_selected = (
        str(selected_ad_key) == ad_key
        if selected_ad_key
        else False
    )

    compare_enabled = (
        st.session_state.get(
            "compare_search_enabled",
            False,
        )
    )

    with st.container(border=True):

        # -------------------------------------------------
        # 1段目：広告情報 + 操作ボタン
        # -------------------------------------------------

        title_col, button_col = st.columns(
            [5, 2.8],
            vertical_alignment="center",
        )

        with title_col:

            facility_name = _display_value(
                row,
                "施設名",
            )

            appeal = _display_value(
                row,
                "訴求内容",
            )

            status = _display_value(
                row,
                "状態",
            )

            if status == "ACTIVE":
                status_display = "⭐ACTIVE⭐"
            else:
                status_display = status

            data_type = str(
                row.get(
                    "データ種別",
                    "",
                )
            ).strip()

            if data_type == "API":
                connection_display = "API連携"
            else:
                connection_display = (
                    "非連携アカウント"
                )

            st.markdown(
                f"**{facility_name}"
                f"｜{appeal}"
                f"｜{status_display}"
                f"｜{connection_display}**"
            )

        with button_col:

            # -----------------------------------------
            # 比較モード
            # -----------------------------------------

            if compare_enabled:

                if is_selected:

                    st.button(
                        "比較対象に選択中",
                        key=(
                            f"selected_ad_"
                            f"{slot_number}_"
                            f"{ad_key}"
                        ),
                        disabled=True,
                        use_container_width=True,
                    )

                else:

                    if st.button(
                        "比較対象に選択",
                        key=(
                            f"select_ad_"
                            f"{slot_number}_"
                            f"{ad_key}"
                        ),
                        type="primary",
                        use_container_width=True,
                    ):

                        _select_ad(
                            ad_key,
                            slot_number,
                        )

                        st.rerun()

            # -----------------------------------------
            # 通常モード
            # -----------------------------------------

            else:

                report_col, request_col, history_col = st.columns(3)

                with report_col:

                    if st.button(
                        "レポート作成",
                        key=(
                            f"report_ad_"
                            f"{slot_number}_"
                            f"{ad_key}"
                        ),
                        type="primary",
                        use_container_width=True,
                    ):
                        st.session_state.speed_report_period_start = (
                            perf_counter()
                        )                    

                        _select_ad(
                            ad_key,
                            slot_number,
                        )

                        st.session_state[
                            "report_period_open"
                        ] = True

                        st.session_state[
                            "confirm_single_report"
                        ] = False

                        st.rerun()

                with request_col:

                    if status in [
                        "ACTIVE",
                        "PAUSED",
                    ]:

                        with st.container(
                            key=f"change-request-button-{slot_number}-{ad_key}"
                        ):

                            if st.button(
                                "変更・停止依頼",
                                key=(
                                    f"change_request_"
                                    f"{slot_number}_"
                                    f"{ad_key}"
                                ),
                                use_container_width=True,
                            ):

                                st.session_state[
                                    "change_request_ad_key"
                                ] = ad_key

                                st.session_state[
                                    "change_request_open"
                                ] = True

                                st.rerun()

                with history_col:

                    if st.button(
                        "変更履歴",
                        key=(
                            f"change_history_"
                            f"{slot_number}_"
                            f"{ad_key}"
                        ),
                        use_container_width=True,
                    ):

                        st.session_state[
                            "change_history_ad_key"
                        ] = ad_key

                        st.session_state[
                            "change_history_open"
                        ] = True

                        st.rerun()

        # -------------------------------------------------
        # 2段目：広告設定
        # -------------------------------------------------

        info_cols = st.columns(
            [
                1.0,   # 都道府県
                1.5,   # エリア
                1.0,   # 年齢
                0.8,   # 性別
                1.1,   # 掲載開始
                1.1,   # 掲載終了
            ],
            vertical_alignment="top",
        )

        items = [
            (
                "都道府県",
                _display_value(
                    row,
                    "都道府県",
                ),
            ),
            (
                "エリア",
                _display_value(
                    row,
                    "エリア",
                ),
            ),
            (
                "年齢",
                _display_value(
                    row,
                    "年齢",
                ),
            ),
            (
                "性別",
                _display_value(
                    row,
                    "性別",
                ),
            ),
            (
                "掲載開始",
                _display_value(
                    row,
                    "配信開始",
                ),
            ),
            (
                "掲載終了",
                _display_value(
                    row,
                    "配信終了",
                ),
            ),
        ]

        for col, (
            label,
            value,
        ) in zip(
            info_cols,
            items,
        ):

            with col:
                st.caption(label)
                st.write(value)

# =========================================================
# 顧客一覧 + 直下広告
# =========================================================

def _render_search_results(
    title,
    search_results,
    slot_number,
    clear_prefix,
):
    """
    検索結果を

    顧客
      ↓
    案件
      ↓
    広告

    の順で表示する。
    """

    st.markdown(
        f"### {title}"
    )

    if search_results is None:
        return

    customer_results = (
        build_customer_results(
            search_results
        )
    )

    # =====================================================
    # 全体件数
    # =====================================================

    case_count = 0

    if (
        not search_results.empty
        and "案件ID" in search_results.columns
    ):
        case_count = (
            search_results["案件ID"]
            .astype(str)
            .str.strip()
            .replace("", pd.NA)
            .dropna()
            .nunique()
        )

    header_left, header_right = (
        st.columns(
            [4, 1]
        )
    )

    with header_left:

        if not customer_results.empty:

            st.caption(
                f"{len(customer_results)}顧客 / "
                f"{case_count}案件 / "
                f"{search_results['ad_id'].nunique()}広告"
            )

    with header_right:

        if st.button(
            "条件をクリア",
            key=f"{clear_prefix}_clear",
            use_container_width=True,
        ):

            _clear_search(
                clear_prefix
            )

            st.rerun()

    if customer_results.empty:

        st.info(
            "条件に一致する広告がありません。"
        )

        return

    # =====================================================
    # 顧客ごとのアコーディオン
    # =====================================================

    for _, customer_row in (
        customer_results.iterrows()
    ):

        customer_id = str(
            customer_row["Meta顧客ID"]
        )

        customer_name = str(
            customer_row["案件名"]
        )

        customer_ads = (
            get_customer_ads(
                search_results,
                customer_id,
            )
        )

        if customer_ads.empty:
            continue

        # -------------------------------------------------
        # この顧客の案件数
        # -------------------------------------------------

        customer_case_count = 0

        if "案件ID" in customer_ads.columns:

            customer_case_count = (
                customer_ads["案件ID"]
                .astype(str)
                .str.strip()
                .replace("", pd.NA)
                .dropna()
                .nunique()
            )

        ad_count = (
            customer_row["広告数"]
        )

        expander_label = (
            f"{customer_name}"
            f"　｜　"
            f"{customer_case_count}案件 / "
            f"{ad_count}広告"
        )

        with st.expander(
            expander_label,
            expanded=False,
        ):

            # =================================================
            # 案件ID単位でまとめる
            # =================================================

            if "案件ID" not in customer_ads.columns:

                for _, ad_row in (
                    customer_ads.iterrows()
                ):

                    _render_ad_card(
                        ad_row,
                        slot_number,
                    )

                continue

            # 案件IDの表示順を維持
            case_ids = []

            for case_id in (
                customer_ads["案件ID"]
                .astype(str)
                .str.strip()
                .tolist()
            ):

                if (
                    case_id
                    and case_id not in case_ids
                ):
                    case_ids.append(
                        case_id
                    )

            # =================================================
            # 案件 → 広告
            # =================================================

            for case_id in case_ids:

                case_ads = customer_ads[
                    customer_ads[
                        "案件ID"
                    ]
                    .astype(str)
                    .str.strip()
                    == case_id
                ].copy()

                if case_ads.empty:
                    continue

                first_row = (
                    case_ads.iloc[0]
                )

                facility_name = (
                    _display_value(
                        first_row,
                        "施設名",
                    )
                )

                appeal = (
                    _display_value(
                        first_row,
                        "訴求内容",
                    )
                )

                case_ad_count = len(
                    case_ads
                )

                # ---------------------------------------------
                # 案件見出し
                # ---------------------------------------------

                with st.container(
                    border=True
                ):

                    st.markdown(
                        f"**{case_id}"
                        f"｜{facility_name}"
                        f"｜{appeal}**"
                    )

                    st.caption(
                        f"この案件の広告："
                        f"{case_ad_count}件"
                    )

                    # -----------------------------------------
                    # 同じ案件に属する広告
                    # -----------------------------------------

                    for _, ad_row in (
                        case_ads.iterrows()
                    ):

                        _render_ad_card(
                            ad_row,
                            slot_number,
                        )


# =========================================================
# 選択広告取得
# =========================================================

def _find_selected_ad(
    ad_data,
    ad_key,
):
    """
    API広告・レガシー広告共通の広告キーから
    広告情報を取得する。
    """

    if not ad_key:
        return None

    matched = ad_data[
        ad_data.apply(
            _get_ad_key,
            axis=1,
        ).astype(str)
        == str(ad_key)
    ]

    if matched.empty:
        return None

    return matched.iloc[0]


# =========================================================
# 選択中広告
# =========================================================

def _render_selected_ad_summary(
    ad_data,
    slot_number,
):
    """
    選択中広告の内容を確認できる形で表示する。
    """

    ad_key = st.session_state.get(
        f"selected_ad_{slot_number}_id"
    )

    selected_ad = _find_selected_ad(
        ad_data,
        ad_key,
    )

    if selected_ad is None:
        return

    with st.container(
        border=True
    ):

        # -------------------------------------------------
        # 1段目：広告名 + 選択解除
        # -------------------------------------------------

        left_col, right_col = (
            st.columns(
                [5, 1],
                vertical_alignment="center",
            )
        )

        with left_col:

            facility_name = _display_value(
                selected_ad,
                "施設名",
            )

            appeal = _display_value(
                selected_ad,
                "訴求内容",
            )

            status = _display_value(
                selected_ad,
                "状態",
            )

            if status == "ACTIVE":
                status_display = "⭐ACTIVE⭐"
            else:
                status_display = status

            data_type = str(
                selected_ad.get(
                    "データ種別",
                    "",
                )
            ).strip()

            if data_type == "API":
                connection_display = "API連携"
            else:
                connection_display = (
                    "非連携アカウント"
                )

            st.markdown(
                f"**{facility_name}"
                f"｜{appeal}"
                f"｜{status_display}"
                f"｜{connection_display}**"
            )

        with right_col:

            if st.button(
                "選択を解除",
                key=(
                    f"remove_selected_ad_"
                    f"{slot_number}"
                ),
                use_container_width=True,
            ):

                _remove_selected_ad(
                    slot_number
                )

                st.rerun()

        # -------------------------------------------------
        # 2段目：選択した広告の設定内容
        # -------------------------------------------------

        info_cols = st.columns(
            [
                1.5,   # エリア
                1.0,   # 年齢
                0.8,   # 性別
                1.1,   # 掲載開始
                1.1,   # 掲載終了
            ],
            vertical_alignment="top",
        )

        items = [
            (
                "エリア",
                _display_value(
                    selected_ad,
                    "エリア",
                ),
            ),
            (
                "年齢",
                _display_value(
                    selected_ad,
                    "年齢",
                ),
            ),
            (
                "性別",
                _display_value(
                    selected_ad,
                    "性別",
                ),
            ),
            (
                "掲載開始",
                _display_value(
                    selected_ad,
                    "配信開始",
                ),
            ),
            (
                "掲載終了",
                _display_value(
                    selected_ad,
                    "配信終了",
                ),
            ),
        ]

        for col, (
            label,
            value,
        ) in zip(
            info_cols,
            items,
        ):

            with col:
                st.caption(label)
                st.write(value)

# =========================================================
# 比較②
# =========================================================

def _enable_compare_search():
    """
    比較用広告②を表示する。
    """

    st.session_state.compare_search_enabled = True
    st.session_state.report_period_open = False
    st.session_state.confirm_single_report = False


def _remove_compare_search():
    """
    比較用広告②を閉じて関連状態も消す。
    """

    _clear_search(
        "ad_search_2"
    )

    st.session_state.compare_search_enabled = False
    st.session_state.selected_ad_2_id = None
    st.session_state.report_period_open = False
    st.session_state.confirm_single_report = False


# =========================================================
# 期間
# =========================================================

def _render_one_period(
    slot_number,
    title,
):
    """
    1広告分のレポート期間設定を表示する。

    月次
        カレンダー月を指定する。

    期間指定
        開始日・終了日を指定する。
    """

    st.markdown(
        f"#### {title}"
    )

    mode_label = st.radio(
        "期間の指定方法",
        [
            "月次",
            "期間指定",
        ],
        horizontal=True,
        key=f"report_{slot_number}_period_mode",
    )

    # -----------------------------------------------------
    # 月次
    # -----------------------------------------------------

    if mode_label == "月次":

        year_col, month_col = st.columns(2)

        today = date.today()

        if today.month == 1:
            default_year = today.year - 1
            default_month = 12
        else:
            default_year = today.year
            default_month = today.month - 1

        with year_col:

            year = st.selectbox(
                "年",
                list(
                    range(
                        default_year,
                        2009,
                        -1,
                    )
                ),
                key=f"report_{slot_number}_year",
            )

        with month_col:

            month = st.selectbox(
                "月",
                list(
                    range(
                        1,
                        13,
                    )
                ),
                index=default_month - 1,
                format_func=lambda value: f"{value}月",
                key=f"report_{slot_number}_month",
            )

        return {
            "mode": PERIOD_MODE_MONTH,
            "year": year,
            "month": month,
        }

    # -----------------------------------------------------
    # 期間指定
    # -----------------------------------------------------

    start_col, end_col = st.columns(2)

    with start_col:

        target_start = st.date_input(
            "開始日",
            value=None,
            key=f"report_{slot_number}_custom_start",
        )

    with end_col:

        target_end = st.date_input(
            "終了日",
            value=None,
            key=f"report_{slot_number}_custom_end",
        )

    return {
        "mode": PERIOD_MODE_CUSTOM,
        "target_start": target_start,
        "target_end": target_end,
    }


def _validate_period_input(
    period_input,
):
    """
    画面で入力された期間条件の基本チェック。

    比較期間・累計期間の計算はここでは行わない。
    services/period.py が担当する。
    """

    if period_input["mode"] == PERIOD_MODE_MONTH:

        year = period_input["year"]
        month = period_input["month"]

        first_day = date(
            year,
            month,
            1,
        )

        if first_day > date.today():

            return (
                False,
                "未来の月は指定できません。",
            )

        return True, ""

    if period_input["mode"] == PERIOD_MODE_CUSTOM:

        target_start = period_input[
            "target_start"
        ]

        target_end = period_input[
            "target_end"
        ]

        if (
            target_start is None
            or target_end is None
        ):

            return (
                False,
                "開始日と終了日を入力してください。",
            )

        if target_start > target_end:

            return (
                False,
                "開始日は終了日以前にしてください。",
            )

        if target_end > date.today():

            return (
                False,
                "終了日に未来の日付は指定できません。",
            )

        return True, ""

    return (
        False,
        "期間の指定方法が不正です。",
    )


# =========================================================
# メイン
# =========================================================

def render_ad_search_view(
    ad_data,
    base_ad_data,
):
    """
    広告検索画面。

    Returns
    -------
    bool
        レポート画面へ遷移する場合 True
    """

    _inject_change_request_style()

    initialize_ad_search_state()

    # =====================================================
    # 変更・停止依頼画面
    # =====================================================

    if st.session_state.get(
        "change_request_open",
        False,
    ):

        render_change_request_view(
            ad_data
        )

        return False

    # =====================================================
    # 変更履歴画面
    # =====================================================

    if st.session_state.get(
        "change_history_open",
        False,
    ):

        _render_change_history(
            ad_data,
            base_ad_data,
        )

        return False

    options = get_search_options(
        ad_data
    )

    st.title(
        "Meta広告レポート"
    )

    st.caption(
        "広告を検索して"
        "レポートを作成します。"
    )



    compare_enabled = (
        st.session_state.compare_search_enabled
    )

    # =====================================================
    # 広告検索
    # =====================================================

    st.subheader(
        "広告検索"
    )

    # -----------------------------------------------------
    # ①のみ
    # -----------------------------------------------------

    if not compare_enabled:

        search_1_form = (
            _render_search_form(
                "広告検索①",
                "ad_search_1",
                options,
            )
        )

        search_2_form = None

        if st.button(
            "＋ 比較用の広告②を追加",
            key="enable_compare_search",
        ):

            _enable_compare_search()
            st.rerun()

    # -----------------------------------------------------
    # ① + ②
    # -----------------------------------------------------

    else:

        search_col_1, search_col_2 = (
            st.columns(
                2,
                gap="large",
            )
        )

        with search_col_1:

            search_1_form = (
                _render_search_form(
                    "広告検索①",
                    "ad_search_1",
                    options,
                )
            )

        with search_col_2:

            search_2_form = (
                _render_search_form(
                    "広告検索②",
                    "ad_search_2",
                    options,
                )
            )

            if st.button(
                "比較用の広告②を閉じる",
                key="remove_compare_search",
            ):

                _remove_compare_search()
                st.rerun()

    # =====================================================
    # 検索
    # =====================================================

    if st.button(
        "検索",
        type="primary",
        use_container_width=True,
        key="shared_ad_search_button",
    ):

        st.session_state.speed_search_start = perf_counter()

        _execute_one_search(
            ad_data=ad_data,
            form_values=search_1_form,
            result_state_key=(
                "ad_search_1_results"
            ),
            message_state_key=(
                "ad_search_1_message"
            ),
        )

        st.session_state.selected_ad_1_id = None

        if compare_enabled:

            _execute_one_search(
                ad_data=ad_data,
                form_values=search_2_form,
                result_state_key=(
                    "ad_search_2_results"
                ),
                message_state_key=(
                    "ad_search_2_message"
                ),
            )

            st.session_state.selected_ad_2_id = None

        else:

            st.session_state.ad_search_2_results = None
            st.session_state.ad_search_2_message = ""
            st.session_state.selected_ad_2_id = None

        st.session_state.report_period_open = False
        st.session_state.confirm_single_report = False

        st.rerun()


    # =====================================================
    # 検索メッセージ
    # =====================================================

    message_1 = (
        st.session_state.ad_search_1_message
    )

    message_2 = (
        st.session_state.ad_search_2_message
    )

    if message_1:

        st.warning(
            f"広告検索①：{message_1}"
        )

    if (
        compare_enabled
        and message_2
    ):

        st.warning(
            f"広告検索②：{message_2}"
        )

    # =====================================================
    # 検索結果
    # =====================================================

    result_1 = (
        st.session_state.ad_search_1_results
    )

    result_2 = (
        st.session_state.ad_search_2_results
    )

    has_result_area = (
        result_1 is not None
        or (
            compare_enabled
            and result_2 is not None
        )
    )

    if not has_result_area:
        _render_pending_change_requests(
            ad_data,
        )

    if has_result_area:

        st.divider()

        # ---------------------------------------------
        # ①のみ
        # ---------------------------------------------

        if not compare_enabled:

            _render_search_results(
                title="広告検索結果",
                search_results=result_1,
                slot_number=1,
                clear_prefix="ad_search_1",
            )

        # ---------------------------------------------
        # ① + ②
        # ---------------------------------------------

        else:

            result_col_1, result_col_2 = (
                st.columns(
                    2,
                    gap="large",
                )
            )

            with result_col_1:

                _render_search_results(
                    title="広告検索結果①",
                    search_results=result_1,
                    slot_number=1,
                    clear_prefix="ad_search_1",
                )

            with result_col_2:

                _render_search_results(
                    title="広告検索結果②",
                    search_results=result_2,
                    slot_number=2,
                    clear_prefix="ad_search_2",
                )

    # =====================================================
    # 検索速度計測
    # =====================================================

    if (
        has_result_area
        and st.session_state.get("speed_search_start")
        is not None
    ):
        print(
            "[SPEED] 検索ボタン → 検索結果表示完了: "
            f"{perf_counter() - st.session_state.speed_search_start:.2f}秒"
        )

        st.session_state.speed_search_start = None

    # =====================================================
    # 選択中広告
    # =====================================================

    selected_1 = (
        st.session_state.selected_ad_1_id
    )

    selected_2 = (
        st.session_state.selected_ad_2_id
    )

    if selected_1 or selected_2:

        st.divider()

        st.subheader(
            "選択中の広告"
        )

        if compare_enabled:

            summary_col_1, summary_col_2 = (
                st.columns(
                    2,
                    gap="large",
                )
            )

            with summary_col_1:

                if selected_1:

                    _render_selected_ad_summary(
                        ad_data,
                        slot_number=1,
                    )

                else:

                    st.info(
                        "広告①を選択してください。"
                    )

            with summary_col_2:

                if selected_2:

                    _render_selected_ad_summary(
                        ad_data,
                        slot_number=2,
                    )

                else:

                    st.info(
                        "広告②を選択してください。"
                    )

        else:

            if selected_1:

                _render_selected_ad_summary(
                    ad_data,
                    slot_number=1,
                )

    # =====================================================
    # 期間設定へ進む
    # =====================================================

    if selected_1:

        if not st.session_state.report_period_open:

            if st.button(
                "期間を設定してレポート作成へ進む",
                type="primary",
                use_container_width=True,
                key="open_report_period",
            ):

                # 比較②を使っているのに
                # 広告②が未選択
                if (
                    compare_enabled
                    and not selected_2
                ):

                    st.session_state.confirm_single_report = True
                    st.rerun()

                else:

                    st.session_state.report_period_open = True
                    st.session_state.confirm_single_report = False
                    st.rerun()

    # =====================================================
    # 比較②未選択確認
    # =====================================================

    if st.session_state.confirm_single_report:

        st.warning(
            "比較用の広告②が"
            "選択されていません。"
            "広告①のみで"
            "レポートを作成しますか？"
        )

        yes_col, continue_col = (
            st.columns(2)
        )

        with yes_col:

            if st.button(
                "はい、1件で作成する",
                type="primary",
                use_container_width=True,
                key="confirm_single_yes",
            ):

                # 比較モード自体を解除
                _remove_compare_search()

                st.session_state.report_period_open = True
                st.session_state.confirm_single_report = False

                st.rerun()

        with continue_col:

            if st.button(
                "広告②を選択する",
                use_container_width=True,
                key="confirm_single_no",
            ):

                st.session_state.confirm_single_report = False
                st.rerun()

    # =====================================================
    # 期間入力
    # =====================================================

    if (
        st.session_state.report_period_open
        and selected_1
    ):

        st.divider()

        with st.container(
            border=True
        ):

            st.subheader(
                "レポート期間"
            )

            st.caption(
                "月次はカレンダー月単位、"
                "期間指定は任意の日付範囲で集計します。\n\n"
                "API連携：月次、期間指定どちらも可能  \n"
                "非連携アカウント：月次のみ"
            )

            # -----------------------------------------
            # 1件
            # -----------------------------------------

            if not compare_enabled:

                period_1 = _render_one_period(
                    slot_number=1,
                    title="期間",
                )

                period_2 = None

            # -----------------------------------------
            # 2件
            # -----------------------------------------

            else:

                period_col_1, period_col_2 = (
                    st.columns(
                        2,
                        gap="large",
                    )
                )

                with period_col_1:

                    period_1 = _render_one_period(
                        slot_number=1,
                        title="広告①",
                    )

                with period_col_2:

                    period_2 = _render_one_period(
                        slot_number=2,
                        title="広告②",
                    )

            st.divider()

            # -----------------------------------------
            # レポート作成
            # -----------------------------------------
            if (
                st.session_state.get(
                    "speed_report_period_start"
                )
                is not None
            ):
                print(
                    "[SPEED] 広告指定 → 期間指定表示完了: "
                    f"{perf_counter() - st.session_state.speed_report_period_start:.2f}秒"
                )

                st.session_state.speed_report_period_start = None

            if st.button(
                "レポート作成",
                type="primary",
                use_container_width=True,
                key="create_report_final",
            ):

                selected_ad_1 = _find_selected_ad(
                    ad_data,
                    selected_1,
                )

                selected_ad_2 = (
                    _find_selected_ad(
                        ad_data,
                        selected_2,
                    )
                    if selected_2
                    else None
                )

                # -------------------------------------
                # レガシー広告は期間指定不可
                # -------------------------------------

                if (
                    selected_ad_1 is not None
                    and str(
                        selected_ad_1.get(
                            "データ種別",
                            "",
                        )
                    ).strip().upper() == "LEGACY"
                    and period_1["mode"] == PERIOD_MODE_CUSTOM
                ):
                    st.warning(
                        "API連携アカウントではないため、"
                        "期間指定レポートは作成できません。"
                        "月次を選択してください。"
                    )
                    return False

                if (
                    selected_ad_2 is not None
                    and str(
                        selected_ad_2.get(
                            "データ種別",
                            "",
                        )
                    ).strip().upper() == "LEGACY"
                    and period_2 is not None
                    and period_2["mode"] == PERIOD_MODE_CUSTOM
                ):
                    st.warning(
                        "広告②はAPI連携アカウントではないため、"
                        "期間指定レポートは作成できません。"
                        "月次を選択してください。"
                    )
                    return False
            

                valid_1, error_1 = (
                    _validate_period_input(
                        period_1
                    )
                )

                if not valid_1:

                    st.error(
                        f"広告①：{error_1}"
                    )

                    return False

                if compare_enabled:

                    valid_2, error_2 = (
                        _validate_period_input(
                            period_2
                        )
                    )

                    if not valid_2:

                        st.error(
                            f"広告②：{error_2}"
                        )

                        return False

                # -------------------------------------
                # 確定した期間条件を保存
                # -------------------------------------

                st.session_state.report_1_period = (
                    period_1
                )

                st.session_state.report_2_period = (
                    period_2
                    if compare_enabled
                    else None
                )

                return True

    # =====================================================
    # 変更・停止依頼一覧
    # =====================================================

    if has_result_area:
        _render_pending_change_requests(
            ad_data,
        )

    return False