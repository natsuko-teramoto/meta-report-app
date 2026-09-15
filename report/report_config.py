# 配信用Meta広告レポートの標準設定
# 一斉配信用PPT/PDFはこの設定だけを参照します。

DELIVERY_REPORT_CONFIG = {
    # 配信結果・表示場所・掲載開始からの詳細で使う指標
    "summary_metrics": [
        "インプレッション",
        "リーチ",
        "クリック(すべて)",
    ],

    # 年齢・性別分析で使う指標
    "analysis_metrics": [
        "インプレッション",
        "リーチ",
        "クリック(すべて)",
    ],

    # 年齢・性別分析：掲載開始からの累計
    "show_cumulative_analysis": True,

    # 表・グラフ
    "show_place": True,
    "show_detail": True,
    "show_awareness": False,
    "show_action": False,

    # 現在の配信用レポートでは累計推移も出さない
    "show_cumulative_awareness": False,
    "show_cumulative_action": False,
}
