import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

METRIC_CONFIG = {
    "impressions": {"label": "インプレッション", "group": "awareness", "color": "#FF6B00"},
    "reach": {"label": "リーチ", "group": "awareness", "color": "#7B2CFF"},
    "clicks": {"label": "クリック", "group": "action", "color": "#FF2D8D"},
    "link_clicks": {"label": "リンククリック", "group": "action", "color": "#009BFC"},
    "landing_page_views": {"label": "LPビュー", "group": "action", "color": "#00B894"},
}

GENDER_COLORS = {"女性": "#009BFC", "男性": "#4000B8", "不明": "#BDBDBD"}

PLACEMENT_COLORS = {
    "Instagramフィード": "#F58529",
    "Instagramストーリーズ": "#DD2A7B",
    "Instagramリール": "#8134AF",
    "Instagram発見ホーム": "#515BD4",
    "Facebookフィード": "#1877F2",
    "Facebookストーリーズ": "#42A5F5",
    "Facebookリール": "#5B7CFA",
    "その他": "#BDBDBD",
}


def visible_metric_keys(visibility):
    return [
        key for key in METRIC_CONFIG
        if visibility.get("metrics", {}).get(key, True)
    ]


def format_period_label(report_period):
    if report_period is None:
        return ""

    start = report_period.target_start
    end = report_period.target_end

    return (
        f"{start.year}/{start.month}/{start.day}"
        f" ～ "
        f"{end.year}/{end.month}/{end.day}"
    )


def value_from_ad(ad_row, *keys, default="―"):
    if ad_row is None:
        return default
    for key in keys:
        try:
            value = ad_row.get(key)
        except AttributeError:
            value = None
        if value is None:
            continue
        text = str(value).strip()
        if text and text.lower() != "nan":
            return text
    return default


def customer_name_from_ad(ad_row, default="Meta広告"):
    """Resolve the actual customer name and never prefer a generic ad/case label."""
    candidates = (
        "顧客名", "customer_name", "Meta顧客名", "顧客名_master",
        "顧客名_y", "customer_name_y", "施設名",
    )
    for key in candidates:
        value = value_from_ad(ad_row, key, default="")
        if value and value not in {"Meta広告", "―", "広告"}:
            return value
    return default


def _build_cumulative_days(ad_row, report_period):
    if report_period is None:
        return "―"
    start = None
    for key in ("配信開始", "配信開始日"):
        raw = value_from_ad(ad_row, key, default="")
        if not raw:
            continue
        parsed = pd.to_datetime(raw, errors="coerce")
        if pd.notna(parsed):
            start = parsed.date()
            break
    if start is None:
        start = report_period.cumulative_start
    if start is None:
        return "―"
    days = (report_period.cumulative_end - start).days + 1
    return f"{max(days, 0):,}日"


def build_basic_info(ad_row, report_period, visibility):
    items = [
        ("customer_name", "顧客名", value_from_ad(ad_row, "顧客名", "customer_name")),
        ("publication_start", "配信開始日", value_from_ad(ad_row, "配信開始", "配信開始日")),
        ("cumulative_days", "累計配信日数", _build_cumulative_days(ad_row, report_period)),
        ("report_period", "レポート集計期間", format_period_label(report_period)),
        ("appeal", "訴求内容", value_from_ad(ad_row, "訴求内容")),
        ("area", "配信エリア", value_from_ad(ad_row, "エリア", "配信エリア")),
        ("age", "年齢", value_from_ad(ad_row, "年齢")),
        ("gender", "性別", value_from_ad(ad_row, "性別")),
    ]
    return [
        (label, value)
        for key, label, value in items
        if visibility.get("basic", {}).get(key, True)
    ]


def _rate(value, reach):
    value = int(value or 0)
    reach = int(reach or 0)
    if reach <= 0:
        return None
    return value / reach * 100


def build_metric_rows(data, visibility, include_change=False, comparison=None):
    data = data or {}
    comparison = comparison or {}
    rows = []
    for metric_key in visible_metric_keys(visibility):
        cfg = METRIC_CONFIG[metric_key]
        value = int(data.get(metric_key, 0) or 0)
        extra = ""
        if metric_key == "impressions":
            extra = f"{float(data.get('frequency', 0) or 0):.2f}回"
        elif metric_key in {"clicks", "link_clicks", "landing_page_views"}:
            rate = _rate(value, data.get("reach", 0))
            extra = f"{rate:.2f}%" if rate is not None else "―"

        change = ""
        if include_change:
            previous = int(comparison.get(metric_key, 0) or 0)
            if previous == 0:
                change = "前期間実績なし" if value > 0 else "±0"
            else:
                diff = (value - previous) / previous * 100
                sign = "+" if diff > 0 else ""
                change = f"{sign}{diff:.1f}%"

        rows.append({
            "key": metric_key,
            "label": cfg["label"],
            "value": f"{value:,}",
            "extra": extra,
            "change": change,
        })
    return rows


def build_age_gender_dataframe(age_gender_rows, metric_key):
    if not age_gender_rows:
        return pd.DataFrame()
    df = pd.DataFrame(age_gender_rows)
    if df.empty or metric_key not in df:
        return pd.DataFrame()
    labels = {"female": "女性", "male": "男性", "unknown": "不明"}
    df["性別"] = df["gender"].map(labels).fillna(df["gender"])
    df["年齢"] = df["age"]
    df["値"] = pd.to_numeric(df[metric_key], errors="coerce").fillna(0)
    total = df["値"].sum()
    df["割合"] = df["値"] / total * 100 if total > 0 else 0.0
    return df


def build_age_gender_table(df):
    """
    Excel版PPTと同じ向きの表を作る。

    列：項目 / 18-24 / 25-34 / 35-44 / 45-54 / 55-64 / 65+
    行：女性 数 / 女性 割合 / 男性 数 / 男性 割合 / 不明 数 / 不明 割合 / 合計 数 / 合計 割合
    """
    if df.empty:
        return pd.DataFrame()

    age_order = [
        "18-24",
        "25-34",
        "35-44",
        "45-54",
        "55-64",
        "65+",
    ]

    gender_order = [
        "女性",
        "男性",
    ]

    work = df.copy()
    work["値"] = pd.to_numeric(
        work["値"],
        errors="coerce",
    ).fillna(0)

    total_value = work["値"].sum()

    rows = []

    for gender in gender_order:
        gender_df = work[
            work["性別"] == gender
        ]


        count_row = {
            "項目": f"{gender} 数",
        }
        rate_row = {
            "項目": f"{gender} 割合",
        }

        for age in age_order:
            value = gender_df.loc[
                gender_df["年齢"] == age,
                "値",
            ].sum()

            count_row[age] = (
                f"{int(value):,}"
                if value > 0
                else "―"
            )

            rate_row[age] = (
                f"{value / total_value * 100:.1f}%"
                if total_value > 0 and value > 0
                else "―"
            )

        rows.append(count_row)
        rows.append(rate_row)

    total_count_row = {
        "項目": "合計 数",
    }
    total_rate_row = {
        "項目": "合計 割合",
    }

    for age in age_order:
        value = work.loc[
            work["年齢"] == age,
            "値",
        ].sum()

        total_count_row[age] = (
            f"{int(value):,}"
            if value > 0
            else "―"
        )

        total_rate_row[age] = (
            f"{value / total_value * 100:.1f}%"
            if total_value > 0 and value > 0
            else "―"
        )

    rows.append(total_count_row)
    rows.append(total_rate_row)

    return pd.DataFrame(
        rows,
        columns=["項目"] + age_order,
    )


def build_age_gender_figures(age_gender_rows, metric_key):
    df = build_age_gender_dataframe(age_gender_rows, metric_key)
    if df.empty:
        return None, None, pd.DataFrame()

    bar = px.bar(
        df,
        x="年齢",
        y="値",
        color="性別",
        barmode="group",
        text=df.apply(
            lambda r: f"{int(r['値']):,}<br>{r['割合']:.1f}%",
            axis=1,
        ),
        category_orders={
            "性別": ["女性", "男性", "不明"],
            "年齢": ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"],
        },
        color_discrete_map=GENDER_COLORS,
    )
    bar.update_traces(
        textposition="outside",
        cliponaxis=False,
        marker_line_width=0,
        textfont=dict(size=15, color="#282828"),
    )
    bar.update_layout(
        height=560,
        margin=dict(l=45, r=20, t=35, b=40),
        xaxis_title="",
        yaxis_title="",
        legend_title_text="",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="right",
            x=1.0,
            font=dict(size=13),
        ),
        font=dict(
            family="Arial, Noto Sans JP, sans-serif",
            size=14,
            color="#282828",
        ),
        paper_bgcolor="white",
        plot_bgcolor="white",
        bargap=0.24,
        bargroupgap=0.08,
    )
    bar.update_xaxes(
        showgrid=False,
        showline=True,
        linecolor="#D9DDE2",
        linewidth=1,
        tickfont=dict(size=14, color="#282828"),
        fixedrange=True,
    )
    bar.update_yaxes(
        rangemode="tozero",
        showgrid=True,
        gridcolor="#ECEFF2",
        gridwidth=1,
        zeroline=False,
        tickfont=dict(size=12, color="#5F6368"),
        fixedrange=True,
    )

    gender_df = df.groupby("性別", as_index=False)["値"].sum()
    gender_df = gender_df[gender_df["値"] > 0]

    pie = None
    if not gender_df.empty:
        pie = go.Figure(
            data=[
                go.Pie(
                    labels=gender_df["性別"],
                    values=gender_df["値"],
                    marker=dict(
                        colors=[
                            GENDER_COLORS.get(g, "#BDBDBD")
                            for g in gender_df["性別"]
                        ],
                        line=dict(color="white", width=1.5),
                    ),
                    texttemplate="%{label}<br>%{value:,}<br>%{percent:.1%}",
                    textposition="inside",
                    textfont=dict(size=19, color="white"),
                    sort=False,
                )
            ]
        )
        pie.update_layout(
            height=560,
            margin=dict(l=20, r=20, t=35, b=20),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.01,
                xanchor="center",
                x=0.5,
                font=dict(size=13),
            ),
            font=dict(
                family="Arial, Noto Sans JP, sans-serif",
                color="#282828",
            ),
            paper_bgcolor="white",
        )

    return bar, pie, build_age_gender_table(df)


def format_placement_name(publisher_platform, platform_position):
    publisher_platform = str(publisher_platform or "").strip().lower()
    platform_position = str(platform_position or "").strip().lower()

    if publisher_platform == "instagram":
        mapping = {
            "feed": "Instagramフィード",
            "story": "Instagramストーリーズ",
            "stories": "Instagramストーリーズ",
            "instagram_stories": "Instagramストーリーズ",
            "reels": "Instagramリール",
            "instagram_reels": "Instagramリール",
            "explore": "Instagram発見",
            "explore_home": "Instagram発見ホーム",
        }
        return mapping.get(
            platform_position,
            f"Instagram {platform_position}" if platform_position else "Instagram",
        )

    if publisher_platform == "facebook":
        mapping = {
            "feed": "Facebookフィード",
            "story": "Facebookストーリーズ",
            "stories": "Facebookストーリーズ",
            "reels": "Facebookリール",
        }
        return mapping.get(
            platform_position,
            f"Facebook {platform_position}" if platform_position else "Facebook",
        )

    if publisher_platform:
        return f"{publisher_platform} {platform_position}".strip()

    return "その他"


def build_placement_dataframe(rows):
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["配置"] = df.apply(
        lambda row: format_placement_name(
            row.get("publisher_platform", ""),
            row.get("platform_position", ""),
        ),
        axis=1,
    )
    for col in [
        "impressions", "reach", "frequency",
        "clicks", "link_clicks", "landing_page_views"
    ]:
        if col not in df:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def build_placement_bar_figure(df, metric_key, metric_label):
    if df.empty:
        return None
    chart_df = df.groupby("配置", as_index=False)[metric_key].sum().sort_values(metric_key, ascending=True)
    chart_df = chart_df[chart_df[metric_key] > 0]
    if chart_df.empty:
        return None
    chart_df["色"] = chart_df["配置"].map(PLACEMENT_COLORS).fillna(PLACEMENT_COLORS["その他"])
    max_value = float(chart_df[metric_key].max() or 1)

    def short_name(name):
        text = str(name).replace("Instagram", "").strip()
        return text or "その他"

    fig = go.Figure()
    for _, row in chart_df.iterrows():
        label = short_name(row["配置"])
        value = int(row[metric_key])
        # Short bars (typically Reels) put the label outside so it remains readable.
        outside = value < max_value * 0.28
        fig.add_trace(go.Bar(
            x=[value], y=[row["配置"]], orientation="h", marker_color=row["色"],
            text=[f"<b>{label}</b>  {value:,}"],
            textposition="outside" if outside else "inside",
            insidetextanchor="start",
            textfont=dict(size=22, color="#282828" if outside else "white"),
            showlegend=False, cliponaxis=False,
        ))
    fig.update_layout(
        height=360, margin=dict(l=12, r=155, t=12, b=34),
        xaxis_title="", yaxis_title="", bargap=0.28,
        font=dict(size=18, color="#282828"), paper_bgcolor="white", plot_bgcolor="white",
        uniformtext_minsize=20, uniformtext_mode="show",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#E4E7EB", zeroline=False, tickfont=dict(size=18,color="#444444"), automargin=True)
    fig.update_yaxes(categoryorder="total ascending", showticklabels=False, showgrid=False, automargin=False)
    return fig


def _placement_rate(value, reach):
    return "―" if reach <= 0 else f"{value / reach * 100:.2f}%"


def _first_existing_value(row, keys, default="―"):
    for key in keys:
        value = row.get(key, None)
        if value is None:
            continue

        text = str(value).strip()
        if text and text.lower() != "nan":
            return text

    return default


def build_placement_table(df, visibility):
    """PPT表示場所詳細。配置 + 選択中の実績指標だけを返す。"""
    if df.empty:
        return pd.DataFrame()

    order = {
        "Instagramフィード": 1,
        "Instagramストーリーズ": 2,
        "Instagramリール": 3,
        "Instagram発見": 4,
        "Instagram発見ホーム": 5,
        "Facebookフィード": 6,
        "Facebookストーリーズ": 7,
        "Facebookリール": 8,
    }

    work = df.copy()
    work["表示順"] = work["配置"].map(order).fillna(999)
    rows = []

    for placement, group in work.sort_values(
        ["表示順", "配置"]
    ).groupby("配置", sort=False):
        impressions = group["impressions"].sum()
        reach = group["reach"].sum()
        clicks = group["clicks"].sum()
        link_clicks = group["link_clicks"].sum()
        landing_page_views = group["landing_page_views"].sum()
        frequency = impressions / reach if reach > 0 else 0

        rows.append({
            "配置": placement,
            "インプレッション": (
                f"{int(impressions):,} ({frequency:.2f})"
                if reach > 0 else f"{int(impressions):,}"
            ),
            "リーチ": f"{int(reach):,}",
            "クリック(すべて)": f"{int(clicks):,} ({_placement_rate(clicks, reach)})",
            "リンククリック": f"{int(link_clicks):,} ({_placement_rate(link_clicks, reach)})",
            "LPビュー": f"{int(landing_page_views):,} ({_placement_rate(landing_page_views, reach)})",
        })

    result = pd.DataFrame(rows)
    metric_columns = [
        ("impressions", "インプレッション"),
        ("reach", "リーチ"),
        ("clicks", "クリック(すべて)"),
        ("link_clicks", "リンククリック"),
        ("landing_page_views", "LPビュー"),
    ]
    columns = ["配置"] + [
        label for key, label in metric_columns
        if visibility.get("metrics", {}).get(key, True)
    ]
    return result[columns]


def build_daily_dataframe(rows):
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    for col in METRIC_CONFIG:
        if col not in df:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df.sort_values("date").reset_index(drop=True)


def build_trend_figure(df, visible_metrics, x_column, x_tickformat=None):
    if df.empty or not visible_metrics:
        return None
    awareness = [k for k in visible_metrics if METRIC_CONFIG[k]["group"] == "awareness"]
    action = [k for k in visible_metrics if METRIC_CONFIG[k]["group"] == "action"]
    both = bool(awareness and action)

    if both:
        fig = make_subplots(
            rows=2, cols=1, shared_xaxes=True,
            vertical_spacing=0.10, row_heights=[0.58, 0.42]
        )
        groups = [(awareness, 1), (action, 2)]
    else:
        fig = make_subplots(rows=1, cols=1)
        groups = [(awareness if awareness else action, 1)]

    for metrics, row_number in groups:
        for key in metrics:
            cfg = METRIC_CONFIG[key]
            fig.add_trace(
                go.Scatter(
                    x=df[x_column],
                    y=df[key],
                    mode="lines+markers",
                    name=cfg["label"],
                    line=dict(color=cfg["color"], width=3),
                    marker=dict(color=cfg["color"], size=7),
                ),
                row=row_number,
                col=1,
            )

    if awareness:
        fig.update_yaxes(title_text="認知指標", rangemode="tozero", row=1, col=1)
    if action:
        row = 2 if both else 1
        fig.update_yaxes(title_text="行動指標", rangemode="tozero", row=row, col=1)

    fig.update_layout(
        height=620,
        margin=dict(l=40, r=30, t=40, b=40),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    if x_tickformat:
        fig.update_xaxes(tickformat=x_tickformat)
    fig.update_yaxes(gridcolor="#EAEAEA")
    return fig


def build_monthly_dataframe(period_result):
    rows = (period_result or {}).get("cumulative_monthly", [])
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["date_start"] = pd.to_datetime(df["date_start"], errors="coerce")
    df = df.dropna(subset=["date_start"])
    for col in [
        "impressions", "reach", "frequency",
        "clicks", "link_clicks", "landing_page_views"
    ]:
        if col not in df:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df = df.sort_values("date_start").reset_index(drop=True)
    if len(df) > 12:
        df = df.tail(12).reset_index(drop=True)
    df["month_label"] = df["date_start"].dt.strftime("%Y/%m")
    return df


def build_monthly_table(df, visible_metrics):
    rows = []
    for key in visible_metrics:
        row = {"指標": METRIC_CONFIG[key]["label"]}
        for _, data_row in df.iterrows():
            month = data_row["month_label"]
            if key == "impressions":
                value = f"{int(data_row['impressions']):,} ({float(data_row['frequency']):.2f})"
            elif key in {"clicks", "link_clicks", "landing_page_views"}:
                rate = _rate(data_row[key], data_row["reach"])
                suffix = f"{rate:.2f}%" if rate is not None else "―"
                value = f"{int(data_row[key]):,} ({suffix})"
            else:
                value = f"{int(data_row[key]):,}"
            row[month] = value
        rows.append(row)
    return pd.DataFrame(rows)


def build_cumulative_gap_figure(cumulative, visibility):
    cumulative = cumulative or {}
    labels, values, colors = [], [], []
    if visibility.get("metrics", {}).get("reach", True):
        labels.append("リーチ")
        values.append(int(cumulative.get("reach", 0) or 0))
        colors.append("#7B2CFF")
    if visibility.get("metrics", {}).get("impressions", True):
        labels.append("インプレッション")
        values.append(int(cumulative.get("impressions", 0) or 0))
        colors.append("#FF6B00")
    if not labels:
        return None

    fig = go.Figure()
    for label, value, color in zip(labels, values, colors):
        fig.add_trace(go.Bar(
            x=[value], y=[label], orientation="h", marker_color=color,
            text=[f"<b>{label}</b>  {value:,}"], textposition="inside",
            insidetextanchor="start", textfont=dict(size=22, color="white"),
            showlegend=False, cliponaxis=False,
        ))
    fig.update_layout(
        height=260, margin=dict(l=12, r=35, t=10, b=25), showlegend=False,
        plot_bgcolor="white", paper_bgcolor="white", bargap=0.38,
        font=dict(size=18, color="#282828"), uniformtext_minsize=20, uniformtext_mode="show",
    )
    fig.update_xaxes(rangemode="tozero", gridcolor="rgba(180,180,180,0.18)", tickfont=dict(size=17))
    fig.update_yaxes(showticklabels=False, showgrid=False, automargin=False)
    return fig
