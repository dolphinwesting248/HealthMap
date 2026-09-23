"""
S5-Fetch: 省级卫生指标采集
输出: data/raw/health_service/
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
PARENT_ID = "aad2947cd56047a69a6b17504f227db5"

PROVINCES = {
    "110000000000": "北京", "120000000000": "天津", "130000000000": "河北",
    "140000000000": "山西", "150000000000": "内蒙古", "210000000000": "辽宁",
    "220000000000": "吉林", "230000000000": "黑龙江", "310000000000": "上海",
    "320000000000": "江苏", "330000000000": "浙江", "340000000000": "安徽",
    "350000000000": "福建", "360000000000": "江西", "370000000000": "山东",
    "410000000000": "河南", "420000000000": "湖北", "430000000000": "湖南",
    "440000000000": "广东", "450000000000": "广西", "460000000000": "海南",
    "500000000000": "重庆", "510000000000": "四川", "520000000000": "贵州",
    "530000000000": "云南", "540000000000": "西藏", "610000000000": "陕西",
    "620000000000": "甘肃", "630000000000": "青海", "640000000000": "宁夏",
    "650000000000": "新疆",
}


def get_domains():
    r = requests.get(TREE_URL, params={"pid": PARENT_ID, "code": 6}, timeout=15, headers=HEADERS, proxies=PROXIES)
    domains_raw = r.json() if isinstance(r.json(), list) else r.json().get("data", [])
    domains = []
    for node in domains_raw:
        name = node.get("show_name", node.get("name", "")).strip()
        cid = node.get("_id", "")
        if not cid: continue
        r2 = requests.get(IND_URL, params={"cid": cid}, timeout=15, headers=HEADERS, proxies=PROXIES)
        if r2.status_code == 200:
            indicators = r2.json().get("data", {}).get("list", [])
            ind_ids = [ind.get("_id") for ind in indicators if ind.get("_id")]
            domains.append({"name": name, "cid": cid, "indicator_ids": ind_ids})
        time.sleep(0.3)
    return domains


def fetch_province(cid, indicator_ids, adcode, province_name):
    body = {"cid": cid, "daCatalogId": "", "das": [{"text": province_name, "value": adcode}],
            "dts": "", "indicatorIds": indicator_ids,
            "rootId": "c4d82af16c3d4f0cb4f09d4af7d5888e", "showType": "1"}
    try:
        r = requests.post(DATA_URL, json=body, timeout=30,
                         headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"},
                         proxies=PROXIES)
        if r.status_code == 200 and r.json().get("success"):
            return r.json().get("data", [])
    except Exception:
        pass
    return []


def fetch(output_dir):
    print("[S5] 获取卫生领域列表...")
    domains = get_domains()
    print(f"  共 {len(domains)} 个领域\n")

    for domain in domains:
        safe_name = domain["name"].replace("/", "_").replace(" ", "_").replace("(", "").replace(")", "")
        csv_path = output_dir / f"nbs_health_{safe_name}.csv"
        if csv_path.exists(): continue

        print(f"  {domain['name']}...")
        all_rows = []
        for adcode, province in PROVINCES.items():
            data = fetch_province(domain["cid"], domain["indicator_ids"], adcode, province)
            for year_data in data:
                year = year_data.get("code", "").replace("YY", "")
                for v in year_data.get("values", []):
                    indicator = v.get("i_showname", "").strip()
                    value = v.get("value", "")
                    if indicator:
                        all_rows.append({"province": province, "adcode": adcode,
                                         "year": year, "indicator": indicator, "value": value.strip() if value else ""})
            time.sleep(0.2)

        df = pd.DataFrame(all_rows)
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"    → {len(df)} 条")


def fetch_who(output_dir):
    from config import WAQI_TOKEN
    WHO_API = "https://ghoapi.azureedge.net/api"
    indicators = {
        "WHOSIS_000001": "life_expectancy_at_birth", "WHOSIS_000002": "healthy_life_expectancy_hale",
        "WHOSIS_000015": "life_expectancy_at_60", "MDG_0000000001": "under5_mortality_rate",
        "MDG_0000000026": "maternal_mortality_ratio", "WHS3_49": "crude_death_rate",
        "WHS3_41": "crude_birth_rate", "NCD_BMI_30A": "obesity_prevalence",
        "NCD_BMI_30C": "overweight_prevalence", "MDG_0000000007": "tb_incidence",
        "WHS4_100": "health_expenditure_per_capita", "SH.MED.PHYS.ZS": "physicians_per_10k",
        "SH.MED.BEDS.ZS": "hospital_beds_per_10k",
    }
    all_data = []
    for ind_id, ind_name in indicators.items():
        try:
            r = requests.get(f"{WHO_API}/{ind_id}",
                           params={"$filter": "SpatialDim eq 'CHN' and TimeDim ge 2020 and TimeDim le 2025"},
                           timeout=20, proxies=PROXIES)
            if r.status_code == 200:
                for rec in r.json().get("value", []):
                    all_data.append({"indicator_id": ind_id, "indicator_name": ind_name,
                                     "year": rec.get("TimeDim"), "value": rec.get("NumericValue"),
                                     "sex": rec.get("Dim1", "")})
        except Exception: pass
        time.sleep(0.3)

    df = pd.DataFrame(all_data)
    out = output_dir / "who_gho_china_health.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"[S5-WHO] {len(df)} 条 → {out}")


if __name__ == "__main__":
    OUTPUT_DIR = get_output_dir("s5_health_service")
    fetch(OUTPUT_DIR)
    fetch_who(OUTPUT_DIR)
