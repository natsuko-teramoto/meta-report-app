from services.period import PERIOD_MODE_MONTH

def build_report_period_label(report_period):
    if report_period is None: return "-"
    if report_period.mode == PERIOD_MODE_MONTH:
        return f"{report_period.target_start.year}年{report_period.target_start.month}月"
    return f"{report_period.target_start:%Y/%m/%d} ～ {report_period.target_end:%Y/%m/%d}"
