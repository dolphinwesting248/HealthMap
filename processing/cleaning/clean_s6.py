"""
S6 清洗: 国家统计局省级社会经济指标
"""
import pandas as pd
from pathlib import Path

from utils import CLEANED_DIR, normalize_province, log

RAW_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "raw" / "s6_stats"


def clean_s6():
    print("\n[S6] 清洗省级社会经济数据...")

    csv_files = sorted(RAW_DIR.glob("nbs_*.csv"))
    if not csv_files:
        log("未找到原始数据文件")
        return

    log(f"找到 {len(csv_files)} 个文件")

    all_dfs = []
    for f in csv_files:
        df = pd.read_csv(f, dtype=str)
        domain = f.stem.replace("nbs_", "").split("_")[0] if "_" in f.stem else f.stem
        df["domain"] = domain
        all_dfs.append(df)
        log(f"  {f.name}: {len(df)} 行")

    df = pd.concat(all_dfs, ignore_index=True)
    log(f"合并后: {df.shape[0]} 行 × {df.shape[1]} 列")

    # 1. 统一省份名
    df["province"] = df["province"].apply(normalize_province)

    # 2. 过滤时间: 2023-2025
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    na_year = df["year"].isna().sum()
    df = df[(df["year"] >= 2023) & (df["year"] <= 2025)]
    log(f"过滤 2023-2025: {df.shape[0]} 行 (年份无效删除: {na_year})")

    # 3. 清理 value → 数值
    df["value_clean"] = df["value"].str.replace(",", "", regex=False).str.strip()
    df["value_num"] = pd.to_numeric(df["value_clean"], errors="coerce")

    # 4. 缺失值分析
    total = len(df)
    empty_mask = df["value"].str.strip() == ""
    abnormal_mask = df["value_num"].isna() & ~empty_mask
    na_pct = df["value_num"].isna().sum() / total * 100 if total > 0 else 0

    log(f"--- 缺失值分析 ---")
    log(f"  总行数: {total}")
    log(f"  value为空(未发布): {empty_mask.sum()} 行")
    log(f"  value非数字(异常): {abnormal_mask.sum()} 行")
    log(f"  value_num 缺失率: {na_pct:.1f}%")

    # 5. 去重
    before = len(df)
    df = df.drop_duplicates(subset=["province", "year", "indicator", "domain"])
    log(f"去重: {before} → {len(df)} 行")

    # 6. 质量检查
    log(f"--- 数据质量报告 ---")
    log(f"省份数: {df['province'].nunique()}")
    log(f"领域数: {df['domain'].nunique()}")
    for year in sorted(df["year"].dropna().unique()):
        year_total = len(df[df["year"] == year])
        year_na = df[df["year"] == year]["value_num"].isna().sum()
        log(f"  {int(year)}年: {year_total} 行, 缺失 {year_na} 行 ({year_na/year_total*100:.1f}%)")

    out = CLEANED_DIR / "s6_economic_provincial.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")
    log(f"输出: {df.shape[0]} 行 × {df.shape[1]} 列 → {out}")
    return df


if __name__ == "__main__":
    clean_s6()
