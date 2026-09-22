"""
S3: 中国省会城市空气质量与气象历史数据

数据源: Kaggle - houjihao/china-capitals-weather-and-air-quality-2023-2026
- 31 个省会/直辖市
- 时间范围限定: 2023-2025
- 每日数据: PM2.5, PM10, NO₂, O₃, AQI + 气温/降水/风速          
"""
import io
import zipfile
from pathlib import Path

import pandas as pd
import requests

from config import get_output_dir, PROXIES

# Kaggle 数据集地址
KAGGLE_DATASET = "houjihao/china-capitals-weather-and-air-quality-2023-2026"
KAGGLE_URL = f"https://www.kaggle.com/api/v1/datasets/download/{KAGGLE_DATASET}"

# 目标文件名
MAIN_CSV = "china_air_quality_daily.csv"


def download_dataset(output_dir: Path):
    """从 Kaggle 下载数据集并解压"""
    zip_path = output_dir / "dataset.zip"

    print("[S3] 从 Kaggle 下载数据集...")
    print(f"  数据集: {KAGGLE_DATASET}")
    resp = requests.get(KAGGLE_URL, timeout=120, proxies=PROXIES)
    resp.raise_for_status()
    print(f"  下载完成: {len(resp.content) / 1024:.0f} KB")

    # 解压
    z = zipfile.ZipFile(io.BytesIO(resp.content))
    print(f"  ZIP 内容:")
    for name in z.namelist():
        info = z.getinfo(name)
        print(f"    {name} ({info.file_size // 1024} KB)")
    z.extractall(output_dir)
    print(f"  解压到: {output_dir}")

    # 清理 zip
    zip_path.unlink(missing_ok=True)


def process_data(output_dir: Path):
    """处理数据：重命名列、标准化"""
    # 找到主 CSV 文件
    csv_files = list(output_dir.glob("*.csv"))
    main_file = None
    for f in csv_files:
        if f.name.startswith("china_provincial"):
            main_file = f
            break
    if not main_file:
        print("  未找到主数据文件")
        return

    print(f"\n[S3] 处理数据: {main_file.name}")
    df = pd.read_csv(main_file)
    print(f"  原始: {df.shape[0]} 行 × {df.shape[1]} 列")
    print(f"  城市: {df['city_name'].nunique()} 个")
    print(f"  时间: {df['date'].min()} ~ {df['date'].max()}")

    # 标准化列名
    df = df.rename(columns={
        "city_name": "city",
        "province_level_region": "province",
        "pm2_5_mean_ug_m3": "pm25",
        "pm10_mean_ug_m3": "pm10",
        "nitrogen_dioxide_mean_ug_m3": "no2",
        "ozone_mean_ug_m3": "o3",
        "us_aqi_daily_max": "aqi_us",
        "european_aqi_daily_max": "aqi_eu",
        "temperature_2m_mean_c": "temp_mean",
        "temperature_2m_min_c": "temp_min",
        "temperature_2m_max_c": "temp_max",
        "precipitation_sum_mm": "precipitation",
        "rain_sum_mm": "rain",
        "wind_speed_10m_max_kmh": "wind_speed",
    })

    # 保留核心列
    keep_cols = [
        "date", "city", "province", "latitude", "longitude",
        "pm25", "pm10", "no2", "o3", "aqi_us", "aqi_eu",
        "temp_mean", "temp_min", "temp_max",
        "precipitation", "rain", "wind_speed",
    ]
    df = df[[c for c in keep_cols if c in df.columns]]

    # 时间范围限定: 2023-2025
    df = df[(df["date"] >= "2023-01-01") & (df["date"] <= "2025-12-31")]
    print(f"  过滤 2023-2025 后: {df.shape[0]} 行")
    print(f"  时间: {df['date'].min()} ~ {df['date'].max()}")

    # 保存
    out = output_dir / MAIN_CSV
    df.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"  输出: {out}")
    print(f"  大小: {out.stat().st_size / 1024:.0f} KB")
    print(f"  缺失值: {df.isnull().sum().sum()}")


if __name__ == "__main__":
    OUTPUT_DIR = get_output_dir("openaq")

    # 检查是否已有数据
    csv_path = OUTPUT_DIR / MAIN_CSV
    if csv_path.exists():
        print(f"[S3] 数据已存在: {csv_path}")
        print(f"  如需重新下载，请先删除 {csv_path}")
    else:
        download_dataset(OUTPUT_DIR)
        process_data(OUTPUT_DIR)

    print("\n[S3] 完成！")
