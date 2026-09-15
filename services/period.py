from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta


# =========================================================
# 定数
# =========================================================

PERIOD_MODE_MONTH = "month"
PERIOD_MODE_CUSTOM = "custom"


# =========================================================
# データ構造
# =========================================================

@dataclass(frozen=True)
class ReportPeriod:
    """
    レポートで使用する期間情報。

    target
        今回レポートとして表示する対象期間

    comparison
        「前期間比」で比較する期間

    cumulative
        広告掲載開始から対象期間終了日まで
    """

    mode: str

    target_start: date
    target_end: date

    comparison_start: date
    comparison_end: date

    cumulative_start: date
    cumulative_end: date


# =========================================================
# 共通
# =========================================================

def _validate_publication_start(
    publication_start,
):
    """
    掲載開始日の基本チェック。
    """

    if publication_start is None:
        raise ValueError(
            "広告の掲載開始日が取得できません。"
        )

    if not isinstance(
        publication_start,
        date,
    ):
        raise ValueError(
            "広告の掲載開始日はdate型で指定してください。"
        )


def _validate_target_period(
    target_start,
    target_end,
):
    """
    対象期間の基本チェック。
    """

    if (
        target_start is None
        or target_end is None
    ):
        raise ValueError(
            "対象期間の開始日と終了日を指定してください。"
        )

    if target_start > target_end:
        raise ValueError(
            "対象期間の開始日は終了日以前にしてください。"
        )


def _validate_publication_overlap(
    publication_start,
    target_end,
):
    """
    対象期間が広告掲載開始より前だけで構成されていないか確認する。

    対象期間の途中から掲載開始するケースは許可する。
    """

    if target_end < publication_start:
        raise ValueError(
            "この広告は指定した対象期間には"
            "まだ掲載されていません。"
        )


# =========================================================
# 月次
# =========================================================

def build_month_period(
    year,
    month,
    publication_start,
):
    """
    カレンダー月単位のレポート期間を作る。

    例
    2026年8月

    target
        2026/08/01 ～ 2026/08/31

    comparison
        2026/07/01 ～ 2026/07/31

    cumulative
        掲載開始日 ～ 2026/08/31
    """

    _validate_publication_start(
        publication_start
    )

    if month < 1 or month > 12:
        raise ValueError(
            "月は1～12で指定してください。"
        )

    # -----------------------------------------------------
    # 対象月
    # -----------------------------------------------------

    last_day = monthrange(
        year,
        month,
    )[1]

    target_start = date(
        year,
        month,
        1,
    )

    target_end = date(
        year,
        month,
        last_day,
    )

    _validate_publication_overlap(
        publication_start,
        target_end,
    )

    # -----------------------------------------------------
    # 前月
    # -----------------------------------------------------

    if month == 1:
        previous_year = year - 1
        previous_month = 12
    else:
        previous_year = year
        previous_month = month - 1

    previous_last_day = monthrange(
        previous_year,
        previous_month,
    )[1]

    comparison_start = date(
        previous_year,
        previous_month,
        1,
    )

    comparison_end = date(
        previous_year,
        previous_month,
        previous_last_day,
    )

    # -----------------------------------------------------
    # 累計
    # -----------------------------------------------------

    cumulative_start = publication_start
    cumulative_end = target_end

    return ReportPeriod(
        mode=PERIOD_MODE_MONTH,

        target_start=target_start,
        target_end=target_end,

        comparison_start=comparison_start,
        comparison_end=comparison_end,

        cumulative_start=cumulative_start,
        cumulative_end=cumulative_end,
    )


# =========================================================
# 任意期間
# =========================================================

def build_custom_period(
    target_start,
    target_end,
    publication_start,
):
    """
    任意期間のレポート期間を作る。

    比較期間は
    「対象期間の直前にある同じ日数」。

    例
    target
        2026/08/10 ～ 2026/08/24
        = 15日間

    comparison
        2026/07/26 ～ 2026/08/09
        = 15日間

    cumulative
        掲載開始日 ～ 2026/08/24
    """

    _validate_publication_start(
        publication_start
    )

    _validate_target_period(
        target_start,
        target_end,
    )

    _validate_publication_overlap(
        publication_start,
        target_end,
    )

    # 対象期間の日数
    target_days = (
        target_end
        - target_start
    ).days + 1

    # 比較期間は対象開始日の前日まで
    comparison_end = (
        target_start
        - timedelta(days=1)
    )

    comparison_start = (
        comparison_end
        - timedelta(
            days=target_days - 1
        )
    )

    # -----------------------------------------------------
    # 累計
    # -----------------------------------------------------

    cumulative_start = publication_start
    cumulative_end = target_end

    return ReportPeriod(
        mode=PERIOD_MODE_CUSTOM,

        target_start=target_start,
        target_end=target_end,

        comparison_start=comparison_start,
        comparison_end=comparison_end,

        cumulative_start=cumulative_start,
        cumulative_end=cumulative_end,
    )


# =========================================================
# 共通入口
# =========================================================

def build_report_period(
    mode,
    publication_start,
    year=None,
    month=None,
    target_start=None,
    target_end=None,
):
    """
    画面側から呼ぶ共通入口。

    mode="month"
        year / month を使用

    mode="custom"
        target_start / target_end を使用
    """

    if mode == PERIOD_MODE_MONTH:

        if year is None or month is None:
            raise ValueError(
                "月次レポートでは年と月を指定してください。"
            )

        return build_month_period(
            year=year,
            month=month,
            publication_start=publication_start,
        )

    if mode == PERIOD_MODE_CUSTOM:

        return build_custom_period(
            target_start=target_start,
            target_end=target_end,
            publication_start=publication_start,
        )

    raise ValueError(
        f"未対応の期間モードです: {mode}"
    )