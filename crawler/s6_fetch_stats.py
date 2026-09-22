"""
S6: 国家统计局省级社会经济指标数据采集
数据源: data.stats.gov.cn stream/esData API

遍历 5 个经济领域（GDP、就业、财政、价格、居民生活），
采集 31 省 2023-2025 年数据。每个领域保存为独立 CSV 文件。
"""
import json
import time
from pathlib import Path

import pandas as pd
import requests

from config import get_output_dir, PROXIES

BASE = "https://data.stats.gov.cn/dg/website/publicrelease/web/external"
TREE_URL = f"{BASE}/new/queryIndexTreeAsync"
IND_URL = f"{BASE}/new/queryIndicatorsByCid"
DATA_URL = f"{BASE}/stream/esData"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# 5 个领域的父节点
DOMAIN_PARENTS = [
    ("da5ccb68e9de4671ad967247fe427c91", "GDP与经济增长"),
    ("d41ae1904e194b9384e0380b1effdc9d", "就业与工资"),
    ("472e11f6c54f4144b233e45f3d641121", "地方财政"),
    ("b607e35c481f47a7ae907d9645ee90a8", "价格指数"),
    ("b8a6a78e15684f47b1c340cdb0ff8a23", "居民生活"),
]

# 31 省 adcode
PROVINCES = {
    "110000000000": "北京", "120000000000": "天津", "130000000000": "河北",
    "140000000000": "山西", "150000000000": "内蒙古",
    "210000000000": "辽宁", "220000000000": "吉林", "230000000000": "黑龙江",
    "310000000000": "上海", "320000000000": "江苏", "330000000000": "浙江",
    "340000000000": "安徽", "350000000000": "福建", "360000000000": "江西",
    "370000000000": "山东", "410000000000": "河南", "420000000000": "湖北",
    "430000000000": "湖南", "440000000000": "广东", "450000000000": "广西",
    "460000000000": "海南", "500000000000": "重庆", "510000000000": "四川",
    "520000000000": "贵州", "530000000000": "云南", "540000000000": "西藏",
    "610000000000": "陕西", "620000000000": "甘肃", "630000000000": "青海",
    "640000000000": "宁夏", "650000000000": "新疆",
}


def get_all_domains():
    """从 5 个父节点获取所有子领域"""
    print("[S6] 获取经济领域列表...")
    all_domains = []

    for parent_id, parent_name in DOMAIN_PARENTS:
        r = requests.get(TREE_URL, params={"pid": parent_id, "code": 6},
                         timeout=15, headers=HEADERS, proxies=PROXIES)
        if r.status_code != 200:
            continue

        nodes = r.json() if isinstance(r.json(), list) else r.json().get("data", [])
        print(f"\n  {parent_name}: {len(nodes)} 个子领域")

        for node in nodes:
            name = node.get("show_name", node.get("name", "")).strip()
            cid = node.get("_id", "")
            if not cid:
                continue

            # 获取指标 IDs
            r2 = requests.get(IND_URL, params={"cid": cid}, timeout=15,
                              headers=HEADERS, proxies=PROXIES)
            if r2.status_code == 200:
                indicators = r2.json().get("data", {}).get("list", [])
                ind_ids = [ind.get("_id") for ind in indicators if ind.get("_id")]
                all_domains.append({
                    "parent": parent_name,
                    "name": name,
                    "cid": cid,
                    "indicator_ids": ind_ids,
                })
                print(f"    {name}: {len(ind_ids)} 个指标")
            time.sleep(0.3)

    return all_domains


def fetch_province_data(cid, indicator_ids, adcode, province_name):
    """获取单个省份的数据"""
    body = {
        "cid": cid,
        "daCatalogId": "",
        "das": [{"text": province_name, "value": adcode}],
        "dts": "",
        "indicatorIds": indicator_ids,
        "rootId": "c4d82af16c3d4f0cb4f09d4af7d5888e",
        "showType": "1",
    }
    try:
        r = requests.post(DATA_URL, json=body, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/json",
        }, proxies=PROXIES)
        if r.status_code == 200:
            data = r.json()
            if data.get("success"):
                return data.get("data", [])
    except Exception:
        pass
    return []


def collect_domain(domain, output_dir):
    """采集单个领域的全部省份数据"""
    parent = domain["parent"]
    name = domain["name"]
    cid = domain["cid"]
    ind_ids = domain["indicator_ids"]

    # 安全文件名
    safe_name = name.replace("/", "_").replace(" ", "_").replace("(", "").replace(")", "")
    csv_path = output_dir / f"nbs_{parent}_{safe_name}.csv"

    all_rows = []
    for adcode, province in PROVINCES.items():
        data = fetch_province_data(cid, ind_ids, adcode, province)
        for year_data in data:
            year_code = year_data.get("code", "").replace("YY", "")
            for v in year_data.get("values", []):
                indicator = v.get("i_showname", "").strip()
                value = v.get("value", "")
                if indicator:
                    all_rows.append({
                        "province": province,
                        "adcode": adcode,
                        "year": year_code,
                        "indicator": indicator,
                        "value": value.strip() if value else "",
                    })
        time.sleep(0.2)

    df = pd.DataFrame(all_rows)
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    return df


def main():
    OUTPUT_DIR = get_output_dir("stats")

    # 1. 获取所有领域
    domains = get_all_domains()
    print(f"\n  共 {len(domains)} 个子领域\n")

    # 2. 逐领域采集
    summary = []
    for i, domain in enumerate(domains):
        print(f"[{i+1}/{len(domains)}] {domain['parent']} > {domain['name']}...")
        df = collect_domain(domain, OUTPUT_DIR)
        summary.append({
            "parent": domain["parent"],
            "domain": domain["name"],
            "rows": len(df),
            "indicators": len(domain["indicator_ids"]),
        })
        print(f"  → {len(df)} 条\n")

    # 3. 汇总
    print("=" * 60)
    print("采集汇总:")
    for s in summary:
        print(f"  [{s['parent']}] {s['domain']:35s} | {s['rows']:6d} 条 | {s['indicators']:2d} 指标")
    total = sum(s["rows"] for s in summary)
    print(f"  {'总计':42s} | {total:6d} 条")


if __name__ == "__main__":
    main()
