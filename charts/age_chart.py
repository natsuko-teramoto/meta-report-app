import pandas as pd
import plotly.express as px


def build_age_gender_df(
    daily_filtered_df,
    metric,
    age_order,
):
    age_gender_df = (
        daily_filtered_df
        .groupby(["年齢", "性別"], as_index=False)[metric]
        .sum()
    )

    total_value = age_gender_df[metric].sum()

    if total_value > 0:
        age_gender_df["割合"] = (
            age_gender_df[metric] / total_value * 100
        )
    else:
        age_gender_df["割合"] = 0

    age_gender_df["性別"] = age_gender_df["性別"].replace(
        {
            "male": "男性",
            "female": "女性",
            "unknown": "不明",
        }
    )

    age_gender_df["年齢"] = pd.Categorical(
        age_gender_df["年齢"],
        categories=age_order,
        ordered=True,
    )

    age_gender_df = age_gender_df.sort_values(
        ["年齢", "性別"]
    )

    return age_gender_df

def build_age_gender_table_df(
    daily_filtered_df,
    metric,
    age_order,
):
    age_gender_df = build_age_gender_df(
        daily_filtered_df,
        metric,
        age_order,
    )

    table_df = (
        age_gender_df
        .pivot(
            index="性別",
            columns="年齢",
            values=[metric, "割合"],
        )
        .fillna(0)
    )

    rows = []

    for gender in ["女性", "男性"]:

        if gender not in table_df.index:
            continue

        count_row = {"項目": f"{gender} 数"}
        ratio_row = {"項目": f"{gender} 割合"}

        for age in age_order:
            count = (
                int(round(table_df.loc[gender, (metric, age)]))
                if (metric, age) in table_df.columns
                else 0
            )

            ratio = (
                table_df.loc[gender, ("割合", age)]
                if ("割合", age) in table_df.columns
                else 0
            )

            count_row[age] = count
            ratio_row[age] = f"{ratio:.1f}%"

        rows.append(count_row)
        rows.append(ratio_row)

    # 年齢別の合計数
    total_by_age = (
        age_gender_df
        .groupby("年齢", observed=False)[metric]
        .sum()
        .reindex(age_order, fill_value=0)
    )

    grand_total = total_by_age.sum()

    total_count_row = {"項目": "合計 数"}
    total_ratio_row = {"項目": "合計 割合"}

    for age in age_order:
        age_total = total_by_age.get(age, 0)

        total_count_row[age] = int(round(age_total))

        if grand_total > 0:
            total_ratio_row[age] = (
                f"{age_total / grand_total * 100:.1f}%"
            )
        else:
            total_ratio_row[age] = "0.0%"

    rows.append(total_count_row)
    rows.append(total_ratio_row)

    return pd.DataFrame(
        rows,
        columns=["項目"] + age_order,
    )

def create_age_chart(
    daily_filtered_df,
    metric,
    display_name,
    age_order,
    gender_color_map,
):
    age_gender_df = build_age_gender_df(
        daily_filtered_df,
        metric,
        age_order,
    )

    age_gender_df["表示"] = age_gender_df.apply(
        lambda row: (
            f'{row[metric]:,.0f}'
            f'<br>{row["割合"]:.1f}%'
        ),
        axis=1,
    )

    fig = px.bar(
        age_gender_df,
        x="年齢",
        y=metric,
        color="性別",
        barmode="group",
        text="表示",
        category_orders={
            "年齢": age_order,
            "性別": ["男性", "女性", "不明"],
        },
        color_discrete_map=gender_color_map,
    )

    fig.update_layout(
        title_text="",
        yaxis_title="",
        xaxis_title="",
        showlegend=True,
        bargap=0.35,
        bargroupgap=0.15,
    )

    fig.update_traces(
        textposition="outside"
    )

    return fig