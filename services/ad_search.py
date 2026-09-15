import pandas as pd

from data_sources.master_source import load_all_master_data


# =========================================================
# 共通処理
# =========================================================

def _clean_text(value):
    """
    検索・表示用の文字列を整える。
    """
    if pd.isna(value):
        return ""

    return str(value).strip()


def _prepare_dataframe(df):
    """
    DataFrame内の空値を空文字に統一する。
    """
    if df.empty:
        return df.copy()

    result = df.copy()
    result = result.fillna("")

    return result


def _unique_sorted_values(df, column):
    """
    指定列から空欄を除いた重複なしの候補一覧を返す。
    """
    if df.empty or column not in df.columns:
        return []

    values = {
        _clean_text(value)
        for value in df[column].tolist()
        if _clean_text(value)
    }

    return sorted(values)

def _build_customer_directory(ad_data):
    """
    Meta顧客ID単位で法人を1つにまとめ、
    配下施設を含む表示名を作る。

    例
    医療法人社団 樹伸会
      ├ 大宮いしはた歯科
      └ 久喜総合歯科

    ↓

    医療法人社団 樹伸会
    （大宮いしはた歯科 / 久喜総合歯科）
    """

    if ad_data.empty:
        return pd.DataFrame(
            columns=[
                "Meta顧客ID",
                "案件名",
                "顧客表示名",
            ]
        )

    if (
        "Meta顧客ID" not in ad_data.columns
        or "案件名" not in ad_data.columns
    ):
        return pd.DataFrame(
            columns=[
                "Meta顧客ID",
                "案件名",
                "顧客表示名",
            ]
        )

    rows = []

    for customer_id, group in ad_data.groupby(
        "Meta顧客ID",
        sort=False,
    ):
        customer_id = _clean_text(customer_id)

        if not customer_id:
            continue

        customer_name = ""

        for value in group["案件名"].tolist():
            cleaned = _clean_text(value)

            if cleaned:
                customer_name = cleaned
                break

        if not customer_name:
            continue

        facility_names = []

        if "施設名" in group.columns:
            for value in group["施設名"].tolist():
                facility_name = _clean_text(value)

                if not facility_name:
                    continue

                # 法人名＝施設名なら二重表示しない
                if facility_name == customer_name:
                    continue

                if facility_name not in facility_names:
                    facility_names.append(
                        facility_name
                    )

        if facility_names:
            display_name = (
                customer_name
                + "（"
                + " / ".join(facility_names)
                + "）"
            )
        else:
            display_name = customer_name

        rows.append(
            {
                "Meta顧客ID": customer_id,
                "案件名": customer_name,
                "顧客表示名": display_name,
            }
        )

    return pd.DataFrame(rows)

# =========================================================
# 広告検索用データ作成
# =========================================================

def build_ad_search_data(master_data=None):
    """
    新広告とレガシー広告をまとめて、
    広告検索で使用する1つのDataFrameを作る。

    新広告
    -------
    Meta配信履歴
        ↓ 案件ID
    案件マスタ
        ↓ Meta顧客ID
    Meta顧客マスタ
        ↓ 施設ID
    施設マスタ

    レガシー広告
    ---------------
    レガシー広告一覧
        ↓ 案件ID
    案件マスタ
        ↓ Meta顧客ID
    Meta顧客マスタ
        ↓ 施設ID
    施設マスタ
    """

    if master_data is None:
        master_data = load_all_master_data()

    customers = _prepare_dataframe(
        master_data["customers"]
    )

    facilities = _prepare_dataframe(
        master_data["facilities"]
    )

    cases = _prepare_dataframe(
        master_data["cases"]
    )

    meta_history = _prepare_dataframe(
        master_data["meta_history"]
    )

    legacy_ads = _prepare_dataframe(
        master_data.get("legacy_ads", pd.DataFrame())
    )


    # =====================================================
    # 共通：案件マスタ
    # =====================================================

    case_columns = [
        "案件ID",
        "営業担当",
        "アポ担当",
        "商材",
        "契約期間",
        "保守月額",
        "月間広告費",
        "年間広告費",
        "訴求内容",
    ]

    available_case_columns = [
        column
        for column in case_columns
        if column in cases.columns
    ]


    # =====================================================
    # 共通：Meta顧客マスタ
    # =====================================================

    customer_columns = [
        "Meta顧客ID",
        "案件名",
        "業種",
    ]

    available_customer_columns = [
        column
        for column in customer_columns
        if column in customers.columns
    ]


    # =====================================================
    # 共通：施設マスタ
    # =====================================================

    facility_columns = [
        "施設ID",
        "施設名",
        "都道府県",
        "住所",
        "電話番号",
    ]

    available_facility_columns = [
        column
        for column in facility_columns
        if column in facilities.columns
    ]


    # =====================================================
    # 新広告
    # =====================================================

    new_result = pd.DataFrame()

    if not meta_history.empty:

        new_result = meta_history.merge(
            cases[available_case_columns],
            on="案件ID",
            how="left",
            validate="many_to_one",
        )

        new_result = new_result.merge(
            customers[available_customer_columns],
            on="Meta顧客ID",
            how="left",
            validate="many_to_one",
        )

        new_result = new_result.merge(
            facilities[available_facility_columns],
            on="施設ID",
            how="left",
            validate="many_to_one",
        )

        # データ種別
        new_result["データ種別"] = "API"

        # レガシー専用列
        new_result["キャンペーン名"] = ""


    # =====================================================
    # レガシー広告
    # =====================================================

    legacy_result = pd.DataFrame()

    if not legacy_ads.empty:

        legacy_result = legacy_ads.copy()

        # レガシー広告一覧のW/X/Y
        # Meta顧客ID / 施設ID / 案件ID を利用
        required_ids = [
            "Meta顧客ID",
            "施設ID",
            "案件ID",
        ]

        for column in required_ids:
            if column not in legacy_result.columns:
                legacy_result[column] = ""

        # 発番済みのみ検索対象
        legacy_result = legacy_result[
            legacy_result["案件ID"].map(_clean_text) != ""
        ].copy()

        if not legacy_result.empty:

            # レガシーシート側にも同名列があるため、
            # マスタ側を正として重複列を先に除外
            columns_to_remove = [
                "営業担当",
                "アポ担当",
                "商材",
                "契約期間",
                "保守月額",
                "月間広告費",
                "年間広告費",
                "訴求内容",
                "案件名",
                "業種",
                "施設名",
                "都道府県",
                "住所",
                "電話番号",
            ]

            legacy_result = legacy_result.drop(
                columns=[
                    column
                    for column in columns_to_remove
                    if column in legacy_result.columns
                ],
                errors="ignore",
            )

            legacy_result = legacy_result.merge(
                cases[available_case_columns],
                on="案件ID",
                how="left",
                validate="many_to_one",
            )

            legacy_result = legacy_result.merge(
                customers[available_customer_columns],
                on="Meta顧客ID",
                how="left",
                validate="many_to_one",
            )

            legacy_result = legacy_result.merge(
                facilities[available_facility_columns],
                on="施設ID",
                how="left",
                validate="many_to_one",
            )

            # 新広告と同じ列名へ合わせる
            rename_map = {
                "エリア": "エリア",
                "年齢": "年齢",
                "性別": "性別",
                "配信開始": "配信開始",
                "配信終了": "配信終了",
                "広告アカウント名": "広告アカウント名",
            }

            legacy_result = legacy_result.rename(
                columns=rename_map
            )

            # API専用IDは存在しない
            legacy_result["ad_id"] = ""
            legacy_result["campaign_id"] = ""
            legacy_result["adset_id"] = ""
            legacy_result["ad_account_id"] = ""

            legacy_result["データ種別"] = "LEGACY"


    # =====================================================
    # 新広告 + レガシー広告
    # =====================================================

    frames = []

    if not new_result.empty:
        frames.append(new_result)

    if not legacy_result.empty:
        frames.append(legacy_result)

    if not frames:
        return pd.DataFrame()

    result = pd.concat(
        frames,
        ignore_index=True,
        sort=False,
    )


    # =====================================================
    # 文字列を整理
    # =====================================================

    text_columns = [
        "ad_id",
        "案件ID",
        "Meta顧客ID",
        "施設ID",
        "campaign_id",
        "adset_id",
        "ad_account_id",
        "キャンペーン名",
        "データ種別",
        "エリア",
        "年齢",
        "性別",
        "広告アカウント名",
        "営業担当",
        "アポ担当",
        "商材",
        "訴求内容",
        "案件名",
        "業種",
        "施設名",
        "都道府県",
        "住所",
        "電話番号",
    ]

    for column in text_columns:
        if column in result.columns:
            result[column] = result[column].map(
                _clean_text
            )

    # =====================================================
    # 顧客表示名
    #
    # 案件名（現在のMeta顧客名）と施設名が同じ
    # → 案件名だけ
    #
    # 異なる
    # → 案件名 + 施設名
    # =====================================================

    def make_customer_display_name(row):
        customer_name = _clean_text(
            row.get("案件名", "")
        )

        facility_name = _clean_text(
            row.get("施設名", "")
        )

        if not facility_name:
            return customer_name

        if customer_name == facility_name:
            return customer_name

        return (
            customer_name
            + " "
            + facility_name
        ).strip()

    result["顧客表示名"] = result.apply(
        make_customer_display_name,
        axis=1,
    )

    # =====================================================
    # 最終的な列順
    # =====================================================

    column_order = [
        "データ種別",
        "ad_id",
        "キャンペーン名",

        "案件ID",
        "Meta顧客ID",
        "施設ID",

        "案件名",
        "施設名",
        "顧客表示名",
        "都道府県",
        "住所",
        "電話番号",
        "業種",

        "営業担当",
        "アポ担当",
        "商材",
        "訴求内容",

        "エリア",
        "年齢",
        "性別",
        "配信開始",
        "配信終了",

        "campaign_id",
        "adset_id",
        "ad_account_id",
        "広告アカウント名",

        "契約期間",
        "保守月額",
        "月間広告費",
        "年間広告費",
    ]

    existing_columns = [
        column
        for column in column_order
        if column in result.columns
    ]

    result = result[existing_columns]

    return result.reset_index(drop=True)

# =========================================================
# 検索条件候補
# =========================================================

def get_search_options(ad_data):
    """
    検索画面のプルダウン候補を作る。

    Returns
    -------
    dict
        customers
        prefectures
        staff
        industries
        appeals
    """

    if ad_data.empty:
        return {
            "customers": [],
            "prefectures": [],
            "staff": [],
            "industries": [],
            "appeals": [],
        }

    # =====================================================
    # 顧客候補
    #
    # Meta顧客ID（法人）単位で1つにまとめ、
    # 配下の施設名をカッコ内に表示する。
    #
    # 例：
    # 医療法人社団 樹伸会
    # （大宮いしはた歯科 / 久喜総合歯科）
    # =====================================================

    # 顧客
    customer_directory = (
        _build_customer_directory(ad_data)
    )

    customers = sorted(
        customer_directory[
            "顧客表示名"
        ].tolist()
    )

    # 都道府県
    prefectures = _unique_sorted_values(
        ad_data,
        "都道府県",
    )

    # 営業担当 + アポ担当を1つの候補にまとめる
    staff = set()

    for column in ["営業担当", "アポ担当"]:
        if column not in ad_data.columns:
            continue

        for value in ad_data[column].tolist():
            cleaned = _clean_text(value)

            if cleaned:
                staff.add(cleaned)

    staff = sorted(staff)

    # 業種
    industries = _unique_sorted_values(
        ad_data,
        "業種",
    )

    # 訴求内容
    appeals = _unique_sorted_values(
        ad_data,
        "訴求内容",
    )

    return {
        "customers": customers,
        "prefectures": prefectures,
        "staff": staff,
        "industries": industries,
        "appeals": appeals,
    }


# =========================================================
# 広告検索
# =========================================================

def search_ads(
    ad_data,
    customer="",
    prefecture="",
    staff="",
    industry="",
    appeal="",
):
    """
    指定された条件で広告を絞り込む。

    空欄の条件は無視する。
    複数条件が指定された場合はAND検索。

    staff は
    「営業担当 または アポ担当」
    のどちらかに一致すれば対象。
    """

    if ad_data.empty:
        return ad_data.copy()

    result = ad_data.copy()

    customer = _clean_text(customer)
    prefecture = _clean_text(prefecture)
    staff = _clean_text(staff)
    industry = _clean_text(industry)
    appeal = _clean_text(appeal)

    # -----------------------------------------------------
    # 顧客
    # -----------------------------------------------------

    if customer:

        customer_directory = (
            _build_customer_directory(result)
        )

        matched_customer_ids = (
            customer_directory.loc[
                customer_directory[
                    "顧客表示名"
                ] == customer,
                "Meta顧客ID",
            ]
            .tolist()
        )

        result = result[
            result["Meta顧客ID"].isin(
                matched_customer_ids
            )
        ]

    # -----------------------------------------------------
    # 都道府県
    # -----------------------------------------------------

    if prefecture and "都道府県" in result.columns:
        result = result[
            result["都道府県"] == prefecture
        ]

    # -----------------------------------------------------
    # 営業担当 または アポ担当
    # -----------------------------------------------------

    if staff:
        sales_match = pd.Series(
            False,
            index=result.index,
        )

        appointment_match = pd.Series(
            False,
            index=result.index,
        )

        if "営業担当" in result.columns:
            sales_match = (
                result["営業担当"] == staff
            )

        if "アポ担当" in result.columns:
            appointment_match = (
                result["アポ担当"] == staff
            )

        result = result[
            sales_match | appointment_match
        ]

    # -----------------------------------------------------
    # 業種
    # -----------------------------------------------------

    if industry and "業種" in result.columns:
        result = result[
            result["業種"] == industry
        ]

    # -----------------------------------------------------
    # 訴求内容
    # -----------------------------------------------------

    if appeal and "訴求内容" in result.columns:
        result = result[
            result["訴求内容"] == appeal
        ]

    # =====================================================
    # 検索条件は「顧客を見つけるため」に使用する
    #
    # 条件に一致した広告・案件からMeta顧客IDを特定し、
    # 最終表示ではその顧客の全案件・全広告を返す。
    #
    # 例：
    # A001 営業：馬場 / アポ：馬場
    # A002 営業：馬場 / アポ：三倉
    #
    # 「三倉」で検索
    #   ↓
    # A002がヒット
    #   ↓
    # 同じMeta顧客IDのA001・A002を両方表示
    # =====================================================

    if result.empty:
        return result.reset_index(
            drop=True
        )

    if "Meta顧客ID" not in result.columns:
        return result.reset_index(
            drop=True
        )

    matched_customer_ids = (
        result["Meta顧客ID"]
        .astype(str)
        .str.strip()
    )

    matched_customer_ids = {
        customer_id
        for customer_id
        in matched_customer_ids.tolist()
        if customer_id
    }

    if not matched_customer_ids:
        return result.reset_index(
            drop=True
        )

    # 元の全広告データへ戻り、
    # ヒットした顧客の全案件・全広告を取得
    full_result = ad_data[
        ad_data["Meta顧客ID"]
        .astype(str)
        .str.strip()
        .isin(matched_customer_ids)
    ].copy()

    return full_result.reset_index(
        drop=True
    )


# =========================================================
# 顧客一覧
# =========================================================

def build_customer_results(ad_data):
    """
    検索後の広告をMeta顧客ID単位にまとめる。

    顧客一覧は1法人1行。
    配下施設は顧客表示名にまとめて表示する。
    """

    if ad_data.empty:
        return pd.DataFrame(
            columns=[
                "Meta顧客ID",
                "案件名",
                "顧客表示名",
                "広告数",
            ]
        )

    work = ad_data.copy()

    # -----------------------------------------------------
    # API / LEGACY 共通の広告識別キー
    # -----------------------------------------------------

    def make_ad_key(row):

        data_type = _clean_text(
            row.get("データ種別", "")
        )

        if data_type == "LEGACY":
            return (
                "LEGACY:"
                + _clean_text(
                    row.get("案件ID", "")
                )
                + ":"
                + _clean_text(
                    row.get("キャンペーン名", "")
                )
            )

        return (
            "API:"
            + _clean_text(
                row.get("ad_id", "")
            )
        )

    work["_広告キー"] = work.apply(
        make_ad_key,
        axis=1,
    )

    # 法人・施設の共通表示名
    customer_directory = (
        _build_customer_directory(work)
    )

    # M単位の広告数
    ad_counts = (
        work.groupby(
            "Meta顧客ID",
            as_index=False,
        )
        .agg(
            広告数=(
                "_広告キー",
                "nunique",
            )
        )
    )

    result = customer_directory.merge(
        ad_counts,
        on="Meta顧客ID",
        how="left",
    )

    result = result.sort_values(
        by=[
            "顧客表示名",
            "Meta顧客ID",
        ]
    )

    return result.reset_index(drop=True)

# =========================================================
# 顧客に属する広告一覧
# =========================================================

def get_customer_ads(
    ad_data,
    customer_id,
):
    """
    指定したMeta顧客IDに属する広告を返す。

    顧客詳細 → 広告一覧
    の画面で使用する。
    """

    if ad_data.empty:
        return ad_data.copy()

    customer_id = _clean_text(customer_id)

    if not customer_id:
        return ad_data.iloc[0:0].copy()

    if "Meta顧客ID" not in ad_data.columns:
        return ad_data.iloc[0:0].copy()

    result = ad_data[
        ad_data["Meta顧客ID"] == customer_id
    ]

    return result.reset_index(drop=True)