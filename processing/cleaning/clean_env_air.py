"""
S3-Clean: 空气质量数据清洗
输入: data/raw/env_air/china_air_quality_daily.csv
输出: data/cleaned/env_air_quality.csv
"""
import pandas as pd
from pathlib import Path

from utils import CLEANED_DIR, log


def clean():
    print("\n[S3] 清洗空气质量数据...")
    raw = Path(__file__).resolve().parent.parent.parent / "data" / "raw" / "env_air" / "china_air_quality_daily.csv"
    if not raw.exists():
        log(f"文件不存在: {raw}")
        return

    df = pd.read_csv(raw)
    log(f"原始: {df.shape[0]} 行 × {df.shape[1]} 列")

    # 0. 英文城市名→省份 (province_level_region 本身可作省份, 统一短名)
    if "province" not in df.columns:
        df["province"] = df.get("province_level_region", df.get("city_name"))
        if "province_level_region" in df.columns:
            df = df.drop(columns=["province_level_region"])

    # 1. 统一省份名
    df["province"] = df["province"].apply(
        lambda x: x.split(",")[0].strip() if isinstance(x, str) and "," in x else x
    )

    # 2. 日期过滤 2023-2025
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df[(df["date"] >= "2023-01-01") & (df["date"] <= "2025-12-31")]
    log(f"过滤 2023-2025: {df.shape[0]} 行")

    # 3. 标准化列名
    df = df.rename(columns={
        "city_name": "city", "pm2_5_mean_ug_m3": "pm25",
        "pm10_mean_ug_m3": "pm10", "nitrogen_dioxide_mean_ug_m3": "no2",
        "ozone_mean_ug_m3": "o3", "us_aqi_daily_max": "aqi",
        "temperature_2m_mean_c": "temp_c", "precipitation_sum_mm": "precipitation",
        "wind_speed_10m_max_kmh": "wind_speed",
    })

    keep = ["date", "city", "province", "latitude", "longitude",
            "pm25", "pm10", "no2", "o3", "aqi", "temp_c", "precipitation", "wind_speed"]
    df = df[[c for c in keep if c in df.columns]]

    # 4. 缺失值：坐标缺失删除，数值前向填充3天
    df = df.dropna(subset=["latitude", "longitude"])
    df = df.sort_values(["city", "date"])
    for col in ["pm25", "pm10", "no2", "o3", "aqi", "temp_c", "precipitation", "wind_speed"]:
        if col in df.columns:
            df[col] = df.groupby("city")[col].transform(lambda x: x.ffill(limit=3))

    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month

    out = CLEANED_DIR / "env_air_quality.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")
    log(f"输出: {df.shape[0]} 行 × {df.shape[1]} 列 → {out}")


if __name__ == "__main__":
    clean()
