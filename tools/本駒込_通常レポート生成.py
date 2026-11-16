"""緊急時の単発ローカルPPT生成（本駒込2026年10月の動作実績）。既存コードは変更しない。"""
from datetime import date
from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parent.parent
if not (ROOT / "ppt" / "create_api_ppt.py").exists():
    raise SystemExit("このファイルは meta-report-app の tools/ に置いて実行してください。")
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

from services.period import build_month_period
from services.legacy_report_service import build_legacy_period_result
from ppt.create_api_ppt import create_api_meta_report_ppt

names = ["本駒込耳鼻咽喉科（医院紹介）", "【再出稿】本駒込耳鼻咽喉科（医院紹介）"]
ad = {
    "キャンペーン名": names[0],
    "同一案件キャンペーン名": names,
    "案件名": "本駒込耳鼻咽喉科",
    "顧客名": "本駒込耳鼻咽喉科",
    "施設名": "本駒込耳鼻咽喉科",
    "訴求内容": "医院紹介",
    "ad_id": "A000122_A000290",
    "データ種別": "LEGACY",
}
# 正式な配信開始日が未確認。累計期間の起点は仮設定。
publication_start = date(2026, 1, 1)
ad["配信開始"] = publication_start.strftime("%Y/%m/%d")
ad["レポート配信開始日"] = ad["配信開始"]
period = build_month_period(2026, 10, publication_start)
result = build_legacy_period_result(ad, period)

basic = ["customer_name", "publication_start", "cumulative_days", "report_period", "appeal", "area", "age", "gender"]
metrics = ["impressions", "reach", "clicks", "link_clicks", "landing_page_views"]
sections = ["period_age_gender", "cumulative_age_gender", "daily_trend", "reach_impression_gap", "monthly_trend"]
visibility = {
    "basic": {k: k not in {"appeal", "area", "age", "gender"} for k in basic},
    "metrics": {k: k not in {"link_clicks", "landing_page_views"} for k in metrics},
    "sections": {k: True for k in sections},
    "placement": {"chart": True, "detail": True},
}
output = create_api_meta_report_ppt(ad, period, result, visibility, report_key="A000122_A000290")
print("\n完了：", output.resolve())
