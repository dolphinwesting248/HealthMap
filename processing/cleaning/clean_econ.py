"""
S6-Clean: 省级社会经济数据清洗
输入: data/raw/econ_gdp/, econ_price/, econ_labor/, econ_income/, pop_age/, pop_life_exp/
输出: data/cleaned/econ_gdp.csv, econ_price.csv, econ_labor.csv,
     econ_income.csv, econ_pop_age.csv, econ_life_expectancy.csv, econ_supplement.csv
"""
import pandas as pd
from pathlib import Path
from utils import CLEANED_DIR, normalize_province, log


def clean_domain(raw_dir, domain_name, output_name):
    csv_files = sorted(raw_dir.glob("nbs_*.csv"))
    if not csv_files:
        log(f"  {domain_name}: 无文件"); return

    all_dfs = []
    for f in csv_files:
        df = pd.read_csv(f, dtype=str)
        df["domain"] = domain_name
        all_dfs.append(df)

    df = pd.concat(all_dfs, ignore_index=True)
    df["province"] = df["province"].apply(normalize_province)
    if "value" in df.columns:
        df["value_clean"] = df["value"].str.replace(",", "", regex=False).str.strip()
        df["value_num"] = pd.to_numeric(df["value_clean"], errors="coerce")

    out = CLEANED_DIR / f"{output_name}.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")
    log(f"  {output_name}: {df.shape[0]} 行 → {out}")


def clean_supplement():
    raw = Path(__file__).resolve().parent.parent.parent / "data" / "raw" / "econ_gdp" / "world_bank_supplement.csv"
    if not raw.exists(): return
    df = pd.read_csv(raw, dtype=str)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    out = CLEANED_DIR / "econ_supplement.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")
    log(f"  经济补充: {df.shape[0]} 行 → {out}")


def clean():
    print("\n[S6] 清洗经济数据...")
    raw_root = Path(__file__).resolve().parent.parent.parent / "data" / "raw"
    for sub, name in [("econ_gdp", "econ_gdp"), ("econ_price", "econ_price"),
                      ("econ_labor", "econ_labor"), ("econ_income", "econ_income"),
                      ("pop_age", "econ_pop_age"), ("pop_life_exp", "econ_life_expectancy")]:
        clean_domain(raw_root / sub, name, name)
    clean_supplement()


if __name__ == "__main__":
    clean()
