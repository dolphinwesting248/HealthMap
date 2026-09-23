"""
S7-Clean: 人口数据清洗
输入: data/raw/pop_census/, data/raw/pop_wb/
输出: data/cleaned/pop_census.csv, pop_wb.csv
"""
import pandas as pd
from pathlib import Path
from utils import CLEANED_DIR, normalize_province, log


def clean_census():
    raw = Path(__file__).resolve().parent.parent.parent / "data" / "raw" / "pop_census" / "census_7_province_population.csv"
    if not raw.exists():
        log("人口普查文件不存在"); return

    df = pd.read_csv(raw, dtype=str)
    df["province"] = df["province"].apply(normalize_province)
    df["population"] = pd.to_numeric(df["population"], errors="coerce")
    df["year"] = pd.to_numeric(df["year"], errors="coerce")

    out = CLEANED_DIR / "pop_census.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")
    log(f"人口普查: {df.shape[0]} 行 → {out}")


def clean_wb():
    raw = Path(__file__).resolve().parent.parent.parent / "data" / "raw" / "pop_wb" / "worldbank_population_china.csv"
    if not raw.exists():
        log("World Bank 文件不存在"); return

    df = pd.read_csv(raw, dtype=str)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"])
    df["year"] = pd.to_numeric(df["year"], errors="coerce")

    out = CLEANED_DIR / "pop_wb.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")
    log(f"World Bank: {df.shape[0]} 行 → {out}")


def clean():
    print("\n[S7] 清洗人口数据...")
    clean_census()
    clean_wb()


if __name__ == "__main__":
    clean()
