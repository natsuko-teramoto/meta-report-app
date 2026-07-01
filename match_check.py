import pandas as pd
from rapidfuzz import process, fuzz
from pathlib import Path

# ===== ファイル設定 =====
MASTER_FILE = "user_master_20260623.xlsx"
META_DIR = Path("data/daily")
OUTPUT_FILE = "match_check_result.xlsx"

# ===== マスタ読み込み =====
master_df = pd.read_excel(MASTER_FILE)

# E列を広告セット名として使う
master_names = master_df.iloc[:, 4].dropna().astype(str).str.strip().unique().tolist()

# ===== Metaデータ読み込み =====
meta_files = list(META_DIR.glob("*.xlsx"))

meta_dfs = []
for file in meta_files:
    df = pd.read_excel(file)
    meta_dfs.append(df)

meta_df = pd.concat(meta_dfs, ignore_index=True)

meta_names = meta_df["広告セット名"].dropna().astype(str).str.strip().unique().tolist()

# ===== 突合チェック =====
results = []

for meta_name in meta_names:
    if meta_name in master_names:
        results.append({
            "Meta広告セット名": meta_name,
            "一致状況": "完全一致",
            "マスタ候補": meta_name,
            "一致率": 100
        })
    else:
        best_match = process.extractOne(
            meta_name,
            master_names,
            scorer=fuzz.ratio
        )

        if best_match:
            candidate, score, _ = best_match
        else:
            candidate, score = "", 0

        results.append({
            "Meta広告セット名": meta_name,
            "一致状況": "要確認",
            "マスタ候補": candidate,
            "一致率": score
        })

result_df = pd.DataFrame(results)

# ===== マスタにあるけどMetaにないもの =====
missing_in_meta = []

for master_name in master_names:
    if master_name not in meta_names:
        best_match = process.extractOne(
            master_name,
            meta_names,
            scorer=fuzz.ratio
        )

        if best_match:
            candidate, score, _ = best_match
        else:
            candidate, score = "", 0

        missing_in_meta.append({
            "マスタE列": master_name,
            "一致状況": "Metaに存在しない",
            "Meta候補": candidate,
            "一致率": score
        })

missing_df = pd.DataFrame(missing_in_meta)

# ===== Excel出力 =====
with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
    result_df.to_excel(writer, sheet_name="Meta→マスタ突合", index=False)
    missing_df.to_excel(writer, sheet_name="マスタ→Meta未一致", index=False)

print("突合チェック完了")
print(f"出力ファイル：{OUTPUT_FILE}")