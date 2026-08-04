import plotly.express as px


def create_awareness_chart(daily_summary, awareness_chart_columns):

    if not awareness_chart_columns:
        return None

    fig = px.line(
        daily_summary,
        x="レポート開始日",
        y=awareness_chart_columns,
        markers=True,
        title="デイリー認知推移"
    )

    fig.update_traces(line=dict(width=3))

    color_map = {
        "インプレッション": "#4F81BD",
        "リーチ": "#1F497D",
    }

    for trace in fig.data:
        if trace.name in color_map:
            trace.line.color = color_map[trace.name]

    return fig


def create_action_chart(daily_summary, action_chart_columns):

    if not action_chart_columns:
        return None

    fig = px.line(
        daily_summary,
        x="レポート開始日",
        y=action_chart_columns,
        markers=True,
        title="デイリー行動推移"
    )

    fig.update_traces(line=dict(width=3))

    color_map = {
        "クリック(すべて)": "#808080",
        "リンククリック": "#F79646",
        "ランディングページビュー": "#00B050",
    }

    for trace in fig.data:
        if trace.name in color_map:
            trace.line.color = color_map[trace.name]

    return fig