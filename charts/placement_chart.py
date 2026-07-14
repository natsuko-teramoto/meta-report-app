def create_placement_summary(monthly_place_df, selected_campaign):
    place_filtered = monthly_place_df[
        monthly_place_df["キャンペーン名"] == selected_campaign
    ].copy()

    place_summary = (
        place_filtered
        .groupby(
            ["配置", "キャンペーンの配信", "アトリビューション設定"],
            as_index=False
        )
        .agg({
            "インプレッション": "sum",
            "リーチ": "sum",
            "クリック(すべて)": "sum",
            "リンククリック": "sum",
            "ランディングページビュー": "sum"
        })
    )

    place_summary = place_summary.rename(
        columns={
            "キャンペーンの配信": "配信",
            "ランディングページビュー": "LPビュー",
            "クリック(すべて)": "クリック(すべて)"
        }
    )

    place_summary["クリック(すべて)"] = place_summary.apply(
        lambda row: (
            f'{row["クリック(すべて)"]:,.0f} ({row["クリック(すべて)"] / row["リーチ"] * 100:.2f}%)'
            if row["リーチ"] > 0 else f'{row["クリック(すべて)"]:,.0f}'
        ),
        axis=1
    )

    place_summary["リンククリック"] = place_summary.apply(
        lambda row: (
            f'{row["リンククリック"]:,.0f} ({row["リンククリック"] / row["リーチ"] * 100:.2f}%)'
            if row["リーチ"] > 0 else f'{row["リンククリック"]:,.0f}'
        ),
        axis=1
    )

    place_summary["LPビュー"] = place_summary.apply(
        lambda row: (
            f'{row["LPビュー"]:,.0f} ({row["LPビュー"] / row["リーチ"] * 100:.2f}%)'
            if row["リーチ"] > 0 else f'{row["LPビュー"]:,.0f}'
        ),
        axis=1
    )

    place_summary["インプレッション"] = place_summary.apply(
        lambda row: (
            f'{row["インプレッション"]:,.0f} ({row["インプレッション"] / row["リーチ"]:.2f})'
            if row["リーチ"] > 0 else f'{row["インプレッション"]:,.0f}'
        ),
        axis=1
    )

    place_summary["リーチ"] = place_summary["リーチ"].map(
        lambda x: f"{x:,.0f}"
    )

    return place_summary
