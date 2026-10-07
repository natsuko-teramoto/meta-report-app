import streamlit as st

from data_sources.master_source import (
    load_applicant_master,
    load_change_requests,
    load_change_request_details,
)
from services.change_request_service import register_change_request
from services.ad_search import (
    get_ad_key,
    find_ad_by_key,
)

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



def render_change_request_view(
    ad_data,
):
    """
    広告の変更・停止依頼画面。
    """

    # =========================================================
    # 登録完了後
    # =========================================================

    completed_request_id = st.session_state.get(
        "change_request_completed_id"
    )

    if completed_request_id:
        st.success(
            f"依頼を登録しました。"
            f" 依頼ID：{completed_request_id}"
        )

        if st.button(
            "広告検索へ戻る",
            key="change_request_back_completed",
            use_container_width=True,
        ):
            st.session_state[
                "change_request_completed_id"
            ] = None

            st.session_state[
                "change_request_open"
            ] = False

            st.session_state[
                "change_request_ad_key"
            ] = None

            st.rerun()

        return

    ad_key = st.session_state.get(
        "change_request_ad_key"
    )

    if not ad_key:
        st.error(
            "対象広告を特定できませんでした。"
        )

        if st.button(
            "広告検索へ戻る",
            key="change_request_back_error",
        ):
            st.session_state[
                "change_request_open"
            ] = False

            st.session_state[
                "change_request_ad_key"
            ] = None

            st.rerun()

        return

    selected_ad = find_ad_by_key(
        ad_data,
        ad_key,
    )

    if selected_ad is None:
        st.error(
            "対象広告のデータが見つかりませんでした。"
        )

        if st.button(
            "広告検索へ戻る",
            key="change_request_back_not_found",
        ):
            st.session_state[
                "change_request_open"
            ] = False

            st.session_state[
                "change_request_ad_key"
            ] = None

            st.rerun()

        return

    # ==================================================
    # タイトル
    # ==================================================

    st.title(
        "変更・停止依頼"
    )

    if st.button(
        "← 広告検索へ戻る",
        key="change_request_back",
    ):
        st.session_state[
            "change_request_open"
        ] = False

        st.session_state[
            "change_request_ad_key"
        ] = None

        st.rerun()

    # ==================================================
    # 対象広告
    # ==================================================

    st.subheader(
        "対象広告"
    )

    with st.container(
        border=True
    ):

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

        info_cols = st.columns(
            [
                1.5,
                1.0,
                0.8,
                1.1,
                1.1,
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

    # ==================================================
    # 申請内容
    # ==================================================

    st.subheader(
        "申請内容"
    )

    # --------------------------------------------------
    # 申請者
    # ※次の工程で申請者マスタと接続する
    # --------------------------------------------------

    applicant_df = load_applicant_master()

    if applicant_df.empty:

        st.warning(
            "有効な申請者が登録されていません。"
        )

        applicant = None

    else:

        applicant_options = (
            applicant_df[
                [
                    "申請者ID",
                    "申請者名",
                ]
            ]
            .to_dict("records")
        )

        applicant = st.selectbox(
            "申請者",
            options=[
                None,
                *applicant_options,
            ],
            format_func=lambda x: (
                "選択してください"
                if x is None
                else x["申請者名"]
            ),
            key="change_request_applicant",
        )
    # ==================================================
    # 依頼内容
    # まず「設定変更」か「配信停止」のどちらかを選択
    # ==================================================

    st.markdown(
        "**依頼内容**"
    )

    if status == "PAUSED":
        request_category_options = [
            "設定・広告内容変更",
            "配信再開・停止",
        ]
    else:
        request_category_options = [
            "設定・広告内容変更",
            "配信停止",
        ]

    request_category = st.radio(
        "依頼内容",
        options=request_category_options,
        index=None,
        key="change_request_category",
        horizontal=True,
        label_visibility="collapsed",
    )


    # ==================================================
    # 初期値
    # ==================================================

    target_change = False
    area_change = False
    budget_change = False
    period_change = False
    text_change = False
    creative_change = False

    delivery_request = None
    delivery_reason = ""


    # ==================================================
    # 1. 設定・広告内容変更
    # 複数選択可
    # ==================================================

    if request_category == "設定・広告内容変更":

        st.markdown(
            "**設定・広告内容変更（複数選択可）**"
        )

        col_1, col_2 = st.columns(2)

        with col_1:

            target_change = st.checkbox(
                "ターゲット変更",
                key="change_request_target",
            )

            area_change = st.checkbox(
                "エリア変更",
                key="change_request_area",
            )

            budget_change = st.checkbox(
                "予算変更",
                key="change_request_budget",
            )

        with col_2:

            period_change = st.checkbox(
                "配信期間延長（更新以外）",
                key="change_request_period",
            )

            text_change = st.checkbox(
                "テキストやリンク先変更など",
                key="change_request_text",
            )

            creative_change = st.checkbox(
                "クリエイティブ差し替え",
                key="change_request_creative",
            )

        # ==================================================
        # ターゲット変更
        # ==================================================

        target_change_type = None
        new_age_min = None
        new_age_max = None
        new_gender = None

        if target_change:

            st.divider()

            st.markdown(
                "#### ターゲット変更"
            )


            # ------------------------------------------
            # 現在の設定
            # ------------------------------------------

            current_age = _display_value(
                selected_ad,
                "年齢",
            )

            current_gender = _display_value(
                selected_ad,
                "性別",
            )

            st.markdown(
                "**現在の設定**"
            )

            current_col_1, current_col_2 = st.columns(2)

            with current_col_1:
                st.write(
                    f"年齢：{current_age}"
                )

            with current_col_2:
                st.write(
                    f"性別：{current_gender}"
                )


            # ------------------------------------------
            # 変更する項目
            # ------------------------------------------

            target_change_type = st.selectbox(
                "変更する項目",
                options=[
                    "",
                    "年齢",
                    "性別",
                    "年齢と性別",
                ],
                index=0,
                key="change_request_target_type",
                format_func=lambda value: (
                    "選択してください"
                    if value == ""
                    else value
                ),
            )


            # ------------------------------------------
            # 年齢変更
            # ------------------------------------------

            if target_change_type in [
                "年齢",
                "年齢と性別",
            ]:

                st.markdown(
                    "**変更後の年齢**"
                )

                age_col_1, age_col_2 = st.columns(2)

                age_values = list(
                    range(
                        18,
                        66,
                    )
                )

                with age_col_1:

                    new_age_min = st.selectbox(
                        "年齢下限",
                        options=[
                            None,
                            *age_values,
                        ],
                        index=0,
                        key="change_request_age_min",
                        format_func=lambda value: (
                            "選択してください"
                            if value is None
                            else f"{value}歳"
                        ),
                    )

                with age_col_2:

                    new_age_max = st.selectbox(
                        "年齢上限",
                        options=[
                            None,
                            *age_values,
                            "上限なし",
                        ],
                        index=0,
                        key="change_request_age_max",
                        format_func=lambda value: (
                            "選択してください"
                            if value is None
                            else (
                                value
                                if value == "上限なし"
                                else f"{value}歳"
                            )
                        ),
                    )


            # ------------------------------------------
            # 性別変更
            # ------------------------------------------

            if target_change_type in [
                "性別",
                "年齢と性別",
            ]:

                st.markdown(
                    "**変更後の性別**"
                )

                new_gender = st.selectbox(
                    "性別",
                    options=[
                        "",
                        "男性",
                        "女性",
                        "性別問わない",
                    ],
                    index=0,
                    key="change_request_gender",
                    format_func=lambda value: (
                        "選択してください"
                        if value == ""
                        else value
                    ),
                )


        # ==================================================
        # エリア変更
        # ==================================================

        area_method = None
        distance_change_type = None
        new_point_type = None
        new_point_name = ""
        new_distance = None
        new_municipalities = ""

        if area_change:

            st.divider()

            st.markdown(
                "#### エリア変更"
            )


            # ------------------------------------------
            # 現在の設定
            # ------------------------------------------

            current_area = _display_value(
                selected_ad,
                "エリア",
            )

            st.markdown(
                "**現在の設定**"
            )

            st.write(
                f"エリア：{current_area}"
            )


            # ------------------------------------------
            # エリアの指定方法
            # ------------------------------------------

            area_method = st.radio(
                "エリアの指定方法",
                options=[
                    "地点からの距離",
                    "市区町村",
                ],
                index=None,
                key="change_request_area_method",
                horizontal=True,
            )


            # ==================================================
            # 地点からの距離
            # ==================================================

            if area_method == "地点からの距離":

                distance_change_type = st.radio(
                    "変更する項目",
                    options=[
                        "地点のみ変更",
                        "距離のみ変更",
                        "地点と距離、両方変更",
                    ],
                    index=None,
                    key="change_request_distance_change_type",
                )


                # ------------------------------------------
                # 地点を変更する場合
                # ------------------------------------------

                if distance_change_type in [
                    "地点のみ変更",
                    "地点と距離、両方変更",
                ]:

                    st.markdown(
                        "**変更後の地点**"
                    )

                    new_point_type = st.selectbox(
                        "地点種別",
                        options=[
                            "",
                            "医院",
                            "駅",
                            "その他ランドマーク",
                        ],
                        index=0,
                        key="change_request_point_type",
                        format_func=lambda value: (
                            "選択してください"
                            if value == ""
                            else value
                        ),
                    )


                    # 医院の場合は施設情報を使うため入力不要
                    if new_point_type in [
                        "駅",
                        "その他ランドマーク",
                    ]:

                        new_point_name = st.text_input(
                            "地点名",
                            key="change_request_point_name",
                            placeholder=(
                                "例：吉祥寺駅"
                                if new_point_type == "駅"
                                else "地点名を入力してください"
                            ),
                        )


                # ------------------------------------------
                # 距離を変更する場合
                # ------------------------------------------

                if distance_change_type in [
                    "距離のみ変更",
                    "地点と距離、両方変更",
                ]:

                    st.markdown(
                        "**変更後の距離**"
                    )

                    new_distance = st.number_input(
                        "距離（km）",
                        min_value=1.0,
                        max_value=80.0,
                        value=None,
                        step=1.0,
                        key="change_request_distance",
                        placeholder="距離を半角数字で入力してください",
                    )


            # ==================================================
            # 市区町村
            # ==================================================

            elif area_method == "市区町村":

                st.markdown(
                    "**変更後の市区町村**"
                )

                new_municipalities = st.text_input(
                    "市区町村",
                    key="change_request_municipalities",
                    placeholder="例：世田谷区、目黒区",
                )


        # ==================================================
        # 予算変更
        # ==================================================

        new_annual_budget = ""
        budget_approved = False

        if budget_change:

            st.divider()

            st.markdown(
                "#### 予算変更"
            )


            # ------------------------------------------
            # 現在の設定
            # ------------------------------------------

            current_annual_budget = _display_value(
                selected_ad,
                "年間広告費",
            )

            st.markdown(
                "**現在の設定**"
            )

            # 現在値を表示用にカンマ区切りへ
            current_budget_display = current_annual_budget

            try:
                current_budget_number = int(
                    float(
                        str(current_annual_budget)
                        .replace(",", "")
                        .replace("円", "")
                        .strip()
                    )
                )

                current_budget_display = (
                    f"{current_budget_number:,}円"
                )

            except (ValueError, TypeError):
                if current_annual_budget != "―":
                    current_budget_display = (
                        f"{current_annual_budget}"
                    )

            st.write(
                f"年間広告費：{current_budget_display}"
            )


            # ------------------------------------------
            # 変更後
            # ------------------------------------------

            st.markdown(
                "**変更後**"
            )

            new_annual_budget = st.text_input(
                "年間広告費",
                key="change_request_annual_budget",
                placeholder="半角数字・カンマなしで入力してください",
            )


            # ------------------------------------------
            # 入力チェック・表示
            # ------------------------------------------

            if new_annual_budget:

                if new_annual_budget.isascii() \
                        and new_annual_budget.isdigit():

                    new_budget_number = int(
                        new_annual_budget
                    )

                    st.caption(
                        f"変更後：{new_budget_number:,}円"
                    )

                else:

                    st.error(
                        "年間広告費は半角数字・カンマなしで入力してください。"
                    )


            # ------------------------------------------
            # 承認
            # ------------------------------------------

            budget_approved = st.checkbox(
                "承認取得済み",
                key="change_request_budget_approved",
            )            


        # ==================================================
        # 配信期間延長（更新以外）
        # ==================================================

        new_end_date = None
        period_extension_reason = ""
        period_extension_approved = False

        if period_change:

            st.divider()

            st.markdown(
                "#### 配信期間延長（更新以外）"
            )


            # ------------------------------------------
            # 現在の設定
            # ------------------------------------------

            current_end_date = _display_value(
                selected_ad,
                "配信終了",
            )

            st.markdown(
                "**現在の設定**"
            )

            st.write(
                f"配信終了日：{current_end_date}"
            )


            # ------------------------------------------
            # 変更後
            # ------------------------------------------

            st.markdown(
                "**変更後**"
            )

            new_end_date = st.date_input(
                "配信終了日",
                value=None,
                key="change_request_end_date",
                format="YYYY/MM/DD",
            )

            period_extension_reason = st.text_input(
                "延長理由",
                key="change_request_period_reason",
                placeholder="延長理由を入力してください",
            )


            # ------------------------------------------
            # 承認
            # ------------------------------------------

            period_extension_approved = st.checkbox(
                "承認取得済み",
                key="change_request_period_approved",
            )

        # ==================================================
        # テキストやリンク先変更など
        # ==================================================

        text_change_detail = ""

        if text_change:

            st.divider()

            st.markdown(
                "#### テキストやリンク先変更など"
            )

            text_change_detail = st.text_input(
                "変更内容",
                key="change_request_text_detail",
                placeholder="変更内容を入力してください",
            )

        # ==================================================
        # クリエイティブ差し替え
        # ==================================================

        creative_confirmed = False

        if creative_change:

            st.divider()

            st.markdown(
                "#### クリエイティブ差し替え"
            )

            creative_confirmed = st.checkbox(
                "顧客確認済み",
                key="change_request_creative_confirmed",
            )

    # ==================================================
    # 2. 配信停止
    # ==================================================

    elif request_category in [
        "配信停止",
        "配信再開・停止",
    ]:


        # --------------------------------------------------
        # ACTIVE広告
        # --------------------------------------------------

        if status == "ACTIVE":

            st.markdown(
                "**配信停止理由**"
            )

            delivery_request = st.selectbox(
                "配信停止理由",
                options=[
                    "",
                    "期間終了をもって更新せず",
                    "クリエイティブ変更・顧客対応のため一時停止",
                    "強制解約",
                    "その他",
                ],
                index=0,
                key="change_request_delivery_active",
                format_func=lambda value: (
                    "選択してください"
                    if value == ""
                    else value
                ),
                label_visibility="collapsed",
            )

            if delivery_request == "その他":

                delivery_reason = st.text_input(
                    "その他の理由",
                    key="change_request_delivery_other",
                    placeholder="理由を入力してください",
                )


        # --------------------------------------------------
        # PAUSED広告
        # --------------------------------------------------

        elif status == "PAUSED":

            st.markdown(
                "**配信について**"
            )

            delivery_request = st.selectbox(
                "配信について",
                options=[
                    "",
                    "配信再開",
                    "配信停止",
                    "強制解約",
                ],
                index=0,
                key="change_request_delivery_paused",
                format_func=lambda value: (
                    "選択してください"
                    if value == ""
                    else value
                ),
                label_visibility="collapsed",
            )

            if delivery_request == "配信停止":

                delivery_reason = st.text_input(
                    "停止理由",
                    key="change_request_delivery_pause_reason",
                    placeholder="理由を入力してください",
                )


    # ==================================================
    # 選択中の依頼内容
    # ==================================================

    selected_types = []

    if target_change:
        selected_types.append(
            "ターゲット変更"
        )

    if area_change:
        selected_types.append(
            "エリア変更"
        )

    if budget_change:
        selected_types.append(
            "予算変更"
        )

    if period_change:
        selected_types.append(
            "配信期間延長（更新以外）"
        )

    if text_change:
        selected_types.append(
            "テキストやリンク先変更など"
        )

    if creative_change:
        selected_types.append(
            "クリエイティブ差し替え"
        )

    if delivery_request:
        selected_types.append(
            delivery_request
        )


    # ==================================================
    # 選択内容の確認表示
    # ==================================================

    if selected_types:

        st.info(
            "選択中："
            + "・".join(
                selected_types
            )
        )

    # ==================================================
    # 必須入力チェック
    # ==================================================

    validation_errors = []

    # 申請者
    if applicant is None:
        validation_errors.append(
            "申請者を選択してください。"
        )

    # 依頼内容
    if request_category is None:
        validation_errors.append(
            "依頼内容を選択してください。"
        )


    # ==================================================
    # 設定・広告内容変更
    # ==================================================

    if request_category == "設定・広告内容変更":

        if not selected_types:
            validation_errors.append(
                "変更する項目を1つ以上選択してください。"
            )


        # ------------------------------------------
        # ターゲット変更
        # ------------------------------------------

        if target_change:

            if not target_change_type:
                validation_errors.append(
                    "ターゲット変更の項目を選択してください。"
                )

            if target_change_type in [
                "年齢",
                "年齢と性別",
            ]:

                if new_age_min is None:
                    validation_errors.append(
                        "年齢下限を選択してください。"
                    )

                if new_age_max is None:
                    validation_errors.append(
                        "年齢上限を選択してください。"
                    )

                if (
                    isinstance(new_age_max, int)
                    and new_age_min is not None
                    and new_age_max < new_age_min
                ):
                    validation_errors.append(
                        "年齢上限は年齢下限以上にしてください。"
                    )

            if target_change_type in [
                "性別",
                "年齢と性別",
            ]:

                if not new_gender:
                    validation_errors.append(
                        "性別を選択してください。"
                    )


        # ------------------------------------------
        # エリア変更
        # ------------------------------------------

        if area_change:

            if not area_method:
                validation_errors.append(
                    "エリアの指定方法を選択してください。"
                )

            elif area_method == "地点からの距離":

                if not distance_change_type:
                    validation_errors.append(
                        "エリアの変更項目を選択してください。"
                    )

                if distance_change_type in [
                    "地点のみ変更",
                    "地点と距離、両方変更",
                ]:

                    if not new_point_type:
                        validation_errors.append(
                            "地点種別を選択してください。"
                        )

                    if (
                        new_point_type in [
                            "駅",
                            "その他ランドマーク",
                        ]
                        and not new_point_name.strip()
                    ):
                        validation_errors.append(
                            "地点名を入力してください。"
                        )

                if distance_change_type in [
                    "距離のみ変更",
                    "地点と距離、両方変更",
                ]:

                    if new_distance is None:
                        validation_errors.append(
                            "距離を入力してください。"
                        )

            elif area_method == "市区町村":

                if not new_municipalities.strip():
                    validation_errors.append(
                        "市区町村を入力してください。"
                    )


        # ------------------------------------------
        # 予算変更
        # ------------------------------------------

        if budget_change:

            if not new_annual_budget:
                validation_errors.append(
                    "年間広告費を入力してください。"
                )

            elif not (
                new_annual_budget.isascii()
                and new_annual_budget.isdigit()
            ):
                validation_errors.append(
                    "年間広告費は半角数字・カンマなしで入力してください。"
                )

            if not budget_approved:
                validation_errors.append(
                    "予算変更の承認取得済みにチェックしてください。"
                )


        # ------------------------------------------
        # 配信期間延長
        # ------------------------------------------

        if period_change:

            if new_end_date is None:
                validation_errors.append(
                    "変更後の配信終了日を選択してください。"
                )

            if not period_extension_reason.strip():
                validation_errors.append(
                    "延長理由を入力してください。"
                )

            if not period_extension_approved:
                validation_errors.append(
                    "配信期間延長の承認取得済みにチェックしてください。"
                )


        # ------------------------------------------
        # テキストやリンク先変更など
        # ------------------------------------------

        if text_change:

            if not text_change_detail.strip():
                validation_errors.append(
                    "テキストやリンク先の変更内容を入力してください。"
                )


        # ------------------------------------------
        # クリエイティブ差し替え
        # ------------------------------------------

        if creative_change:

            if not creative_confirmed:
                validation_errors.append(
                    "クリエイティブ差し替えの顧客確認済みにチェックしてください。"
                )


    # ==================================================
    # 配信停止・再開
    # ==================================================

    elif request_category in [
        "配信停止",
        "配信再開・停止",
    ]:

        if not delivery_request:
            validation_errors.append(
                "配信について選択してください。"
            )

        if (
            status == "ACTIVE"
            and delivery_request == "その他"
            and not delivery_reason.strip()
        ):
            validation_errors.append(
                "停止理由を入力してください。"
            )

        if (
            status == "PAUSED"
            and delivery_request == "配信停止"
            and not delivery_reason.strip()
        ):
            validation_errors.append(
                "停止理由を入力してください。"
            )

    # ==================================================
    # 依頼する
    # ==================================================

    st.divider()

    if st.button(
        "依頼する",
        key="change_request_submit",
        type="primary",
        use_container_width=True,
    ):

        if validation_errors:

            for error in validation_errors:
                st.error(
                    error
                )

        else:

            # ==================================================
            # 親データ
            # ==================================================

            parent_data = {
                "申請者": applicant["申請者名"],
                "案件ID": str(
                    selected_ad.get(
                        "案件ID",
                        "",
                    ) or ""
                ).strip(),
                "施設ID": str(
                    selected_ad.get(
                        "施設ID",
                        "",
                    ) or ""
                ).strip(),
                "施設名": str(
                    selected_ad.get(
                        "施設名",
                        "",
                    ) or ""
                ).strip(),
                "訴求内容": str(
                    selected_ad.get(
                        "訴求内容",
                        "",
                    ) or ""
                ).strip(),
                "対象広告キー": ad_key,
                "データ種別": str(
                    selected_ad.get(
                        "データ種別",
                        "",
                    ) or ""
                ).strip(),

                "ad_account_id": str(
                    selected_ad.get(
                        "ad_account_id",
                        "",
                    ) or ""
                ).strip(),
                "広告アカウント名": str(
                    selected_ad.get(
                        "広告アカウント名",
                        "",
                    ) or ""
                ).strip(),
                "campaign_id": str(
                    selected_ad.get(
                        "campaign_id",
                        "",
                    ) or ""
                ).strip(),
                "adset_id": str(
                    selected_ad.get(
                        "adset_id",
                        "",
                    ) or ""
                ).strip(),
                "ad_id": str(
                    selected_ad.get(
                        "ad_id",
                        "",
                    ) or ""
                ).strip(),
            }


            # ==================================================
            # 明細データ
            # ==================================================

            detail_rows = []


            # --------------------------------------------------
            # ターゲット変更
            # --------------------------------------------------

            if target_change:

                detail_rows.append(
                    {
                        "変更種別": "ターゲット変更",
                        "変更対象": target_change_type,
                        "変更後年齢下限": (
                            new_age_min
                            if new_age_min is not None
                            else ""
                        ),
                        "変更後年齢上限": (
                            new_age_max
                            if new_age_max is not None
                            else ""
                        ),
                        "変更後性別": (
                            new_gender or ""
                        ),
                    }
                )


            # --------------------------------------------------
            # エリア変更
            # --------------------------------------------------

            if area_change:

                detail_rows.append(
                    {
                        "変更種別": "エリア変更",
                        "エリア指定方法": area_method,
                        "エリア変更対象": (
                            distance_change_type or ""
                        ),
                        "変更後地点種別": (
                            new_point_type or ""
                        ),
                        "変更後地点名": (
                            new_point_name.strip()
                        ),
                        "変更後距離km": (
                            new_distance
                            if new_distance is not None
                            else ""
                        ),
                        "変更後市区町村": (
                            new_municipalities.strip()
                        ),
                    }
                )


            # --------------------------------------------------
            # 予算変更
            # --------------------------------------------------

            if budget_change:

                detail_rows.append(
                    {
                        "変更種別": "予算変更",
                        "変更後年間広告費": int(
                            new_annual_budget
                        ),
                        "予算承認取得済み": (
                            budget_approved
                        ),
                    }
                )


            # --------------------------------------------------
            # 配信期間延長
            # --------------------------------------------------

            if period_change:

                detail_rows.append(
                    {
                        "変更種別": "配信期間延長（更新以外）",
                        "変更後配信終了日": (
                            new_end_date.strftime(
                                "%Y/%m/%d"
                            )
                        ),
                        "配信期間延長理由": (
                            period_extension_reason.strip()
                        ),
                        "配信期間延長承認取得済み": (
                            period_extension_approved
                        ),
                    }
                )


            # --------------------------------------------------
            # テキスト・リンク先等
            # --------------------------------------------------

            if text_change:

                detail_rows.append(
                    {
                        "変更種別": "テキストやリンク先変更など",
                        "テキスト・リンク先等変更内容": (
                            text_change_detail.strip()
                        ),
                    }
                )


            # --------------------------------------------------
            # クリエイティブ差し替え
            # --------------------------------------------------

            if creative_change:

                detail_rows.append(
                    {
                        "変更種別": "クリエイティブ差し替え",
                        "クリエイティブ顧客確認済み": (
                            creative_confirmed
                        ),
                    }
                )


            # --------------------------------------------------
            # 配信停止・再開
            # --------------------------------------------------

            if delivery_request:

                detail_rows.append(
                    {
                        "変更種別": "配信操作",
                        "配信操作": delivery_request,
                        "配信理由": (
                            delivery_reason.strip()
                        ),
                    }
                )


            # ==================================================
            # Google Sheetsへ登録
            # ==================================================

            try:

                request_id = register_change_request(
                    parent_data=parent_data,
                    detail_rows=detail_rows,
                )

            except Exception as exc:

                st.error(
                    "依頼の登録に失敗しました。"
                )

                st.exception(
                    exc
                )

            else:
                # 新しい変更依頼を登録したので、
                # 変更依頼データのキャッシュだけ破棄する
                load_change_requests.clear()
                load_change_request_details.clear()

                st.session_state[
                    "change_request_completed_id"
                ] = request_id

                st.rerun()