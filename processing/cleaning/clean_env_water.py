"""
S3-Clean: 水质量数据清洗
输入: data/raw/env_water/china_water_pollution_data.csv
输出: data/cleaned/env_water_quality.csv
"""
import pandas as pd
from pathlib import Path
from utils import CLEANED_DIR, log


def clean():
    print("\n[S3-Water] 清洗水质量数据...")
    raw = Path(__file__).resolve().parent.parent.parent / "data" / "raw" / "env_water" / "china_water_pollution_data.csv"
    if not raw.exists():
        log(f"文件不存在: {raw}"); return

    df = pd.read_csv(raw)
    log(f"原始: {df.shape[0]} 行 × {df.shape[1]} 列")

    # 标准化列名
    df = df.rename(columns={"Province": "province", "City": "city", "Date": "date"})
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # 过滤 2023-2025
    df = df[(df["date"] >= "2023-01-01") & (df["date"] <= "2025-12-31")]
    log(f"过滤 2023-2025: {df.shape[0]} 行")

    # 缺失值统计
    na = df.isnull().sum().sum()
    log(f"缺失值: {na}")

    out = CLEANED_DIR / "env_water_quality.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")
    log(f"输出: {df.shape[0]} 行 × {df.shape[1]} 列 → {out}")


if __name__ == "__main__":
    clean()
