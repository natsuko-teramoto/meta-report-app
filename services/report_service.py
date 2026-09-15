from services.meta_api_source import (
    fetch_ad_period_insights,
    fetch_ad_age_gender_insights,
    fetch_ad_placement_insights,
    fetch_ad_daily_insights,
    fetch_ad_monthly_insights,
)

# =========================================================
# 率計算
# =========================================================

def _calculate_reach_rate(
    value,
    reach,
):
    """
    リーチ数に対する割合を％で返す。

    例:
    value=179
    reach=5535
    → 3.23
    """

    if not reach:
        return 0.0

    return (
        value
        / reach
        * 100
    )


# =========================================================
# Meta取得値 → レポート表示用データ
# =========================================================

def _build_metric_result(
    insights,
):
    """
    Meta APIから取得した基本指標を、
    レポート表示用データへ整形する。

    frequency:
        Meta APIの値をそのまま使用。

    click_rate:
        clicks ÷ reach

    link_click_rate:
        link_clicks ÷ reach

    landing_page_view_rate:
        landing_page_views ÷ reach
    """

    impressions = insights[
        "impressions"
    ]
    reach = insights[
        "reach"
    ]
    frequency = insights[
        "frequency"
    ]
    clicks = insights[
        "clicks"
    ]
    link_clicks = insights[
        "link_clicks"
    ]
    landing_page_views = insights[
        "landing_page_views"
    ]

    return {
        "impressions": impressions,
        "reach": reach,
        "frequency": frequency,
        "clicks": clicks,
        "click_rate": (
            _calculate_reach_rate(
                clicks,
                reach,
            )
        ),
        "link_clicks": link_clicks,
        "link_click_rate": (
            _calculate_reach_rate(
                link_clicks,
                reach,
            )
        ),
        "landing_page_views": (
            landing_page_views
        ),
        "landing_page_view_rate": (
            _calculate_reach_rate(
                landing_page_views,
                reach,
            )
        ),
    }


# =========================================================
# 1広告 × 3期間 レポートデータ
# =========================================================

def build_period_result(
    ad_row,
    report_period,
):
    if ad_row is None:
        raise ValueError(
            "広告情報がありません。"
        )

    if report_period is None:
        raise ValueError(
            "レポート期間がありません。"
        )

    ad_id = str(
        ad_row.get("ad_id", "")
    ).strip()

    if not ad_id:
        raise ValueError(
            "ad_id がありません。"
        )

    # ------------------------------
    # 設定期間
    # ------------------------------
    target_insights = (
        fetch_ad_period_insights(
            ad_id=ad_id,
            start_date=report_period.target_start,
            end_date=report_period.target_end,
        )
    )

    # ------------------------------
    # 前期間
    # ------------------------------
    comparison_insights = (
        fetch_ad_period_insights(
            ad_id=ad_id,
            start_date=report_period.comparison_start,
            end_date=report_period.comparison_end,
        )
    )

    # ------------------------------
    # 配信開始からの累計
    # ------------------------------
    cumulative_insights = (
        fetch_ad_period_insights(
            ad_id=ad_id,
            start_date=report_period.cumulative_start,
            end_date=report_period.cumulative_end,
        )
    )

    # ------------------------------
    # 設定期間 年齢・性別
    # ------------------------------
    target_age_gender = (
        fetch_ad_age_gender_insights(
            ad_id=ad_id,
            start_date=report_period.target_start,
            end_date=report_period.target_end,
        )
    )

    # ------------------------------
    # 配信開始からの累計 年齢・性別
    # ------------------------------
    cumulative_age_gender = (
        fetch_ad_age_gender_insights(
            ad_id=ad_id,
            start_date=report_period.cumulative_start,
            end_date=report_period.cumulative_end,
        )
    )

    # ------------------------------
    # 設定期間 表示場所
    # ------------------------------
    target_placement = (
        fetch_ad_placement_insights(
            ad_id=ad_id,
            start_date=report_period.target_start,
            end_date=report_period.target_end,
        )
    )

    # ------------------------------
    # 設定期間 デイリー推移
    # ------------------------------
    target_daily = (
        fetch_ad_daily_insights(
            ad_id=ad_id,
            start_date=report_period.target_start,
            end_date=report_period.target_end,
        )
    )

    # ------------------------------
    # 配信開始からの月次推移
    # ------------------------------
    cumulative_monthly = (
        fetch_ad_monthly_insights(
            ad_id=ad_id,
            start_date=report_period.cumulative_start,
            end_date=report_period.cumulative_end,
        )
    )

    return {
        "target": _build_metric_result(
            target_insights
        ),
        "comparison": _build_metric_result(
            comparison_insights
        ),
        "cumulative": _build_metric_result(
            cumulative_insights
        ),
        "target_age_gender": target_age_gender,
        "cumulative_age_gender": cumulative_age_gender,
        "target_placement": target_placement,
        "target_daily": target_daily,
        "cumulative_monthly": cumulative_monthly,
    }