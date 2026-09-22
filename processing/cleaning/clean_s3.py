"""
S3 清洗: 空气质量数据
"""
import pandas as pd
from pathlib import Path

from utils import CLEANED_DIR, log

RAW_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "raw" / "s3_openaq" / "china_air_quality_daily.csv"


def clean_s3():
    print("\n[S3] 清洗空气质量数据...")
    if not RAW_FILE.exists():
        log(f"原始文件不存在: {RAW_FILE}")
        return

    df = pd.read_csv(RAW_FILE)
    log(f"原始: {df.shape[0]} 行 × {df.shape[1]} 列")

    # 1. 统一省份名
    df["province"] = df["province"].apply(
        lambda x: x.split(",")[0].strip() if isinstance(x, str) and "," in x else x
    )

    # 2. 确保日期格式
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    na_dates = df["date"].isna().sum()
    if na_dates > 0:
        log(f"日期解析失败: {na_dates} 行 → 删除")
        df = df.dropna(subset=["date"])

    # 3. 时间范围限定: 2023-2025
    df = df[(df["date"] >= "2023-01-01") & (df["date"] <= "2025-12-31")]
    log(f"过滤 2023-2025: {df.shape[0]} 行")

    # 4. 标准化列名
    df = df.rename(columns={
        "city_name": "city",
        "pm2_5_mean_ug_m3": "pm25_ugm3",
        "pm10_mean_ug_m3": "pm10_ugm3",
        "nitrogen_dioxide_mean_ug_m3": "no2_ugm3",
        "ozone_mean_ug_m3": "o3_ugm3",
        "us_aqi_daily_max": "aqi",
        "temperature_2m_mean_c": "temp_c",
        "precipitation_sum_mm": "precip_mm",
        "wind_speed_10m_max_kmh": "wind_kmh",
    })

    # 5. 保留核心列
    keep = ["date", "city", "province", "latitude", "longitude",
            "pm25_ugm3", "pm10_ugm3", "no2_ugm3", "o3_ugm3", "aqi",
            "temp_c", "precip_mm", "wind_kmh"]
    df = df[[c for c in keep if c in df.columns]]

    # 6. 缺失值处理
    #    - 坐标缺失: 删除（无法空间分析）
    before = len(df)
    df = df.dropna(subset=["latitude", "longitude"])
    dropped = before - len(df)
    if dropped > 0:
        log(f"坐标缺失删除: {dropped} 行")

    #    - 数值列: 按城市时间排序后前向填充（最多填充3天）
    numeric_cols = ["pm25_ugm3", "pm10_ugm3", "no2_ugm3", "o3_ugm3",
                    "aqi", "temp_c", "precip_mm", "wind_kmh"]
    numeric_cols = [c for c in numeric_cols if c in df.columns]

    missing_before = df[numeric_cols].isnull().sum().sum()
    df = df.sort_values(["city", "date"])
    for col in numeric_cols:
        df[col] = df.groupby("city")[col].transform(
            lambda x: x.ffill(limit=3)
        )
    missing_after = df[numeric_cols].isnull().sum().sum()
    log(f"数值缺失值: {missing_before} → {missing_after} (前向填充3天)")

    #    - 剩余缺失值: 标记为 NA 保留（不删除）
    final_missing = df.isnull().sum().sum()
    if final_missing > 0:
        log(f"保留缺失值: {final_missing} 个 (标记为NA)")

    # 7. 添加年月列
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month

    # 8. 质量检查报告
    log(f"--- 数据质量报告 ---")
    log(f"总行数: {len(df)}")
    log(f"时间范围: {df['date'].min().date()} ~ {df['date'].max().date()}")
    log(f"城市数: {df['city'].nunique()}")
    for col in numeric_cols:
        pct = df[col].isnull().sum() / len(df) * 100
        log(f"  {col}: 缺失率 {pct:.1f}%")

    # 9. 保存
    out = CLEANED_DIR / "s3_air_quality.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")
    log(f"输出: {df.shape[0]} 行 × {df.shape[1]} 列 → {out}")
    return df


if __name__ == "__main__":
    clean_s3()
