from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

# ----------------------------
# スライド
# ----------------------------

SLIDE_WIDTH = Inches(13.333)
SLIDE_HEIGHT = Inches(7.5)

# ----------------------------
# フォント
# ----------------------------

FONT_NAME = "Yu Gothic"

TITLE_SIZE = Pt(24)
HEADER_SIZE = Pt(15)
BODY_SIZE = Pt(10)
VALUE_SIZE = Pt(18)
SLIDE_TITLE_SIZE = Pt(24)
SLIDE_SUBTITLE_SIZE = Pt(10)
SECTION_TITLE_SIZE = Pt(14)
# ----------------------------
# 色
# ----------------------------

COLOR_TEXT = RGBColor(40, 40, 40)
COLOR_SUB = RGBColor(120, 120, 120)

COLOR_BORDER = RGBColor(220, 220, 220)
COLOR_HEADER = RGBColor(245, 245, 245)

COLOR_SECTION = RGBColor(30, 76, 140)

# ----------------------------
# 余白
# ----------------------------

PAGE_LEFT = Inches(0.45)
PAGE_TOP = Inches(0.35)

# 互換用（後で削除予定）
MARGIN_X = PAGE_LEFT
MARGIN_TOP = PAGE_TOP
SUBTITLE_SIZE = BODY_SIZE

# ----------------------------
# カード
# ----------------------------

CARD_WIDTH = Inches(2.5)
CARD_HEIGHT = Inches(0.8)
CARD_GAP = Inches(0.2)

CARD_LABEL_SIZE = Pt(9)
CARD_VALUE_SIZE = Pt(22)
CARD_DELTA_SIZE = Pt(11)

# ----------------------------
# セクション
# ----------------------------

SECTION_TITLE_HEIGHT = Inches(0.3)
SECTION_GAP = Inches(0.4)

# ----------------------------
# テーブル
# ----------------------------

TABLE_HEADER_SIZE = Pt(11)
TABLE_BODY_SIZE = Pt(11)

TABLE_ROW_HEIGHT = Inches(0.30)
TABLE_HEADER_HEIGHT = Inches(0.34)

# 男性色 #4000B8 を基準にした配色
TABLE_HEADER_FILL = RGBColor(64, 0, 184)
TABLE_HEADER_TEXT_COLOR = RGBColor(255, 255, 255)

# 通常行
TABLE_BODY_FILL = RGBColor(255, 255, 255)

# 交互行：ごく薄い紫
TABLE_ALT_ROW_FILL = RGBColor(244, 240, 255)

# 合計行：交互行より少し濃い紫
TABLE_TOTAL_FILL = RGBColor(226, 216, 255)

# 罫線
TABLE_BORDER_COLOR = RGBColor(224, 218, 240)



# ----------------------------
# グラフ
# ----------------------------

CHART_TITLE_SIZE = Pt(18)

# ----------------------------
# Summaryページ座標
# ----------------------------

SUMMARY_CONDITION_TITLE_TOP = Inches(1.35)
SUMMARY_CONDITION_CARD_TOP = Inches(1.75)

SUMMARY_METRIC_TITLE_TOP = Inches(1.55)
SUMMARY_METRIC_CARD_TOP = Inches(1.90)

SUMMARY_CUMULATIVE_TITLE_TOP = Inches(3.00)
SUMMARY_CUMULATIVE_CARD_TOP = Inches(3.35)

SUMMARY_PLACEMENT_TITLE_TOP = Inches(4.55)
SUMMARY_PLACEMENT_TABLE_TOP = Inches(4.90)

SUMMARY_PLACEMENT_TABLE_WIDTH = Inches(12.2)
SUMMARY_PLACEMENT_TABLE_HEIGHT = Inches(1.0)

SUMMARY_INFO_CARD_TOP = Inches(0.25)

SUMMARY_START_DATE_LEFT = Inches(8.35)
SUMMARY_ELAPSED_DAYS_LEFT = Inches(10.75)

SUMMARY_INFO_CARD_WIDTH = Inches(2.1)
SUMMARY_INFO_CARD_HEIGHT = Inches(0.75)

# ----------------------------
# Detailページ座標・サイズ
# ----------------------------

DETAIL_TITLE_WIDTH = Inches(8)
DETAIL_TITLE_HEIGHT = Inches(0.5)

DETAIL_EMPTY_LEFT = Inches(0.7)
DETAIL_EMPTY_TOP = Inches(1.3)
DETAIL_EMPTY_WIDTH = Inches(6)
DETAIL_EMPTY_HEIGHT = Inches(0.5)

DETAIL_TABLE_LEFT = Inches(0.4)
DETAIL_TABLE_TOP = Inches(1.1)
DETAIL_TABLE_WIDTH = Inches(12.5)
DETAIL_TABLE_HEIGHT = Inches(5.8)

# ----------------------------
# Metric Analysisページ座標・サイズ
# ----------------------------

METRIC_TITLE_WIDTH = Inches(8)
METRIC_TITLE_HEIGHT = Inches(0.5)

METRIC_GENDER_LEFT = Inches(8.3)
METRIC_AGE_TOP = Inches(0.9)
METRIC_GENDER_TOP = Inches(1.4)

METRIC_AGE_WIDTH = Inches(7.0)
METRIC_GENDER_WIDTH = Inches(4.2)

METRIC_AGE_LEFT = Inches(0.4)

METRIC_TABLE_TITLE_TOP = Inches(4.65)
METRIC_TABLE_TITLE_WIDTH = Inches(3.0)
METRIC_TABLE_TITLE_HEIGHT = Inches(0.3)

METRIC_TABLE_LEFT = Inches(0.4)
METRIC_TABLE_TOP = Inches(5.05)
METRIC_TABLE_WIDTH = Inches(12.5)
METRIC_TABLE_HEIGHT = Inches(1.8)

# ----------------------------
# Chartページ座標・サイズ
# ----------------------------

CHART_TITLE_WIDTH = Inches(8)
CHART_TITLE_HEIGHT = Inches(0.5)

CHART_SINGLE_LEFT = Inches(0.7)
CHART_SINGLE_TOP = Inches(1.1)
CHART_SINGLE_WIDTH = Inches(11.9)
CHART_SINGLE_HEIGHT = Inches(5.9)

CHART_EMPTY_LEFT = Inches(0.7)
CHART_EMPTY_TOP = Inches(1.5)
CHART_EMPTY_WIDTH = Inches(6)
CHART_EMPTY_HEIGHT = Inches(0.5)

CHART_MULTI_LAYOUTS = {
    4: [
        (Inches(0.7), Inches(1.1), Inches(5.7), Inches(2.7)),
        (Inches(6.9), Inches(1.1), Inches(5.7), Inches(2.7)),
        (Inches(0.7), Inches(4.1), Inches(5.7), Inches(2.7)),
        (Inches(6.9), Inches(4.1), Inches(5.7), Inches(2.7)),
    ],
    5: [
        (Inches(1.4), Inches(1.1), Inches(5.1), Inches(2.4)),
        (Inches(6.8), Inches(1.1), Inches(5.1), Inches(2.4)),
        (Inches(0.4), Inches(4.0), Inches(4.1), Inches(2.3)),
        (Inches(4.6), Inches(4.0), Inches(4.1), Inches(2.3)),
        (Inches(8.8), Inches(4.0), Inches(4.1), Inches(2.3)),
    ],
}

CHART_MULTI_DEFAULT_LAYOUT = [
    (Inches(0.8), Inches(1.2), Inches(11.5), Inches(5.6)),
]