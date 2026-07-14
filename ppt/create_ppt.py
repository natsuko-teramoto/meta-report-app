from pathlib import Path

from ppt.common.layout import create_presentation
from ppt.pages.summary import add_summary_slide
from ppt.pages.chart_page import add_chart_slide, add_multi_chart_slide
from ppt.pages.detail import add_detail_slide
from ppt.pages.metric_analysis import add_metric_analysis_slide
from utils.chart_export import get_chart_file_name

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


def create_meta_report_ppt(report):
    prs = create_presentation()

    add_summary_slide(prs, report)

    if report["pages"]["awareness"]:
        add_chart_slide(
            prs,
            "認知推移",
            "output/images/awareness.png",
        )

    if report["pages"]["action"]:
        add_chart_slide(
            prs,
            "行動推移",
            "output/images/action.png",
        )

    for metric in report["analysis_metrics"]:

        safe_metric = get_chart_file_name(metric)

        analysis = {
            "gender_image": f"output/images/gender_{safe_metric}.png",
            "age_image": f"output/images/age_{safe_metric}.png",
            "table": report["analysis_tables"].get(metric),
        }

        add_metric_analysis_slide(
            prs,
            f"{metric}分析",
            analysis,
        )


#    if report["pages"]["gender"]:
#        add_multi_chart_slide(
#            prs,
#            "男女分析",
#            [
#                "output/images/gender_インプレッション.png",
#                "output/images/gender_リーチ.png",
#                "output/images/gender_クリックすべて.png",
#                "output/images/gender_リンククリック.png",
#                "output/images/gender_ランディングページビュー.png",
#            ],
#        )     

#    if report["pages"]["age"]:
#        add_multi_chart_slide(
#            prs,
#            "年齢分析",
#            [
#                "output/images/age_インプレッション.png",
#                "output/images/age_リーチ.png",
#                "output/images/age_クリックすべて.png",
#                "output/images/age_リンククリック.png",
#                "output/images/age_ランディングページビュー.png",
#            ],
#        )

    if report["pages"]["detail"]:
        add_detail_slide(prs, report)


    file_name = f"Meta広告レポート_{report['month']}.pptx"
    save_path = OUTPUT_DIR / file_name

    prs.save(save_path)

    return save_path


if __name__ == "__main__":
    from report.report_builder import build_report

    test_report = build_report(
        selected_month="2026年6月",
        selected_campaign="テスト歯科医院"
    )

    path = create_meta_report_ppt(test_report)
    print(f"保存しました：{path}")