import plotly.express as px


def create_gender_chart(
    daily_filtered_df,
    metric,
    gender_label_map,
    gender_color_map,
):
    gender_df = (
        daily_filtered_df
        .groupby("性別", as_index=False)[metric]
        .sum()
    )

    gender_df["性別"] = gender_df["性別"].replace(
        gender_label_map
    )

    fig = px.pie(
        gender_df,
        names="性別",
        values=metric,
        color="性別",
        color_discrete_map=gender_color_map,
    )

    fig.update_traces(
        textposition="inside",
        texttemplate="%{label}<br>%{value:,.0f}<br>%{percent}",
    )

    fig.update_layout(
        title_text="",
        showlegend=True,
        legend=dict(
            orientation="h",
            y=-0.12,
            x=0.5,
            xanchor="center",
        ),
        margin=dict(l=10, r=10, t=20, b=40),
        font=dict(size=18),
    )

    return fig