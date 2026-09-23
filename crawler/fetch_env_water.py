"""
S3-Fetch: 水质量数据采集
输出: data/raw/env_water/
"""
import io
import zipfile

import requests

from config import get_output_dir, PROXIES


def fetch(output_dir):
    csv_path = output_dir / "china_water_pollution_data.csv"
    if csv_path.exists():
        print(f"[S3] 数据已存在: {csv_path}")
        return

    url = "https://www.kaggle.com/api/v1/datasets/download/khushikyad001/china-water-pollution-monitoring-dataset"
    print("[S3] 从 Kaggle 下载水质量数据...")
    resp = requests.get(url, timeout=60, proxies=PROXIES)
    resp.raise_for_status()

    z = zipfile.ZipFile(io.BytesIO(resp.content))
    z.extractall(output_dir)
    print(f"[S3] 解压完成 → {output_dir}")


if __name__ == "__main__":
    OUTPUT_DIR = get_output_dir("s3_env_water")
    fetch(OUTPUT_DIR)
