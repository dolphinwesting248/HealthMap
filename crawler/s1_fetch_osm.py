"""
S1: OpenStreetMap 中国路网数据采集
数据源: Geofabrik
"""
import requests
from pathlib import Path

from config import get_output_dir, PROXIES

# Geofabrik 下载链接
REGIONS = {
    "china": "https://download.geofabrik.de/asia/china-latest.osm.pbf",
    # 按需取消注释各省子区域
    # "guangdong": "https://download.geofabrik.de/asia/china/guangdong-latest.osm.pbf",
    # "beijing":   "https://download.geofabrik.de/asia/china/beijing-latest.osm.pbf",
    # "shanghai":  "https://download.geofabrik.de/asia/china/shanghai-latest.osm.pbf",
    # "zhejiang":  "https://download.geofabrik.de/asia/china/zhejiang-latest.osm.pbf",
    # "jiangsu":   "https://download.geofabrik.de/asia/china/jiangsu-latest.osm.pbf",
    # "shandong":  "https://download.geofabrik.de/asia/china/shandong-latest.osm.pbf",
    # "sichuan":   "https://download.geofabrik.de/asia/china/sichuan-latest.osm.pbf",
    # "henan":     "https://download.geofabrik.de/asia/china/henan-latest.osm.pbf",
    # "hubei":     "https://download.geofabrik.de/asia/china/hubei-latest.osm.pbf",
    # "hunan":     "https://download.geofabrik.de/asia/china/hunan-latest.osm.pbf",
}


def download_file(url, output_path):
    """带进度显示的大文件下载"""
    print(f"  下载: {url}")
    resp = requests.get(url, stream=True, timeout=300, proxies=PROXIES)
    resp.raise_for_status()
    total = int(resp.headers.get("content-length", 0))
    downloaded = 0
    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8 * 1024 * 1024):
            f.write(chunk)
            downloaded += len(chunk)
            if total > 0:
                pct = downloaded / total * 100
                mb = downloaded / 1024 / 1024
                print(f"\r  {mb:.0f}/{total/1024/1024:.0f} MB ({pct:.1f}%)", end="", flush=True)
    print()
    return output_path


if __name__ == "__main__":
    OUTPUT_DIR = get_output_dir("osm")
    print("[S1] 下载 OpenStreetMap 路网数据...")

    for region, url in REGIONS.items():
        filename = url.split("/")[-1]
        output = OUTPUT_DIR / filename
        if output.exists():
            print(f"  已存在，跳过: {filename}")
            continue
        try:
            download_file(url, output)
            size_mb = output.stat().st_size / 1024 / 1024
            print(f"  完成: {filename} ({size_mb:.1f} MB)")
        except Exception as e:
            print(f"  下载失败: {e}")

    print("[S1] 完成！")
