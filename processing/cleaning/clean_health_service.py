"""
S5-Clean: 省级卫生指标清洗
输入: data/raw/health_service/nbs_health_*.csv, who_gho_china_health.csv
输出: data/cleaned/health_service.csv
"""
import pandas as pd
from pathlib import Path
from utils import CLEANED_DIR, normalize_province, log


def clean():
    print("\n[S5] 清洗卫生指标数据...")
    raw_dir = Path(__file__).resolve().parent.parent.parent / "data" / "raw" / "health_service"

    all_dfs = []
    for f in sorted(raw_dir.glob("nbs_health_*.csv")):
        df = pd.read_csv(f, dtype=str)
        df["domain"] = f.stem.replace("nbs_health_", "")
        all_dfs.append(df)
        log(f"  {f.name}: {len(df)} 行")

    # WHO 数据
    who_file = raw_dir / "who_gho_china_health.csv"
    if who_file.exists():
        who_df = pd.read_csv(who_file, dtype=str)
        who_df["domain"] = "who_gho"
        all_dfs.append(who_df)
        log(f"  who_gho: {len(who_df)} 行")

    if not all_dfs:
        log("无数据文件"); return

    df = pd.concat(all_dfs, ignore_index=True)
    log(f"合并: {df.shape[0]} 行")

    # 省份统一
    if "province" in df.columns:
        df["province"] = df["province"].apply(normalize_province)

    # value 转数值
    if "value" in df.columns:
        df["value_clean"] = df["value"].str.replace(",", "", regex=False).str.strip()
        df["value_num"] = pd.to_numeric(df["value_clean"], errors="coerce")

    out = CLEANED_DIR / "health_service.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")
    log(f"输出: {df.shape[0]} 行 × {df.shape[1]} 列 → {out}")


if __name__ == "__main__":
    clean()
