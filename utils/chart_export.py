from pathlib import Path

PLOTLY_FONT_FAMILY = (
    "Noto Sana CJK JP,"
    "Noto Sana JP,"
    "Yu Gothic,"
    "Meiryo,"
    "sans-serif"
)

IMAGE_DIR = Path("output/images")

def get_chart_file_name(name):
    return (
        name
        .replace("/", "_")
        .replace("\\", "_")
        .replace("(", "")
        .replace(")", "")
    )


def save_chart(
    fig,
    name,
    width=1200,
    height=700,
    scale=2,
):
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    safe_name = get_chart_file_name(name)
    file_path = IMAGE_DIR / f"{safe_name}.png"

    fig.write_image(
        file_path,
        width=width,
        height=height,
        scale=scale,
    )

    return file_path


def generate_ppt_images(chart_figures):
    """
    ブラウザ表示用に作成済みのPlotly Figureを、
    PowerPoint用PNGとして一括保存する。

    chart_figuresの形式：
    {
        "画像名": {
            "fig": Plotly Figure,
            "width": 1200,
            "height": 700,
            "scale": 2,
        }
    }
    """
    saved_files = []

    for image_name, settings in chart_figures.items():
        fig = settings.get("fig")

        if fig is None:
            continue
        fig.update_layout(
            font=dict(
                family=PLOTLY_FONT_FAMILY,
            ),
            legend=dict(
                font=dict(
                    family=PLOTLY_FONT_FAMILY,
                ),
                title_font=dict(
                    family=PLOTLY_FONT_FAMILY,
                ),
            ),
        )

        fig.update_xaxes(
            tickfont=dict(
                family=PLOTLY_FONT_FAMILY,
            ),
            title_font=dict(
                family=PLOTLY_FONT_FAMILY,
            ),
        )

        fig.update_yaxes(
            tickfont=dict(
                family=PLOTLY_FONT_FAMILY,
            ),
            title_font=dict(
                family=PLOTLY_FONT_FAMILY,
            ),
        )


        saved_files.append(
            save_chart(
                fig=fig,
                name=image_name,
                width=settings.get("width", 1200),
                height=settings.get("height", 700),
                scale=settings.get("scale", 2),
            )
        )

    return saved_files