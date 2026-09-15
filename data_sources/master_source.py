from pathlib import Path

import gspread
import pandas as pd
import streamlit as st


# =========================================================
# 基本設定
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

CREDENTIALS_FILE = BASE_DIR / "credentials.json"

SPREADSHEET_ID = "1jQlMBosAHIDCn6kjq_8JyxxeIhbBpzJdGzfV8hiVU_0"


SHEET_NAMES = {
    "customers": "Meta顧客マスタ",
    "facilities": "施設マスタ",
    "cases": "案件マスタ",
    "meta_history": "Meta配信履歴",
    "legacy_ads": "レガシー広告一覧",
}


# =========================================================
# Google Sheets 接続
# =========================================================

def _get_spreadsheet():
    """
    Google Sheetsへ接続する。

    ローカル:
        credentials.json を使用

    Streamlit Cloud:
        st.secrets["gcp_service_account"] を使用
    """

    # -------------------------------------------------
    # ローカル環境
    # -------------------------------------------------
    if CREDENTIALS_FILE.exists():

        client = gspread.service_account(
            filename=str(CREDENTIALS_FILE)
        )

        return client.open_by_key(SPREADSHEET_ID)

    # -------------------------------------------------
    # Streamlit Cloud
    # -------------------------------------------------
    try:
        credentials_info = dict(
            st.secrets["gcp_service_account"]
        )
    except Exception as exc:
        raise RuntimeError(
            "Google Sheets認証情報を取得できません。"
            "Streamlit Secrets の "
            "[gcp_service_account] を確認してください。"
        ) from exc

    try:
        client = gspread.service_account_from_dict(
            credentials_info
        )
    except Exception as exc:
        raise RuntimeError(
            "Google Sheets認証情報の読み込みに失敗しました。"
        ) from exc

    return client.open_by_key(SPREADSHEET_ID)

# =========================================================
# 1シート読み込み
# =========================================================

def _read_sheet(spreadsheet, sheet_name):
    """
    指定したシートをDataFrameとして読み込む。

    1行目を列名として使用し、
    完全な空行は除外する。
    """

    worksheet = spreadsheet.worksheet(sheet_name)

    values = worksheet.get_all_values()

    if not values:
        return pd.DataFrame()

    headers = values[0]
    rows = values[1:]

    if not rows:
        return pd.DataFrame(columns=headers)

    df = pd.DataFrame(rows, columns=headers)

    # 完全な空行を除外
    df = df.replace("", pd.NA)
    df = df.dropna(how="all")
    df = df.fillna("")

    return df.reset_index(drop=True)


# =========================================================
# 各マスタ取得
# =========================================================

def load_customer_master():
    """
    Meta顧客マスタを取得。
    """

    spreadsheet = _get_spreadsheet()

    return _read_sheet(
        spreadsheet,
        SHEET_NAMES["customers"],
    )


def load_facility_master():
    """
    施設マスタを取得。
    """

    spreadsheet = _get_spreadsheet()

    return _read_sheet(
        spreadsheet,
        SHEET_NAMES["facilities"],
    )


def load_case_master():
    """
    案件マスタを取得。
    """

    spreadsheet = _get_spreadsheet()

    return _read_sheet(
        spreadsheet,
        SHEET_NAMES["cases"],
    )


def load_meta_history():
    """
    Meta配信履歴を取得。
    """

    spreadsheet = _get_spreadsheet()

    return _read_sheet(
        spreadsheet,
        SHEET_NAMES["meta_history"],
    )


# =========================================================
# 全マスタ一括取得
# =========================================================

def load_all_master_data():
    """
    Meta広告レポートで使用する4シートを一括取得。

    Returns
    -------
    dict
        customers
        facilities
        cases
        meta_history
    """

    spreadsheet = _get_spreadsheet()

    return {
        "customers": _read_sheet(
            spreadsheet,
            SHEET_NAMES["customers"],
        ),
        "facilities": _read_sheet(
            spreadsheet,
            SHEET_NAMES["facilities"],
        ),
        "cases": _read_sheet(
            spreadsheet,
            SHEET_NAMES["cases"],
        ),
        "meta_history": _read_sheet(
            spreadsheet,
            SHEET_NAMES["meta_history"],
        ),
        "legacy_ads": _read_sheet(
            spreadsheet,
            SHEET_NAMES["legacy_ads"],
        ),
    }
    