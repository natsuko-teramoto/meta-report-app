# Meta広告レポート｜実装仕様・引き継ぎ

最終コード調査：2026-10-27  
対象：`natsuko-teramoto/meta-report-app`（GitHubの既定ブランチ上のコード）  
状態：**コード確認済み／本番動作・運用確定は未検証**。本書は既存仕様を変更する指示ではない。

## 1. 目的と管理上の位置づけ

広告検索、レポート表示、PowerPoint出力、広告変更依頼の機能を引き継ぐため、現在のコードで確認できる構成・計算方法・未確認事項をまとめる。

- **実装の正本**：このリポジトリのPythonコード。
- **システム間連携と全体進捗の正本**：`natsuko-teramoto/meta-ads-management`。データ連携は同リポジトリ `docs/01_data_flow.md` を参照する。
- **障害対応**：同リポジトリ `manuals/04_streamlit_troubleshooting.md` を参照する。
- 認証情報、トークン、秘密鍵をGitHubに保存しない。

## 2. 起動・データフロー

Streamlit Cloudのアプリ一覧で確認された設定は `meta-report-app / main / app.py`。GitHub最新コードと本番実行内容の完全一致は未検証。

1. `app.py` が `services/ad_search.py` から検索用データを取得。
2. `data_sources/master_source.py` がGoogleスプレッドシート「Meta広告管理」から「Meta顧客マスタ」「施設マスタ」「案件マスタ」「Meta配信履歴」「レガシー広告一覧」を取得。
3. `services/ad_search.py` が案件ID・Meta顧客ID・施設IDで情報を結合し、API広告とレガシー広告を共通の検索データにまとめる。レガシー広告は案件IDがある行を対象とするコード。
4. `app.py` が「広告変更依頼」「広告変更依頼明細」を取得し、`services/change_request_service.py` の `apply_completed_changes_to_ad_data` を適用。
5. `ui/ad_search_view.py` で広告検索、選択、期間指定を行う。検索フォームには顧客・都道府県・担当者・業種・訴求内容の選択UIがある。2件比較用の選択・表示コードがある。
6. `services/period.py` で集計期間を確定。
7. API広告は `services/meta_api_source.py` → `services/report_service.py`、レガシー広告は `services/legacy_report_service.py` で実績データを生成。
8. `ui/report_view.py` で画面表示、`ui/report_export.py` → `ppt/create_api_ppt.py` でPPT作成。

## 3. データ取得元と認証

- Google Sheets：`data_sources/master_source.py` が `gspread` を使用。ローカルは `credentials.json` が存在すれば参照し、Cloudは `st.secrets["gcp_service_account"]` を使用。
- API広告実績：`services/meta_api_source.py` がMeta Graph APIに問い合わせ、`st.secrets["META_ACCESS_TOKEN"]` を参照する。トークン値はコードに記録しない。
- レガシー広告実績：`services/legacy_report_service.py` が `data/monthly/`、`data/monthly_place/`、`data/daily_age_gender/` 配下の `.xlsx` を読み込む実装。
- スプレッドシートのマスタと広告実績は異なる取得経路。レガシーExcelの更新手順は未確認。

## 4. 期間の確定ルール（`services/period.py`）

| モード | 対象期間 | 比較期間 | 累計期間 |
|---|---|---|---|
| 月次 `month` | 指定月の1日～末日 | 前月1日～末日 | 広告掲載開始日～対象月末 |
| 任意 `custom` | 指定開始日～終了日 | 対象開始日の直前、同じ日数 | 広告掲載開始日～対象終了日 |

- 対象期間が掲載開始日前のみの場合はエラー。
- 期間の途中から掲載開始する指定は許可するコード。
- `app.py` は広告行の「配信開始」を期間計算の掲載開始日として読み込む。

## 5. 指標と表示（コード確認）

`services/report_service.py` のAPI広告集計は対象期間・比較期間・累計期間の基本指標を作成する。主要指標はインプレッション、リーチ、フリークエンシー、クリック、リンククリック、LPビュー。

- クリック率：クリック数 ÷ リーチ × 100。
- リンククリック率：リンククリック数 ÷ リーチ × 100。
- LPビュー率：LPビュー数 ÷ リーチ × 100。
- フリークエンシーはMeta APIが返す値を使用。
- 指定期間のリーチは期間単位のAPI取得値を使用し、日別リーチを合算して作らない。
- `ui/report_view.py` は基本情報、期間・累計指標、期間・累計の年齢性別、配信面、日次推移、累計リーチ／インプレッション、月次推移を呼び出す。
- 前期間比の表示計算は `services/report_export_service.py` にも実装されている。画面全体との計算一致は未検証。

## 6. 表示設定とPowerPoint

- `ui/report_sidebar.py` が基本情報、数値指標、年齢性別、配信面、日次・累計・月次グラフの表示チェックボックスを提供する。
- `ui/report_config.py` が表示設定を `st.session_state` に保持し、`get_report_view_snapshot()` で出力用に取得する。
- 初期状態で非表示の設定がある：訴求内容・配信エリア・年齢・性別・リンククリック・LPビュー。
- `ui/report_export.py` は表示設定のスナップショットを `ppt/create_api_ppt.py` に渡す。表示設定変更後は、以前の設定で生成したPPTのダウンロードボタンを出さない処理がある。
- 2件比較時はレポート1・2それぞれにPPT作成ボタンがある。
- `ppt/create_api_ppt.py` のファイル名形式は `【Instagram広告レポート】{顧客名} 様_{訴求内容}（{開始日}～{終了日}）.pptx`。
- **注意**：画面で非表示にしたすべての項目がPPTからも完全に除外されるかは、出力結果を用いた検証が必要。

## 7. 広告変更依頼

- `ui/change_request_view.py` に変更依頼フォームのコードがある。
- `services/change_request_service.py` にGoogle Sheets「広告変更依頼」「広告変更依頼明細」への登録処理がある。
- `app.py` は完了済み変更を広告検索・表示用データに反映する処理を呼び出す。
- 入力項目の最終運用ルール、GASとの依存関係、登録・完了の本番動作は未検証。

## 8. 主要ファイル一覧

| ファイル | 役割 |
|---|---|
| `app.py` | 画面遷移、データ取得、期間結果、PPT操作の呼び出し |
| `data_sources/master_source.py` | Google Sheetsのマスタ・依頼データ取得 |
| `services/ad_search.py` | API／レガシー広告の検索データ結合 |
| `services/change_request_service.py` | 変更依頼の登録・完了変更反映 |
| `services/period.py` | 対象・比較・累計期間の算出 |
| `services/meta_api_source.py` | Meta APIへの問い合わせ |
| `services/report_service.py` | API広告のレポート集計 |
| `services/legacy_report_service.py` | レガシーExcelからのレポート集計 |
| `ui/ad_search_view.py` | 広告検索・期間選択画面 |
| `ui/report_view.py` | レポート画面の組み立て |
| `ui/report_sidebar.py`・`ui/report_config.py` | 表示設定 |
| `ui/report_export.py`・`ppt/create_api_ppt.py` | PPT生成・ダウンロード |

## 9. 引き継ぎ時の確認事項（未完了と断定しない）

- 本番のコードとGitHubの最新コードの一致、デプロイ設定。
- レガシーExcelの実データ更新・投入の運用。
- 検索・変更依頼・レポート表示・PPTの本番動作と表示の整合性。
- GASとStreamlitの依存関係の詳細。
- 最新の開発進捗（完了・保留・未着手）は全体管理リポジトリの記録と照合する。

## 10. 変更時のルール

変更前に既存コード・設計・影響範囲を確認し、仕様を推測で補わない。原因未確認の場当たり修正は禁止。コード変更と本番反映は別作業として扱い、明示的な承認なしに実施しない。
