from datetime import datetime
import pandas as pd
from data_sources.master_source import (
    SHEET_NAMES,
    get_spreadsheet,
    load_change_requests,
    load_change_request_details,
)
from services.ad_search import (
    get_ad_key,
    find_ad_by_key,
)

# =========================================================
# 広告変更依頼：登録
# =========================================================

def register_change_request(
    parent_data,
    detail_rows,
):
    """
    広告変更依頼をGoogle Sheetsへ登録する。

    Parameters
    ----------
    parent_data : dict
        「広告変更依頼」へ登録する親データ。

    detail_rows : list[dict]
        「広告変更依頼明細」へ登録する明細データ。

    Returns
    -------
    str
        発行した依頼ID。
    """

    if not parent_data:
        raise ValueError(
            "親データがありません。"
        )

    if not detail_rows:
        raise ValueError(
            "依頼明細がありません。"
        )

    spreadsheet = get_spreadsheet()

    parent_sheet = spreadsheet.worksheet(
        SHEET_NAMES["change_requests"]
    )

    detail_sheet = spreadsheet.worksheet(
        SHEET_NAMES["change_request_details"]
    )


    # =====================================================
    # 依頼ID発番
    # =====================================================

    request_id = _generate_request_id(
        parent_sheet
    )


    # =====================================================
    # 親データ
    # =====================================================

    parent_headers = parent_sheet.row_values(1)

    if not parent_headers:
        raise ValueError(
            "「広告変更依頼」のヘッダーがありません。"
        )

    parent_record = dict(
        parent_data
    )

    parent_record["依頼ID"] = request_id

    parent_record.setdefault(
        "依頼日時",
        datetime.now().strftime(
            "%Y/%m/%d %H:%M:%S"
        ),
    )

    parent_record.setdefault(
        "対応状況",
        "未対応",
    )

    parent_record.setdefault(
        "対応完了日時",
        "",
    )

    parent_row = [
        parent_record.get(
            header,
            "",
        )
        for header in parent_headers
    ]


    # =====================================================
    # 明細データ
    # =====================================================

    detail_headers = detail_sheet.row_values(1)

    if not detail_headers:
        raise ValueError(
            "「広告変更依頼明細」のヘッダーがありません。"
        )

    detail_values = []

    for detail_no, detail_data in enumerate(
        detail_rows,
        start=1,
    ):

        detail_record = dict(
            detail_data
        )

        detail_record["依頼ID"] = request_id
        detail_record["明細No"] = detail_no

        detail_values.append(
            [
                detail_record.get(
                    header,
                    "",
                )
                for header in detail_headers
            ]
        )


    # =====================================================
    # Google Sheetsへ登録
    # =====================================================

    parent_append_result = parent_sheet.append_row(
        parent_row,
        value_input_option="USER_ENTERED",
    )

    updated_range = (
        parent_append_result
        .get("updates", {})
        .get("updatedRange", "")
    )

    if not updated_range:
        raise RuntimeError(
            "登録した親行の位置を取得できませんでした。"
        )

    parent_row_number = int(
        updated_range
        .split("!")[1]
        .split(":")[0]
        .lstrip("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    )

    try:

        detail_sheet.append_rows(
            detail_values,
            value_input_option="USER_ENTERED",
        )

    except Exception:

        # 明細登録に失敗した場合、
        # 親だけ残さないように、
        # 今回追加した親行だけを削除する。
        parent_sheet.delete_rows(
            parent_row_number
        )

        raise


    return request_id

# =========================================================
# 依頼ID発番
# =========================================================

def _generate_request_id(
    parent_sheet,
):
    """
    依頼IDを発行する。

    形式:
        CR-YYYYMMDD-HHMMSSffffff

    例:
        CR-20260930-150612123456
    """

    return datetime.now().strftime(
        "CR-%Y%m%d-%H%M%S%f"
    )


# =========================================================
# 広告変更依頼：申請内容詳細
# =========================================================

def _build_request_detail_summary(
    detail_group,
):
    """
    1件の広告変更依頼に紐づく明細から、
    一覧表示用の「申請内容詳細」を作る。

    この段階では明細に保存されている
    変更後の内容・操作内容を表示する。
    """

    details = []

    for _, row in detail_group.iterrows():

        change_type = str(
            row.get("変更種別", "") or ""
        ).strip()

        # -------------------------------------------------
        # ターゲット変更
        # -------------------------------------------------

        if change_type == "ターゲット変更":

            target_details = []

            age_min = str(
                row.get(
                    "変更後年齢下限",
                    "",
                ) or ""
            ).strip()

            age_max = str(
                row.get(
                    "変更後年齢上限",
                    "",
                ) or ""
            ).strip()

            gender = str(
                row.get(
                    "変更後性別",
                    "",
                ) or ""
            ).strip()

            if age_min or age_max:

                if age_min and age_max:
                    age_text = (
                        f"年齢：{age_min}～{age_max}"
                    )

                elif age_min:
                    age_text = (
                        f"年齢：{age_min}以上"
                    )

                else:
                    age_text = (
                        f"年齢：{age_max}以下"
                    )

                target_details.append(
                    age_text
                )

            if gender:
                target_details.append(
                    f"性別：{gender}"
                )

            if target_details:
                details.append(
                    "／".join(
                        target_details
                    )
                )

        # -------------------------------------------------
        # エリア変更
        # -------------------------------------------------

        elif change_type == "エリア変更":

            area_method = str(
                row.get(
                    "エリア指定方法",
                    "",
                ) or ""
            ).strip()

            area_target = str(
                row.get(
                    "エリア変更対象",
                    "",
                ) or ""
            ).strip()

            point_type = str(
                row.get(
                    "変更後地点種別",
                    "",
                ) or ""
            ).strip()

            point_name = str(
                row.get(
                    "変更後地点名",
                    "",
                ) or ""
            ).strip()

            radius = str(
                row.get(
                    "変更後距離km",
                    "",
                ) or ""
            ).strip()

            municipalities = str(
                row.get(
                    "変更後市区町村",
                    "",
                ) or ""
            ).strip()

            area_parts = []

            if area_target:
                area_parts.append(
                    f"変更対象：{area_target}"
                )

            if area_method:
                area_parts.append(
                    f"指定方法：{area_method}"
                )

            if point_type:
                area_parts.append(
                    f"地点種別：{point_type}"
                )

            if point_name:
                area_parts.append(
                    f"地点：{point_name}"
                )

            if radius:
                area_parts.append(
                    f"距離：{radius}km"
                )

            if municipalities:
                area_parts.append(
                    f"市区町村：{municipalities}"
                )

            if area_parts:
                details.append(
                    "／".join(
                        area_parts
                    )
                )

        # -------------------------------------------------
        # 予算変更
        # -------------------------------------------------

        elif change_type == "予算変更":

            annual_budget = str(
                row.get(
                    "変更後年間広告費",
                    "",
                ) or ""
            ).strip()

            if annual_budget:
                details.append(
                    f"年間広告費：{annual_budget}"
                )

        # -------------------------------------------------
        # 配信期間延長
        # -------------------------------------------------

        elif change_type == "配信期間延長":

            end_date = str(
                row.get(
                    "変更後配信終了日",
                    "",
                ) or ""
            ).strip()

            reason = str(
                row.get(
                    "配信期間延長理由",
                    "",
                ) or ""
            ).strip()

            period_parts = []

            if end_date:
                period_parts.append(
                    f"配信終了日：{end_date}"
                )

            if reason:
                period_parts.append(
                    f"理由：{reason}"
                )

            if period_parts:
                details.append(
                    "／".join(
                        period_parts
                    )
                )

        # -------------------------------------------------
        # テキスト・リンク先等変更
        # -------------------------------------------------

        elif change_type == "テキスト・リンク先等変更":

            content = str(
                row.get(
                    "テキスト・リンク先等変更内容",
                    "",
                ) or ""
            ).strip()

            if content:
                details.append(
                    content
                )

        # -------------------------------------------------
        # クリエイティブ差し替え
        # -------------------------------------------------

        elif change_type == "クリエイティブ差し替え":

            confirmed = str(
                row.get(
                    "クリエイティブ顧客確認済み",
                    "",
                ) or ""
            ).strip()

            if confirmed:
                details.append(
                    "クリエイティブ差し替え"
                    f"（顧客確認：{confirmed}）"
                )

            else:
                details.append(
                    "クリエイティブ差し替え"
                )

        # -------------------------------------------------
        # 配信操作
        # -------------------------------------------------

        elif change_type == "配信操作":

            operation = str(
                row.get(
                    "配信操作",
                    "",
                ) or ""
            ).strip()

            reason = str(
                row.get(
                    "配信理由",
                    "",
                ) or ""
            ).strip()

            delivery_parts = []

            if operation:
                delivery_parts.append(
                    operation
                )

            if reason:
                delivery_parts.append(
                    f"理由：{reason}"
                )

            if delivery_parts:
                details.append(
                    "／".join(
                        delivery_parts
                    )
                )

    return " ｜ ".join(details)

# =========================================================
# 広告変更依頼：未完了一覧取得
# =========================================================

def get_pending_change_requests(
    ad_data=None,
):
    """
    変更・停止依頼を一覧表示用に取得する。

    表示対象：
    ・未対応の依頼
    ・完了後1か月以内の依頼

    1依頼 = 1行。
    複数の明細がある場合は、
    変更種別をまとめて「依頼内容」として表示する。

    新しい依頼から順に表示する。
    """

    parent_df = load_change_requests()
    detail_df = load_change_request_details()

    # -----------------------------------------------------
    # 親データがない場合
    # -----------------------------------------------------

    if parent_df.empty:
        return parent_df.copy()

    # -----------------------------------------------------
    # 日時を変換
    # -----------------------------------------------------

    parent_df = parent_df.copy()

    parent_df["_依頼日時"] = pd.to_datetime(
        parent_df["依頼日時"],
        errors="coerce",
    )

    parent_df["_対応完了日時"] = pd.to_datetime(
        parent_df["対応完了日時"],
        errors="coerce",
    )

    # -----------------------------------------------------
    # 表示対象
    #
    # ・未対応 → すべて表示
    # ・完了   → 完了後1か月以内だけ表示
    # -----------------------------------------------------

    now = pd.Timestamp.now()

    one_month_ago = (
        now - pd.DateOffset(months=1)
    )

    status = (
        parent_df["対応状況"]
        .astype(str)
        .str.strip()
    )

    is_incomplete = (
        status != "完了"
    )

    is_recently_completed = (
        (status == "完了")
        & parent_df["_対応完了日時"].notna()
        & (
            parent_df["_対応完了日時"]
            >= one_month_ago
        )
    )

    pending_df = parent_df[
        is_incomplete
        | is_recently_completed
    ].copy()

    if pending_df.empty:
        return pending_df.drop(
            columns=[
                "_依頼日時",
                "_対応完了日時",
            ],
            errors="ignore",
        ).reset_index(drop=True)

    # -----------------------------------------------------
    # 明細から依頼内容を作る
    # -----------------------------------------------------

    request_summaries = {}

    if not detail_df.empty:

        for request_id, group in detail_df.groupby(
            "依頼ID",
            sort=False,
        ):

            change_types = []

            for change_type in group["変更種別"]:

                change_type = str(
                    change_type
                ).strip()

                if (
                    change_type
                    and
                    change_type not in change_types
                ):
                    change_types.append(
                        change_type
                    )

            request_summaries[
                str(request_id).strip()
            ] = "・".join(
                change_types
            )

    # -----------------------------------------------------
    # 親データへ依頼内容を追加
    # -----------------------------------------------------

    pending_df["依頼内容"] = (
        pending_df["依頼ID"]
        .astype(str)
        .str.strip()
        .map(request_summaries)
        .fillna("")
    )

    # -----------------------------------------------------
    # 親データへ申請内容詳細を追加
    # -----------------------------------------------------

    request_detail_summaries = {}

    if not detail_df.empty:

        for request_id, group in detail_df.groupby(
            "依頼ID",
            sort=False,
        ):

            request_detail_summaries[
                str(request_id).strip()
            ] = _build_request_detail_summary(
                group
            )

    pending_df["申請内容詳細"] = (
        pending_df["依頼ID"]
        .astype(str)
        .str.strip()
        .map(request_detail_summaries)
        .fillna("")
    )

    # -----------------------------------------------------
    # 「期間終了をもって更新せず」の場合
    # 対象広告の掲載終了日を申請内容詳細へ追加
    # -----------------------------------------------------

    if ad_data is not None and not ad_data.empty:

        for index, row in pending_df.iterrows():

            detail_text = str(
                row.get(
                    "申請内容詳細",
                    "",
                ) or ""
            ).strip()

            if (
                "期間終了をもって更新せず"
                not in detail_text
            ):
                continue

            ad_key = str(
                row.get(
                    "対象広告キー",
                    "",
                ) or ""
            ).strip()

            ad_row = find_ad_by_key(
                ad_data,
                ad_key,
            )

            if ad_row is None:
                continue

            end_date = str(
                ad_row.get(
                    "配信終了",
                    "",
                ) or ""
            ).strip()

            if not end_date:
                continue

            pending_df.at[
                index,
                "申請内容詳細",
            ] = (
                f"{detail_text}"
                f"／掲載終了日：{end_date}"
            )

    # -----------------------------------------------------
    # 新しい依頼から順に表示
    # -----------------------------------------------------

    pending_df = pending_df.sort_values(
        "_依頼日時",
        ascending=False,
        kind="stable",
    )

    # -----------------------------------------------------
    # 一覧用の一時列を削除
    # -----------------------------------------------------

    pending_df = pending_df.drop(
        columns=[
            "_依頼日時",
            "_対応完了日時",
        ],
        errors="ignore",
    )

    return pending_df.reset_index(
        drop=True
    )

# =========================================================
# 広告変更依頼：完了済み変更履歴
# =========================================================

def get_completed_change_requests(
    parent_df=None,
    detail_df=None,
):
    """
    対応状況が「完了」の変更依頼と、
    その明細を取得する。

    渡された変更依頼データを優先して使用する。
    データが渡されていない場合だけ
    Google Sheetsから取得する。
    """

    if parent_df is None:
        parent_df = load_change_requests()

    if detail_df is None:
        detail_df = load_change_request_details()

    if parent_df.empty:
        return (
            parent_df.copy(),
            detail_df.iloc[0:0].copy(),
        )

    completed_parent_df = parent_df[
        parent_df["対応状況"]
        .astype(str)
        .str.strip()
        == "完了"
    ].copy()

    if completed_parent_df.empty:
        return (
            completed_parent_df.reset_index(
                drop=True
            ),
            detail_df.iloc[0:0].copy(),
        )

    completed_parent_df["_対応完了日時"] = (
        pd.to_datetime(
            completed_parent_df[
                "対応完了日時"
            ],
            errors="coerce",
        )
    )

    completed_parent_df = (
        completed_parent_df
        .sort_values(
            [
                "_対応完了日時",
                "依頼日時",
            ],
            ascending=True,
            kind="stable",
        )
        .drop(
            columns=[
                "_対応完了日時",
            ],
            errors="ignore",
        )
        .reset_index(
            drop=True
        )
    )

    completed_request_ids = set(
        completed_parent_df[
            "依頼ID"
        ]
        .astype(str)
        .str.strip()
    )

    completed_detail_df = detail_df[
        detail_df["依頼ID"]
        .astype(str)
        .str.strip()
        .isin(
            completed_request_ids
        )
    ].copy()

    return (
        completed_parent_df,
        completed_detail_df.reset_index(
            drop=True
        ),
    )

# =========================================================
# 広告変更依頼：完了済み変更を広告へ適用
# =========================================================

def apply_completed_changes_to_ad_data(
    ad_data,
    parent_df=None,
    detail_df=None,
):
    """
    元の広告データへ完了済み変更履歴を古い順に適用し、
    現在設定を持つ広告データを返す。

    元のad_data自体は変更しない。
    """

    if ad_data is None:
        return ad_data

    if ad_data.empty:
        return ad_data.copy()

    current_ad_data = ad_data.copy()

    (
        completed_parent_df,
        completed_detail_df,
    ) = get_completed_change_requests(
        parent_df=parent_df,
        detail_df=detail_df,
    )

    if (
        completed_parent_df.empty
        or completed_detail_df.empty
    ):
        return current_ad_data


    # =====================================================
    # 完了した依頼を古い順に適用
    # =====================================================

    for _, request_row in (
        completed_parent_df.iterrows()
    ):

        request_id = str(
            request_row.get(
                "依頼ID",
                "",
            ) or ""
        ).strip()

        ad_key = str(
            request_row.get(
                "対象広告キー",
                "",
            ) or ""
        ).strip()

        if (
            not request_id
            or not ad_key
        ):
            continue


        # -------------------------------------------------
        # 対象広告を特定
        # -------------------------------------------------

        matched_indexes = (
            current_ad_data[
                current_ad_data.apply(
                    lambda row:
                    get_ad_key(
                        row
                    )
                    == ad_key,
                    axis=1,
                )
            ].index
        )

        if len(matched_indexes) == 0:
            continue

        ad_index = matched_indexes[0]


        # -------------------------------------------------
        # この依頼の明細
        # -------------------------------------------------

        request_details = (
            completed_detail_df[
                completed_detail_df[
                    "依頼ID"
                ]
                .astype(str)
                .str.strip()
                == request_id
            ]
            .copy()
        )

        if request_details.empty:
            continue

        if "明細No" in request_details.columns:
            request_details["_明細No"] = (
                pd.to_numeric(
                    request_details[
                        "明細No"
                    ],
                    errors="coerce",
                )
            )

            request_details = (
                request_details
                .sort_values(
                    "_明細No",
                    ascending=True,
                    kind="stable",
                )
                .drop(
                    columns=[
                        "_明細No",
                    ],
                    errors="ignore",
                )
            )


        # -------------------------------------------------
        # 明細を順番に適用
        # -------------------------------------------------

        for _, detail_row in (
            request_details.iterrows()
        ):

            _apply_completed_detail_to_ad(
                current_ad_data,
                ad_index,
                detail_row,
            )


    return current_ad_data




# =========================================================
# 現在設定用：明細1件を広告へ適用
# =========================================================

def _apply_completed_detail_to_ad(
    ad_data,
    ad_index,
    detail_row,
):

    change_type = str(
        detail_row.get(
            "変更種別",
            "",
        ) or ""
    ).strip()


    # =====================================================
    # ターゲット変更
    # =====================================================

    if change_type == "ターゲット変更":

        age_min = str(
            detail_row.get(
                "変更後年齢下限",
                "",
            ) or ""
        ).strip()

        age_max = str(
            detail_row.get(
                "変更後年齢上限",
                "",
            ) or ""
        ).strip()

        gender = str(
            detail_row.get(
                "変更後性別",
                "",
            ) or ""
        ).strip()

        if age_min or age_max:

            if age_min and age_max:
                age = (
                    f"{age_min}～{age_max}"
                )

            elif age_min:
                age = (
                    f"{age_min}以上"
                )

            else:
                age = (
                    f"{age_max}以下"
                )

            ad_data.at[
                ad_index,
                "年齢",
            ] = age

        if gender:
            ad_data.at[
                ad_index,
                "性別",
            ] = gender

        return


    # =====================================================
    # エリア変更
    # =====================================================

    if change_type == "エリア変更":

        area_method = str(
            detail_row.get(
                "エリア指定方法",
                "",
            ) or ""
        ).strip()

        point_type = str(
            detail_row.get(
                "変更後地点種別",
                "",
            ) or ""
        ).strip()

        point_name = str(
            detail_row.get(
                "変更後地点名",
                "",
            ) or ""
        ).strip()

        radius = str(
            detail_row.get(
                "変更後距離km",
                "",
            ) or ""
        ).strip()

        municipalities = str(
            detail_row.get(
                "変更後市区町村",
                "",
            ) or ""
        ).strip()

        if area_method == "距離":

            area_parts = []

            if point_name:
                area_parts.append(
                    point_name
                )

            elif point_type:
                area_parts.append(
                    point_type
                )

            if radius:
                area_parts.append(
                    f"{radius}km"
                )

            if area_parts:
                ad_data.at[
                    ad_index,
                    "エリア",
                ] = "から".join(
                    area_parts
                )

        elif (
            area_method == "市区町村"
            and municipalities
        ):
            ad_data.at[
                ad_index,
                "エリア",
            ] = municipalities

        return


    # =====================================================
    # 予算変更
    # =====================================================

    if change_type == "予算変更":

        annual_budget = str(
            detail_row.get(
                "変更後年間広告費",
                "",
            ) or ""
        ).strip()

        if annual_budget:
            ad_data.at[
                ad_index,
                "年間広告費",
            ] = annual_budget

        return


    # =====================================================
    # 配信期間延長
    # =====================================================

    if change_type == "配信期間延長":

        end_date = str(
            detail_row.get(
                "変更後配信終了日",
                "",
            ) or ""
        ).strip()

        if end_date:
            ad_data.at[
                ad_index,
                "配信終了",
            ] = end_date

        return


    # =====================================================
    # 配信操作
    # =====================================================

    if change_type == "配信操作":

        operation = str(
            detail_row.get(
                "配信操作",
                "",
            ) or ""
        ).strip()

        if operation == "配信再開":
            ad_data.at[
                ad_index,
                "状態",
            ] = "ACTIVE"

        elif operation in {
            "クリエイティブ変更・顧客対応のため一時停止",
            "配信停止",
        }:
            ad_data.at[
                ad_index,
                "状態",
            ] = "PAUSED"

        elif operation in {
            "期間終了をもって更新せず",
            "強制解約",
            "その他",
        }:
            ad_data.at[
                ad_index,
                "状態",
            ] = "ENDED"

        return

# =========================================================
# 広告変更依頼：変更前 → 変更後 履歴再生
# =========================================================
# =========================================================
# 広告変更依頼：変更前 → 変更後 表示
# =========================================================

def _build_before_after_detail_summary(
    before_ad,
    after_ad,
    detail_group,
):
    """
    変更適用前・適用後の広告設定から、
    履歴表示用の「変更前 → 変更後」を作る。
    """

    details = []

    change_types = (
        detail_group["変更種別"]
        .astype(str)
        .str.strip()
        .tolist()
    )


    # =====================================================
    # ターゲット変更
    # =====================================================

    if "ターゲット変更" in change_types:

        before_age = str(
            before_ad.get(
                "年齢",
                "",
            ) or ""
        ).strip()

        after_age = str(
            after_ad.get(
                "年齢",
                "",
            ) or ""
        ).strip()

        if (
            before_age
            or after_age
        ) and before_age != after_age:

            details.append(
                f"年齢：{before_age or '―'}"
                f" → {after_age or '―'}"
            )


        before_gender = str(
            before_ad.get(
                "性別",
                "",
            ) or ""
        ).strip()

        after_gender = str(
            after_ad.get(
                "性別",
                "",
            ) or ""
        ).strip()

        if (
            before_gender
            or after_gender
        ) and before_gender != after_gender:

            details.append(
                f"性別：{before_gender or '―'}"
                f" → {after_gender or '―'}"
            )


    # =====================================================
    # エリア変更
    # =====================================================

    if "エリア変更" in change_types:

        before_area = str(
            before_ad.get(
                "エリア",
                "",
            ) or ""
        ).strip()

        after_area = str(
            after_ad.get(
                "エリア",
                "",
            ) or ""
        ).strip()

        if (
            before_area
            or after_area
        ) and before_area != after_area:

            details.append(
                f"エリア：{before_area or '―'}"
                f" → {after_area or '―'}"
            )


    # =====================================================
    # 予算変更
    # =====================================================

    if "予算変更" in change_types:

        before_budget = str(
            before_ad.get(
                "年間広告費",
                "",
            ) or ""
        ).strip()

        after_budget = str(
            after_ad.get(
                "年間広告費",
                "",
            ) or ""
        ).strip()

        if (
            before_budget
            or after_budget
        ) and before_budget != after_budget:

            details.append(
                f"年間広告費：{before_budget or '―'}"
                f" → {after_budget or '―'}"
            )


    # =====================================================
    # 配信期間延長
    # =====================================================

    if "配信期間延長" in change_types:

        before_end = str(
            before_ad.get(
                "配信終了",
                "",
            ) or ""
        ).strip()

        after_end = str(
            after_ad.get(
                "配信終了",
                "",
            ) or ""
        ).strip()

        if (
            before_end
            or after_end
        ) and before_end != after_end:

            details.append(
                f"配信終了日：{before_end or '―'}"
                f" → {after_end or '―'}"
            )


    # =====================================================
    # 配信操作
    # =====================================================

    if "配信操作" in change_types:

        before_status = str(
            before_ad.get(
                "状態",
                "",
            ) or ""
        ).strip()

        after_status = str(
            after_ad.get(
                "状態",
                "",
            ) or ""
        ).strip()

        operation = ""
        reason = ""

        delivery_rows = detail_group[
            detail_group[
                "変更種別"
            ]
            .astype(str)
            .str.strip()
            == "配信操作"
        ]

        if not delivery_rows.empty:

            reason = str(
                delivery_rows.iloc[0].get(
                    "配信理由",
                    "",
                ) or ""
            ).strip()

        if (
            before_status
            or after_status
        ) and before_status != after_status:

            status_text = (
                f"配信状態：{before_status or '―'}"
                f" → {after_status or '―'}"
            )

            if operation:
                status_text += (
                    f"／配信操作：{operation}"
                )

            if reason:
                status_text += (
                    f"／理由：{reason}"
                )

            details.append(
                status_text
            )

        elif operation:

            operation_text = (
                f"配信操作：{operation}"
            )

            if reason:
                operation_text += (
                    f"／理由：{reason}"
                )

            details.append(
                operation_text
            )


    # =====================================================
    # 現在値を持たない変更
    # =====================================================

    for _, row in detail_group.iterrows():

        change_type = str(
            row.get(
                "変更種別",
                "",
            ) or ""
        ).strip()

        if change_type in {
            "テキスト・リンク先等変更",
            "クリエイティブ差し替え",
        }:

            single_detail = pd.DataFrame(
                [row.to_dict()]
            )

            summary = (
                _build_request_detail_summary(
                    single_detail
                )
            )

            if summary:
                details.append(
                    summary
                )


    return "／".join(details)

def build_ad_change_history_with_before_after(
    base_ad,
    ad_key,
):
    """
    広告の初期設定を起点に変更依頼を時系列で再生し、
    各依頼の「変更前 → 変更後」を作る。

    完了済み依頼だけが次の現在設定へ反映される。
    未対応依頼は申請内容を表示するだけで、
    次の履歴の変更前には反映しない。
    """

    if base_ad is None or not ad_key:
        return pd.DataFrame()

    parent_df = load_change_requests()
    detail_df = load_change_request_details()

    if parent_df.empty:
        return parent_df.copy()


    # =====================================================
    # 対象広告の依頼だけ取得
    # =====================================================

    history_df = parent_df[
        parent_df[
            "対象広告キー"
        ]
        .astype(str)
        .str.strip()
        == str(ad_key).strip()
    ].copy()

    if history_df.empty:
        return history_df.reset_index(
            drop=True
        )


    # =====================================================
    # 古い申請から順に並べる
    # =====================================================

    history_df[
        "_依頼日時"
    ] = pd.to_datetime(
        history_df[
            "依頼日時"
        ],
        errors="coerce",
    )

    history_df = (
        history_df
        .sort_values(
            "_依頼日時",
            ascending=True,
            kind="stable",
        )
        .reset_index(
            drop=True
        )
    )


    # =====================================================
    # 初期設定を1行DataFrameにする
    #
    # _apply_completed_detail_to_ad() を
    # そのまま再利用するため。
    # =====================================================

    current_ad = pd.DataFrame(
        [base_ad.to_dict()]
    )

    ad_index = current_ad.index[0]

    request_summaries = {}
    detail_summaries = {}


    # =====================================================
    # 依頼を古い順に再生
    # =====================================================

    for _, request_row in history_df.iterrows():

        request_id = str(
            request_row.get(
                "依頼ID",
                "",
            ) or ""
        ).strip()

        status = str(
            request_row.get(
                "対応状況",
                "",
            ) or ""
        ).strip()

        request_details = detail_df[
            detail_df[
                "依頼ID"
            ]
            .astype(str)
            .str.strip()
            == request_id
        ].copy()

        if request_details.empty:
            request_summaries[
                request_id
            ] = ""

            detail_summaries[
                request_id
            ] = ""

            continue


        # -------------------------------------------------
        # 明細No順
        # -------------------------------------------------

        if "明細No" in request_details.columns:

            request_details[
                "_明細No"
            ] = pd.to_numeric(
                request_details[
                    "明細No"
                ],
                errors="coerce",
            )

            request_details = (
                request_details
                .sort_values(
                    "_明細No",
                    ascending=True,
                    kind="stable",
                )
                .drop(
                    columns=[
                        "_明細No",
                    ],
                    errors="ignore",
                )
            )


        # -------------------------------------------------
        # 依頼内容
        # -------------------------------------------------

        change_types = []

        for change_type in (
            request_details[
                "変更種別"
            ]
        ):

            change_type = str(
                change_type
            ).strip()

            if (
                change_type
                and change_type
                not in change_types
            ):
                change_types.append(
                    change_type
                )

        request_summaries[
            request_id
        ] = "・".join(
            change_types
        )


        # -------------------------------------------------
        # この申請を仮に反映した広告を作る
        #
        # 未対応でも「申請した変更後」は
        # 表示したいので一度適用する。
        # -------------------------------------------------

        requested_ad = current_ad.copy()

        requested_index = (
            requested_ad.index[0]
        )

        for _, detail_row in (
            request_details.iterrows()
        ):

            _apply_completed_detail_to_ad(
                requested_ad,
                requested_index,
                detail_row,
            )


        # -------------------------------------------------
        # 変更前 → 変更後 の表示を作る
        # -------------------------------------------------

        detail_summaries[
            request_id
        ] = (
            _build_before_after_detail_summary(
                current_ad.loc[
                    ad_index
                ],
                requested_ad.loc[
                    requested_index
                ],
                request_details,
            )
        )


        # -------------------------------------------------
        # 完了済みだけ現在設定を更新
        # -------------------------------------------------

        if status == "完了":
            current_ad = requested_ad
            ad_index = current_ad.index[0]


    # =====================================================
    # 履歴表示列へ反映
    # =====================================================

    request_ids = (
        history_df[
            "依頼ID"
        ]
        .astype(str)
        .str.strip()
    )

    history_df[
        "依頼内容"
    ] = (
        request_ids
        .map(
            request_summaries
        )
        .fillna("")
    )

    history_df[
        "申請内容詳細"
    ] = (
        request_ids
        .map(
            detail_summaries
        )
        .fillna("")
    )


    # =====================================================
    # 画面表示は新しい順
    # =====================================================

    history_df = (
        history_df
        .sort_values(
            "_依頼日時",
            ascending=False,
            kind="stable",
        )
        .drop(
            columns=[
                "_依頼日時",
            ],
            errors="ignore",
        )
        .reset_index(
            drop=True
        )
    )

    return history_df

# =========================================================
# 広告変更依頼：広告別変更履歴
# =========================================================

def get_ad_change_history(
    ad_key,
):
    """
    指定した広告の変更・停止依頼履歴を
    新しい順ですべて取得する。

    未対応・完了を問わず、
    期間制限なしで履歴を保持する。
    """

    if not ad_key:
        return pd.DataFrame()

    parent_df = load_change_requests()
    detail_df = load_change_request_details()

    if parent_df.empty:
        return parent_df.copy()


    # =====================================================
    # 対象広告だけに絞る
    # =====================================================

    history_df = parent_df[
        parent_df[
            "対象広告キー"
        ]
        .astype(str)
        .str.strip()
        == str(ad_key).strip()
    ].copy()

    if history_df.empty:
        return history_df.reset_index(
            drop=True
        )


    # =====================================================
    # 明細から依頼内容・申請内容詳細を作る
    # =====================================================

    request_summaries = {}
    detail_summaries = {}

    if not detail_df.empty:

        target_request_ids = set(
            history_df[
                "依頼ID"
            ]
            .astype(str)
            .str.strip()
        )

        target_details = detail_df[
            detail_df[
                "依頼ID"
            ]
            .astype(str)
            .str.strip()
            .isin(
                target_request_ids
            )
        ].copy()

        for request_id, group in (
            target_details.groupby(
                "依頼ID",
                sort=False,
            )
        ):

            request_id = str(
                request_id
            ).strip()

            change_types = []

            for change_type in (
                group["変更種別"]
            ):

                change_type = str(
                    change_type
                ).strip()

                if (
                    change_type
                    and change_type
                    not in change_types
                ):
                    change_types.append(
                        change_type
                    )

            request_summaries[
                request_id
            ] = "・".join(
                change_types
            )

            detail_summaries[
                request_id
            ] = (
                _build_request_detail_summary(
                    group
                )
            )


    # =====================================================
    # 履歴表示用の列を追加
    # =====================================================

    request_ids = (
        history_df[
            "依頼ID"
        ]
        .astype(str)
        .str.strip()
    )

    history_df[
        "依頼内容"
    ] = (
        request_ids
        .map(
            request_summaries
        )
        .fillna("")
    )

    history_df[
        "申請内容詳細"
    ] = (
        request_ids
        .map(
            detail_summaries
        )
        .fillna("")
    )


    # =====================================================
    # 新しい申請から順に並べる
    # =====================================================

    history_df[
        "_依頼日時"
    ] = pd.to_datetime(
        history_df[
            "依頼日時"
        ],
        errors="coerce",
    )

    history_df = (
        history_df
        .sort_values(
            "_依頼日時",
            ascending=False,
            kind="stable",
        )
        .drop(
            columns=[
                "_依頼日時",
            ],
            errors="ignore",
        )
        .reset_index(
            drop=True
        )
    )

    return history_df