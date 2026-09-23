"""
S2-Fetch: 医疗机构 POI 采集 (百度地图)
输出: data/raw/health_resource/medical_poi.csv
"""
import json
import sys
import time
from pathlib import Path

import pandas as pd
import requests

from config import get_output_dir, PROXIES, BAIDU_AK

BAIDU_POI_URL = "https://api.map.baidu.com/place/v2/search"
MEDICAL_QUERIES = ["医院", "诊所", "卫生所", "卫生院", "社区卫生服务中心",
                   "妇幼保健", "中医院", "体检中心", "药店"]

# 31 个省会/直辖市
CITIES = [
    "北京", "上海", "天津", "重庆",
    "石家庄", "太原", "呼和浩特", "沈阳", "长春", "哈尔滨",
    "南京", "杭州", "合肥", "福州", "南昌", "济南",
    "郑州", "武汉", "长沙", "广州", "南宁", "海口",
    "成都", "贵阳", "昆明", "拉萨", "西安", "兰州",
    "西宁", "银川", "乌鲁木齐",
]


def search_pois(ak, query, region):
    """百度 POI 搜索"""
    all_pois, page = [], 0
    while page < 20:
        try:
            r = requests.get(BAIDU_POI_URL, params={
                "query": query, "region": region, "ak": ak,
                "output": "json", "scope": 2,
                "page_size": 20, "page_num": page,
            }, timeout=15, proxies=PROXIES)
            data = r.json()
            if data.get("status") != 0:
                break
            results = data.get("results", [])
            total = data.get("total", 0)
            if not results:
                break
            for p in results:
                loc = p.get("location", {})
                all_pois.append({
                    "id": p.get("uid", ""),
                    "name": p.get("name", ""),
                    "address": p.get("address", ""),
                    "city": p.get("city", ""),
                    "district": p.get("area", ""),
                    "tel": p.get("telephone", ""),
                    "longitude": loc.get("lng", 0),
                    "latitude": loc.get("lat", 0),
                    "search_query": query,
                })
            if len(all_pois) >= total:
                break
            page += 1
            time.sleep(0.1)
        except Exception:
            break
    return all_pois


def _append_csv(rows, csv_path):
    df = pd.DataFrame(rows)
    write_header = not csv_path.exists() or csv_path.stat().st_size == 0
    df.to_csv(csv_path, mode="a", index=False, header=write_header, encoding="utf-8-sig")


def _load_progress(progress_path):
    if progress_path.exists():
        return set(json.loads(progress_path.read_text(encoding="utf-8")))
    return set()


def _save_progress(progress_path, done):
    progress_path.write_text(json.dumps(sorted(done), ensure_ascii=False), encoding="utf-8")


def fetch(output_dir):
    csv_path = output_dir / "medical_poi.csv"
    progress_path = output_dir / "progress.json"

    if not BAIDU_AK:
        print("[S2] 未设置 BAIDU_AK"); return

    done = _load_progress(progress_path)
    seen = set()
    # 从已有 CSV 加载已采集的 ID
    if csv_path.exists() and csv_path.stat().st_size > 0:
        df = pd.read_csv(csv_path, usecols=["id"], dtype=str)
        seen = set(df["id"].tolist())
    print(f"[S2] 百度地图医疗 POI 采集 (已完成 {len(done)} 个任务, {len(seen)} 条 POI)")

    batch = []
    count = 0
    for city in CITIES:
        for query in MEDICAL_QUERIES:
            count += 1
            task_key = f"{city}_{query}"
            if task_key in done:
                continue

            pois = search_pois(BAIDU_AK, query, city)
            new = [p for p in pois if p["id"] not in seen]
            for p in new:
                seen.add(p["id"])
            batch.extend(new)
            done.add(task_key)

            if new:
                print(f"  [{count}] {city}/{query}: +{len(new)}")

            if len(batch) >= 10:
                _append_csv(batch, csv_path)
                _save_progress(progress_path, done)
                batch = []
            time.sleep(0.15)

    if batch:
        _append_csv(batch, csv_path)
        _save_progress(progress_path, done)

    if csv_path.exists():
        df = pd.read_csv(csv_path)
        print(f"\n  总计 {len(df)} 条 → {csv_path}")


if __name__ == "__main__":
    OUTPUT_DIR = get_output_dir("s2_health_resource")
    fetch(OUTPUT_DIR)
