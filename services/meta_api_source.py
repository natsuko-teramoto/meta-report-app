import json

import requests
import streamlit as st


# =========================================================
# Meta API 設定
# =========================================================

META_API_VERSION = "v26.0"
META_GRAPH_URL = "https://graph.facebook.com"


# =========================================================
# アクセストークン
# =========================================================

def _get_access_token():
    """
    Streamlit Secretsから
    Metaアクセストークンを取得する。
    """

    try:
        token = st.secrets["META_ACCESS_TOKEN"]
    except Exception as exc:
        raise RuntimeError(
            "META_ACCESS_TOKENを取得できません。"
        ) from exc

    token = str(token).strip()

    if not token:
        raise RuntimeError(
            "META_ACCESS_TOKENが空です。"
        )

    return token


# =========================================================
# 共通APIリクエスト
# =========================================================

def _request_meta_api(
    object_path,
    params=None,
):
    """
    Meta Graph APIへGETリクエストする共通処理。
    """

    if params is None:
        params = {}

    request_params = dict(params)
    request_params["access_token"] = (
        _get_access_token()
    )

    url = (
        f"{META_GRAPH_URL}/"
        f"{META_API_VERSION}/"
        f"{object_path}"
    )

    response = requests.get(
        url,
        params=request_params,
        timeout=30,
    )

    try:
        result = response.json()
    except ValueError as exc:
        raise RuntimeError(
            "Meta APIからJSON形式ではない"
            "レスポンスが返されました。"
        ) from exc

    if not response.ok:

        error = result.get(
            "error",
            {},
        )

        message = error.get(
            "message",
            "Meta APIでエラーが発生しました。",
        )

        raise RuntimeError(
            f"Meta APIエラー: {message}"
        )

    return result


# =========================================================
# actions取得
# =========================================================

def _get_action_value(
    actions,
    action_type,
):
    """
    actions配列から指定action_typeの値を取得する。
    """

    if not actions:
        return 0

    for action in actions:

        if (
            action.get("action_type")
            == action_type
        ):

            try:
                return int(
                    float(
                        action.get(
                            "value",
                            0,
                        )
                    )
                )

            except (
                TypeError,
                ValueError,
            ):
                return 0

    return 0


# =========================================================
# 1広告 × 1期間 Insights
# =========================================================

def fetch_ad_period_insights(
    ad_id,
    start_date,
    end_date,
):
    """
    1つのad_idについて、
    指定期間の基本指標を取得する。

    取得指標
    - impressions
    - reach
    - frequency
    - clicks
    - inline_link_clicks
    - landing_page_views

    frequencyはMeta APIの値をそのまま使用する。

    Reachは指定期間全体を
    Meta APIへ1回問い合わせて取得する。
    日別値の合算はしない。
    """

    if not ad_id:
        raise ValueError(
            "ad_idがありません。"
        )

    if start_date is None:
        raise ValueError(
            "開始日がありません。"
        )

    if end_date is None:
        raise ValueError(
            "終了日がありません。"
        )

    if start_date > end_date:
        raise ValueError(
            "開始日は終了日以前にしてください。"
        )

    time_range = {
        "since": start_date.strftime(
            "%Y-%m-%d"
        ),
        "until": end_date.strftime(
            "%Y-%m-%d"
        ),
    }

    result = _request_meta_api(
        f"{ad_id}/insights",
        params={
            "fields": ",".join([
                "impressions",
                "reach",
                "frequency",
                "clicks",
                "inline_link_clicks",
                "actions",
            ]),
            "time_range": json.dumps(
                time_range
            ),
        },
    )

    rows = result.get(
        "data",
        [],
    )

    if not rows:

        return {
            "impressions": 0,
            "reach": 0,
            "frequency": 0.0,
            "clicks": 0,
            "link_clicks": 0,
            "landing_page_views": 0,
        }

    row = rows[0]

    impressions = int(
        row.get(
            "impressions",
            0,
        )
        or 0
    )

    reach = int(
        row.get(
            "reach",
            0,
        )
        or 0
    )

    try:
        frequency = float(
            row.get(
                "frequency",
                0,
            )
            or 0
        )
    except (
        TypeError,
        ValueError,
    ):
        frequency = 0.0

    clicks = int(
        row.get(
            "clicks",
            0,
        )
        or 0
    )

    link_clicks = int(
        row.get(
            "inline_link_clicks",
            0,
        )
        or 0
    )

    landing_page_views = (
        _get_action_value(
            row.get(
                "actions",
                [],
            ),
            "landing_page_view",
        )
    )

    return {
        "impressions": impressions,
        "reach": reach,
        "frequency": frequency,
        "clicks": clicks,
        "link_clicks": link_clicks,
        "landing_page_views": (
            landing_page_views
        ),
    }

def fetch_ad_age_gender_insights(
    ad_id,
    start_date,
    end_date,
):
    """
    指定広告・指定期間の
    年齢 × 性別別 Meta Insights を取得する。

    注意:
    breakdownごとのreachは、
    全体reachを作るために合計しない。
    """

    if not ad_id:
        raise ValueError(
            "ad_id がありません。"
        )

    if start_date is None or end_date is None:
        raise ValueError(
            "集計期間を指定してください。"
        )

    if start_date > end_date:
        raise ValueError(
            "集計開始日は終了日以前にしてください。"
        )

    fields = ",".join([
        "impressions",
        "reach",
        "frequency",
        "clicks",
        "inline_link_clicks",
        "actions",
    ])

    params = {
        "access_token": _get_access_token(),
        "level": "ad",
        "fields": fields,
        "breakdowns": "age,gender",
        "time_range": json.dumps({
            "since": start_date.strftime("%Y-%m-%d"),
            "until": end_date.strftime("%Y-%m-%d"),
        }),
    }

    response_data = _request_meta_api(
        object_path=f"{ad_id}/insights",
        params=params,
    )

    rows = response_data.get("data", [])

    results = []

    for row in rows:
        reach = int(
            float(row.get("reach", 0) or 0)
        )

        clicks = int(
            float(row.get("clicks", 0) or 0)
        )

        link_clicks = int(
            float(
                row.get(
                    "inline_link_clicks",
                    0,
                )
                or 0
            )
        )

        landing_page_views = int(
            float(
                _get_action_value(
                    row.get("actions", []),
                    "landing_page_view",
                )
            )
        )

        results.append({
            "age": row.get("age", ""),
            "gender": row.get("gender", ""),
            "impressions": int(
                float(
                    row.get(
                        "impressions",
                        0,
                    )
                    or 0
                )
            ),
            "reach": reach,
            "frequency": float(
                row.get(
                    "frequency",
                    0,
                )
                or 0
            ),
            "clicks": clicks,
            "click_rate": (
                clicks / reach * 100
                if reach > 0
                else 0.0
            ),
            "link_clicks": link_clicks,
            "link_click_rate": (
                link_clicks / reach * 100
                if reach > 0
                else 0.0
            ),
            "landing_page_views": (
                landing_page_views
            ),
            "landing_page_view_rate": (
                landing_page_views
                / reach
                * 100
                if reach > 0
                else 0.0
            ),
        })

    return results

def fetch_ad_daily_insights(
    ad_id,
    start_date,
    end_date,
):
    """
    指定した広告のデイリー推移用データを取得する。

    1日ごとに以下を取得する。
    - impressions
    - reach
    - clicks
    - inline_link_clicks
    - landing_page_views

    注意:
    daily の reach は、その日単位でMetaが重複排除した値。
    累計reachの算出には使用しない。
    """

    if not ad_id:
        raise ValueError(
            "ad_id が指定されていません。"
        )

    if not start_date or not end_date:
        raise ValueError(
            "取得期間が指定されていません。"
        )

    params = {
        "fields": (
            "impressions,"
            "reach,"
            "clicks,"
            "inline_link_clicks,"
            "actions"
        ),
        "time_range": json.dumps({
            "since": start_date.strftime(
                "%Y-%m-%d"
            ),
            "until": end_date.strftime(
                "%Y-%m-%d"
            ),
        }),
        "time_increment": 1,
    }

    response_data = _request_meta_api(
        object_path=f"{ad_id}/insights",
        params=params,
    )

    rows = response_data.get(
        "data",
        [],
    )

    daily_rows = []

    for row in rows:
        impressions = int(
            row.get(
                "impressions",
                0,
            )
            or 0
        )

        reach = int(
            row.get(
                "reach",
                0,
            )
            or 0
        )

        clicks = int(
            row.get(
                "clicks",
                0,
            )
            or 0
        )

        link_clicks = int(
            row.get(
                "inline_link_clicks",
                0,
            )
            or 0
        )

        landing_page_views = 0

        for action in row.get(
            "actions",
            [],
        ):
            if (
                action.get(
                    "action_type"
                )
                == "landing_page_view"
            ):
                landing_page_views = int(
                    float(
                        action.get(
                            "value",
                            0,
                        )
                        or 0
                    )
                )
                break

        daily_rows.append({
            "date": row.get(
                "date_start",
                "",
            ),
            "impressions": impressions,
            "reach": reach,
            "clicks": clicks,
            "link_clicks": link_clicks,
            "landing_page_views": (
                landing_page_views
            ),
        })

    return daily_rows

def fetch_ad_monthly_insights(
    ad_id,
    start_date,
    end_date,
):
    """
    指定した広告の月次推移用データを取得する。

    取得項目:
    - impressions
    - reach
    - frequency
    - clicks
    - inline_link_clicks
    - landing_page_views

    注意:
    月次reachは各月単位でMetaが重複排除した値。
    月次推移の表示専用として使用し、
    累計reachの算出には使用しない。

    frequencyは計算値ではなく、
    Meta APIが返す値をそのまま使用する。
    """

    if not ad_id:
        raise ValueError(
            "ad_id が指定されていません。"
        )

    if not start_date or not end_date:
        raise ValueError(
            "取得期間が指定されていません。"
        )

    params = {
        "fields": (
            "impressions,"
            "reach,"
            "frequency,"
            "clicks,"
            "inline_link_clicks,"
            "actions"
        ),
        "time_range": json.dumps({
            "since": start_date.strftime(
                "%Y-%m-%d"
            ),
            "until": end_date.strftime(
                "%Y-%m-%d"
            ),
        }),
        "time_increment": "monthly",
    }

    response_data = _request_meta_api(
        object_path=f"{ad_id}/insights",
        params=params,
    )

    rows = response_data.get(
        "data",
        [],
    )

    monthly_rows = []

    for row in rows:
        impressions = int(
            row.get(
                "impressions",
                0,
            )
            or 0
        )

        reach = int(
            row.get(
                "reach",
                0,
            )
            or 0
        )

        frequency = float(
            row.get(
                "frequency",
                0,
            )
            or 0
        )

        clicks = int(
            row.get(
                "clicks",
                0,
            )
            or 0
        )

        link_clicks = int(
            row.get(
                "inline_link_clicks",
                0,
            )
            or 0
        )

        landing_page_views = 0

        for action in row.get(
            "actions",
            [],
        ):
            if (
                action.get(
                    "action_type"
                )
                == "landing_page_view"
            ):
                landing_page_views = int(
                    float(
                        action.get(
                            "value",
                            0,
                        )
                        or 0
                    )
                )
                break

        monthly_rows.append({
            "date_start": row.get(
                "date_start",
                "",
            ),
            "date_stop": row.get(
                "date_stop",
                "",
            ),
            "impressions": impressions,
            "reach": reach,
            "frequency": frequency,
            "clicks": clicks,
            "link_clicks": link_clicks,
            "landing_page_views": (
                landing_page_views
            ),
        })

    return monthly_rows

def fetch_ad_placement_insights(
    ad_id,
    start_date,
    end_date,
):
    """
    指定広告・指定期間の
    配置別Meta Insightsを取得する。
    """

    if not ad_id:
        raise ValueError(
            "ad_id がありません。"
        )

    if start_date is None or end_date is None:
        raise ValueError(
            "集計期間を指定してください。"
        )

    if start_date > end_date:
        raise ValueError(
            "集計開始日は終了日以前にしてください。"
        )

    fields = ",".join([
        "impressions",
        "reach",
        "frequency",
        "clicks",
        "inline_link_clicks",
        "actions",
    ])

    params = {
        "access_token": _get_access_token(),
        "level": "ad",
        "fields": fields,
        "breakdowns": (
            "publisher_platform,"
            "platform_position"
        ),
        "time_range": json.dumps({
            "since": start_date.strftime("%Y-%m-%d"),
            "until": end_date.strftime("%Y-%m-%d"),
        }),
    }

    response_data = _request_meta_api(
        object_path=f"{ad_id}/insights",
        params=params,
    )

    rows = response_data.get("data", [])

    results = []

    for row in rows:
        reach = int(
            float(
                row.get("reach", 0)
                or 0
            )
        )

        clicks = int(
            float(
                row.get("clicks", 0)
                or 0
            )
        )

        link_clicks = int(
            float(
                row.get(
                    "inline_link_clicks",
                    0,
                )
                or 0
            )
        )

        landing_page_views = int(
            float(
                _get_action_value(
                    row.get("actions", []),
                    "landing_page_view",
                )
            )
        )

        results.append({
            "publisher_platform": (
                row.get(
                    "publisher_platform",
                    "",
                )
            ),
            "platform_position": (
                row.get(
                    "platform_position",
                    "",
                )
            ),
            "impressions": int(
                float(
                    row.get(
                        "impressions",
                        0,
                    )
                    or 0
                )
            ),
            "reach": reach,
            "frequency": float(
                row.get(
                    "frequency",
                    0,
                )
                or 0
            ),
            "clicks": clicks,
            "click_rate": (
                clicks / reach * 100
                if reach > 0
                else 0.0
            ),
            "link_clicks": link_clicks,
            "link_click_rate": (
                link_clicks
                / reach
                * 100
                if reach > 0
                else 0.0
            ),
            "landing_page_views": (
                landing_page_views
            ),
            "landing_page_view_rate": (
                landing_page_views
                / reach
                * 100
                if reach > 0
                else 0.0
            ),
        })

    return results