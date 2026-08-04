import pandas as pd

def total(df, col):
    if df is None or col not in df.columns:
        return 0

    values = (
        df[col]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("%", "", regex=False)
    )

    return pd.to_numeric(values, errors="coerce").fillna(0).sum()

def format_num(value):
    return f"{value:,.0f}"

def calc_change(current_value, prev_value):
    if prev_value is None or prev_value == 0:
        return ""

    change = (current_value - prev_value) / prev_value * 100

    if change > 0:
        return f"▲{change:.1f}%"
    elif change < 0:
        return f"▼{abs(change):.1f}%"
    else:
        return "±0.0%"

def build_summary_metrics(
    df,
    prev_df,
    selected_summary_metrics,
):
    metrics = []

    if selected_summary_metrics is None:
        selected_summary_metrics = []

    metric_defs = [
        {"key": "インプレッション", "label": "インプレッション", "column": "インプレッション", "kind": "frequency"},
        {"key": "リーチ", "label": "リーチ", "column": "リーチ", "kind": "normal"},
        {"key": "クリック(すべて)", "label": "クリック(すべて)", "column": "クリック(すべて)", "kind": "reach_rate"},
        {"key": "リンククリック", "label": "リンククリック", "column": "リンククリック", "kind": "reach_rate"},
        {"key": "ランディングページビュー", "label": "LPビュー", "column": "ランディングページビュー", "kind": "reach_rate"},
    ]

    reach_total = total(df, "リーチ")

    for metric_def in metric_defs:
        if metric_def["key"] not in selected_summary_metrics:
            continue

        column = metric_def["column"]
        value_total = total(df, column)

        frequency = None
        reach_rate = None

        if metric_def["kind"] == "frequency" and reach_total > 0:
            frequency = value_total / reach_total

        if metric_def["kind"] == "reach_rate" and reach_total > 0:
            reach_rate = value_total / reach_total * 100

        change = None
        if prev_df is not None:
            prev_value = total(prev_df, column)
            if prev_value != 0:
                change = (value_total - prev_value) / prev_value * 100


        metrics.append({
            "key": metric_def["key"],
            "label": metric_def["label"],
            "column": column,
            "value": value_total,
            "frequency": frequency,
            "reach_rate": reach_rate,
            "change": change,
        })

    return metrics

def build_report(
    selected_month,
    selected_campaign,
    start_from_first,
    days_from_start,
    filtered_df,
    cumulative_df,
    place_summary=None,
    detail_summary=None,
    analysis_sections=None,
    prev_df=None,
    show_place=True,
    show_awareness=True,
    show_action=True,
    show_gender=True,
    show_age=True,
    show_detail=True,
    selected_summary_metrics=None,
):
    if selected_summary_metrics is None:
        selected_summary_metrics = []

    metrics = build_summary_metrics(
        filtered_df,
        prev_df,
        selected_summary_metrics,
    )

    cumulative_metrics = build_summary_metrics(
        cumulative_df,
        None,
        selected_summary_metrics,
    )
    report = {
        "month": selected_month,
        "campaign": selected_campaign,

        "summary": {
            "start_date": str(start_from_first),
            "elapsed_days": f"{days_from_start}日",
            "metrics": metrics,
            "cumulative_metrics": cumulative_metrics,
        },

        "placement": place_summary,
        "detail": detail_summary,
        "analysis_sections": analysis_sections or [],

        "pages": {
            "summary": True,
            "placement": show_place,
            "awareness": show_awareness,
            "action": show_action,
            "gender": show_gender,
            "age": show_age,
            "detail": show_detail,
        },
    }

    return report

def build_detail_columns(selected_summary_metrics):
    detail_cols = ["期間"]

    if "インプレッション" in selected_summary_metrics:
        detail_cols.append("インプレッション")

    if "リーチ" in selected_summary_metrics:
        detail_cols.append("リーチ")

    if "クリック(すべて)" in selected_summary_metrics:
        detail_cols.append("リンククリック（すべて）")

    if "リンククリック" in selected_summary_metrics:
        detail_cols.append("リンククリック")

    if "ランディングページビュー" in selected_summary_metrics:
        detail_cols.append("LPビュー")

    return detail_cols

def build_place_columns(selected_summary_metrics):
    place_cols = [
        "配置",
        "配信",
        "アトリビューション設定",
    ]

    if "インプレッション" in selected_summary_metrics:
        place_cols.append("インプレッション")

    if "リーチ" in selected_summary_metrics:
        place_cols.append("リーチ")

    if "クリック(すべて)" in selected_summary_metrics:
        place_cols.append("クリック(すべて)")

    if "リンククリック" in selected_summary_metrics:
        place_cols.append("リンククリック")

    if "ランディングページビュー" in selected_summary_metrics:
        place_cols.append("LPビュー")

    return place_cols

def build_awareness_chart_columns(selected_summary_metrics):
    columns = []

    if "インプレッション" in selected_summary_metrics:
        columns.append("インプレッション")

    if "リーチ" in selected_summary_metrics:
        columns.append("リーチ")

    return columns

def build_action_chart_columns(selected_summary_metrics):
    columns = []

    if "クリック(すべて)" in selected_summary_metrics:
        columns.append("クリック(すべて)")

    if "リンククリック" in selected_summary_metrics:
        columns.append("リンククリック")

    if "ランディングページビュー" in selected_summary_metrics:
        columns.append("ランディングページビュー")

    return columns

def build_cumulative_awareness_chart_columns(selected_summary_metrics):
    columns = []

    if "インプレッション" in selected_summary_metrics:
        columns.append("累計インプレッション")

    if "リーチ" in selected_summary_metrics:
        columns.append("累計リーチ")

    return columns


def build_cumulative_action_chart_columns(selected_summary_metrics):
    columns = []

    if "クリック(すべて)" in selected_summary_metrics:
        columns.append("累計クリック(すべて)")

    if "リンククリック" in selected_summary_metrics:
        columns.append("累計リンククリック")

    if "ランディングページビュー" in selected_summary_metrics:
        columns.append("累計LPビュー")

    return columns

def build_analysis_metrics(
    show_analysis_impression,
    show_analysis_reach,
    show_analysis_click,
    show_analysis_link_click,
    show_analysis_lp,
):
    analysis_metrics = []

    if show_analysis_impression:
        analysis_metrics.append("インプレッション")

    if show_analysis_reach:
        analysis_metrics.append("リーチ")

    if show_analysis_click:
        analysis_metrics.append("クリック(すべて)")

    if show_analysis_link_click:
        analysis_metrics.append("リンククリック")

    if show_analysis_lp:
        analysis_metrics.append("ランディングページビュー")

    return analysis_metrics