"""
S3-Fetch: 空气质量数据采集
输出: data/raw/env_air/
"""
import io
import zipfile
from pathlib import Path

import pandas as pd
import requests

from config import get_output_dir, PROXIES


def fetch(output_dir):
    csv_path = output_dir / "china_air_quality_daily.csv"
    if csv_path.exists():
        print(f"[S3] 数据已存在: {csv_path}")
        return

    url = "https://www.kaggle.com/api/v1/datasets/download/houjihao/china-capitals-weather-and-air-quality-2023-2026"
    print("[S3] 从 Kaggle 下载...")
    resp = requests.get(url, timeout=120, proxies=PROXIES)
    resp.raise_for_status()

    z = zipfile.ZipFile(io.BytesIO(resp.content))
    z.extractall(output_dir)

    for f in output_dir.glob("china_provincial*.csv"):
        df = pd.read_csv(f)
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"[S3] {len(df)} 行 → {csv_path}")
        break


if __name__ == "__main__":
    import pandas as pd
    OUTPUT_DIR = get_output_dir("s3_env_air")
    fetch(OUTPUT_DIR)
