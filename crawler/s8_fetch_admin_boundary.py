"""
S8: 行政区划边界矢量数据采集
数据源: DataV GeoAtlas
"""
import json
import requests

from config import get_output_dir, CHINA_PROVINCES, PROXIES

BASE_URL = "https://geo.datav.aliyun.com/areas_v3/bound"


def download_boundary(adcode, name, children=True):
    """下载指定行政区划的 GeoJSON"""
    suffix = "_full" if children else ""
    url = f"{BASE_URL}/{adcode}{suffix}.json"
    resp = requests.get(url, timeout=60, proxies=PROXIES)
    if resp.status_code != 200:
        print(f"    跳过 {name} ({adcode}): HTTP {resp.status_code}")
        return None
    data = resp.json()
    out = OUTPUT_DIR / f"{adcode}_{name}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    n = len(data.get("features", []))
    print(f"  {name} ({adcode}): {n} 个子区域 → {out.name}")
    return data


if __name__ == "__main__":
    OUTPUT_DIR = get_output_dir("admin_boundary")
    print("[S8] 下载行政区划边界数据...")

    # 全国省界
    download_boundary("100000", "china")

    # 31省市级边界
    for code, name in CHINA_PROVINCES.items():
        download_boundary(code, name)

    print("[S8] 完成！")
