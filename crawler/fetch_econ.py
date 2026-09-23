"""
S6-Fetch: 社会经济数据采集 (国家数据平台)
输出: data/raw/econ_gdp/, econ_price/, econ_labor/, econ_income/, pop_age/, pop_life_exp/
"""
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

# 7 个父节点 → (父节点ID, 输出目录key, CSV文件名, 标签)
PARENT_NODES = [
    ("da5ccb68e9de4671ad967247fe427c91", "s6_econ", "nbs_econ_gdp.csv", "GDP与经济增长"),
    ("472e11f6c54f4144b233e45f3d641121", "s6_econ", "nbs_econ_finance.csv", "地方财政"),
    ("b607e35c481f47a7ae907d9645ee90a8", "s6_econ_price", "nbs_econ_price.csv", "价格指数"),
    ("d41ae1904e194b9384e0380b1effdc9d", "s6_econ_labor", "nbs_econ_labor.csv", "就业与工资"),
    ("5c072e1073514e448de4132760308fcf", "s6_econ_income", "nbs_econ_income.csv", "居民收入"),
    ("5a4602c60d764cc6adc7d88d9b512efc", "s6_pop_age", "nbs_pop_age_structure.csv", "人口年龄构成与抚养比"),
    ("96c74b9bdfcf480192ff566bffc50bb0", "s6_pop_life_exp", "nbs_life_expectancy.csv", "人口平均预期寿命"),
]

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


def get_sub_domains(parent_id):
    """获取父节点下的子领域列表"""
    try:
        r = requests.get(TREE_URL, params={"pid": parent_id, "code": 6},
                         timeout=15, headers=HEADERS, proxies=PROXIES)
        if r.status_code == 200:
            return r.json() if isinstance(r.json(), list) else r.json().get("data", [])
    except Exception:
        pass
    return []


def fetch_domain(parent_id, label, csv_path):
    """采集一个分类的数据: 若有子领域则逐个采集, 否则按叶子分类直接采指标"""
    if csv_path.exists():
        print(f"  {label}: 已存在 ({csv_path.name})"); return

    sub_domains = get_sub_domains(parent_id)
    leaf_mode = not sub_domains  # 叶子分类: cid 即指标容器
    if leaf_mode:
        sub_domains = [{"show_name": label, "_id": parent_id}]
    print(f"  {label}: {'叶子分类' if leaf_mode else f'{len(sub_domains)} 个子领域'}")

    all_rows = []
    for sub in sub_domains:
        sub_name = sub.get("show_name", sub.get("name", ""))
        cid = sub.get("_id", "")
        if not cid: continue

        # 获取指标 IDs
        try:
            r2 = requests.get(IND_URL, params={"cid": cid}, timeout=15, headers=HEADERS, proxies=PROXIES)
            indicators = r2.json().get("data", {}).get("list", []) if r2.status_code == 200 else []
        except Exception:
            indicators = []
        ind_ids = [ind.get("_id") for ind in indicators if ind.get("_id")]
        # 空指标列表时仍尝试 POST (API 支持 indicatorIds=[] 返回该分类全部指标)

        # 逐省采集
        for adcode, province in PROVINCES.items():
            body = {"cid": cid, "daCatalogId": "", "das": [{"text": province, "value": adcode}],
                    "dts": "", "indicatorIds": ind_ids,
                    "rootId": "c4d82af16c3d4f0cb4f09d4af7d5888e", "showType": "1"}
            try:
                r3 = requests.post(DATA_URL, json=body, timeout=30,
                                   headers=HEADERS, proxies=PROXIES)
                if r3.status_code == 200 and r3.json().get("success"):
                    for yd in r3.json().get("data", []):
                        year = yd.get("code", "").replace("YY", "")
                        for v in yd.get("values", []):
                            ind = v.get("i_showname", "").strip()
                            val = v.get("value", "")
                            if ind:
                                all_rows.append({"province": province, "adcode": adcode,
                                                 "year": year, "indicator": ind,
                                                 "value": val.strip() if val else ""})
            except Exception as e:
                print(f"    {province} {sub_name}: 失败 {e}")
            time.sleep(0.2)
        time.sleep(0.3)

    if all_rows:
        df = pd.DataFrame(all_rows)
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"    → {len(df)} 条")
    else:
        print(f"    → 无数据 (可能网络受限或接口变更)")


def fetch():
    for parent_id, dir_key, csv_name, label in PARENT_NODES:
        sub_dir = get_output_dir(dir_key)
        print(f"\n[S6] {label}...")
        fetch_domain(parent_id, label, sub_dir / csv_name)


if __name__ == "__main__":
    fetch()
