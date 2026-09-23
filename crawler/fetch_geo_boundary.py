"""
S8-Fetch: 行政区划边界采集
输出: data/raw/geo_boundary/
"""
import json
import time
from pathlib import Path

import requests

from config import get_output_dir, PROXIES, CHINA_PROVINCES

BASE_URL = "https://geo.datav.aliyun.com/areas_v3/bound"


def fetch(output_dir):
    print("[S8] 下载行政区划边界...")
    for adcode, name in CHINA_PROVINCES.items():
        out = output_dir / f"{adcode}_{name}.json"
        if out.exists(): continue
        url = f"{BASE_URL}/{adcode}_full.json"
        try:
            r = requests.get(url, timeout=60, proxies=PROXIES)
            if r.status_code == 200:
                data = r.json()
                with open(out, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)
                print(f"  {name}: {len(data.get('features', []))} 个区域")
        except Exception as e:
            print(f"  {name}: 失败 {e}")
        time.sleep(0.15)

    # 全国边界
    out = output_dir / "100000_china.json"
    if not out.exists():
        r = requests.get(f"{BASE_URL}/100000_full.json", timeout=60, proxies=PROXIES)
        if r.status_code == 200:
            with open(out, "w", encoding="utf-8") as f:
                json.dump(r.json(), f, ensure_ascii=False)
            print(f"  全国: {len(r.json().get('features', []))} 个区域")


if __name__ == "__main__":
    OUTPUT_DIR = get_output_dir("s8_geo_boundary")
    fetch(OUTPUT_DIR)
