"""
S7 清洗: 人口普查 + World Bank 人口数据
"""
import pandas as pd
from pathlib import Path

from utils import CLEANED_DIR, normalize_province, log

RAW_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "raw" / "s7_census"


def clean_s7():
    print("\n[S7] 清洗人口数据...")

    # 1. 省级人口普查
    census_file = RAW_DIR / "census_7_province_population.csv"
    if census_file.exists():
        df_census = pd.read_csv(census_file, dtype=str)
        log(f"人口普查: {len(df_census)} 行")
        df_census["province"] = df_census["province"].apply(normalize_province)
        df_census["year"] = pd.to_numeric(df_census["year"], errors="coerce")
        df_census["population"] = pd.to_numeric(df_census["population"], errors="coerce")
    else:
        df_census = pd.DataFrame()
        log("人口普查文件不存在")

    # 2. World Bank 人口指标
    wb_file = RAW_DIR / "worldbank_population_china.csv"
    if wb_file.exists():
        df_wb = pd.read_csv(wb_file, dtype=str)
        log(f"World Bank 人口: {len(df_wb)} 行")
        df_wb["year"] = pd.to_numeric(df_wb["year"], errors="coerce")
        df_wb["value"] = pd.to_numeric(df_wb["value"], errors="coerce")
        df_wb = df_wb[(df_wb["year"] >= 2023) & (df_wb["year"] <= 2025)]
    else:
        df_wb = pd.DataFrame()
        log("World Bank 文件不存在")

    # 合并
    all_rows = []
    for _, row in df_census.iterrows():
        if pd.notna(row.get("population")):
            all_rows.append({
                "province": row.get("province", ""),
                "year": row.get("year"),
                "indicator": "常住人口",
                "value": row.get("population"),
                "source": "第七次人口普查",
            })

    for _, row in df_wb.iterrows():
        if pd.notna(row.get("value")):
            all_rows.append({
                "province": "全国",
                "year": row.get("year"),
                "indicator": row.get("indicator", ""),
                "value": row.get("value"),
                "source": "World Bank",
            })

    df = pd.DataFrame(all_rows)
    log(f"合并后: {df.shape[0]} 行")

    # 缺失值报告
    na_total = df.isnull().sum().sum()
    log(f"缺失值: {na_total} 个 (已删除 value 为空的行)")

    out = CLEANED_DIR / "s7_population.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")
    log(f"输出: {df.shape[0]} 行 × {df.shape[1]} 列 → {out}")
    return df


if __name__ == "__main__":
    clean_s7()
