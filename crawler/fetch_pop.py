"""
S7-Fetch: 人口数据采集
输出: data/raw/pop_census/, data/raw/pop_wb/
"""
import time
from pathlib import Path

import pandas as pd
import requests

from config import get_output_dir, PROXIES


# 省级人口普查数据（编译自第七次全国人口普查公报）
PROVINCE_POPULATION_2020 = {
    "广东": 12601, "山东": 10153, "河南": 9937, "江苏": 8475, "四川": 8368,
    "河北": 7461, "湖南": 6644, "浙江": 6457, "安徽": 6103, "湖北": 5775,
    "广西": 5013, "云南": 4721, "江西": 4519, "辽宁": 4259, "福建": 4154,
    "陕西": 3953, "贵州": 3856, "山西": 3492, "重庆": 3206, "黑龙江": 3185,
    "新疆": 2585, "甘肃": 2502, "上海": 2487, "内蒙古": 2405, "吉林": 2407,
    "北京": 2189, "天津": 1387, "海南": 1008, "宁夏": 720, "青海": 592, "西藏": 365,
}

ADCODES = {
    "广东": 440000, "山东": 370000, "河南": 410000, "江苏": 320000, "四川": 510000,
    "河北": 130000, "湖南": 430000, "浙江": 330000, "安徽": 340000, "湖北": 420000,
    "广西": 450000, "云南": 530000, "江西": 360000, "辽宁": 210000, "福建": 350000,
    "陕西": 610000, "贵州": 520000, "山西": 140000, "重庆": 500000, "黑龙江": 230000,
    "新疆": 650000, "甘肃": 620000, "上海": 310000, "内蒙古": 150000, "吉林": 220000,
    "北京": 110000, "天津": 120000, "海南": 460000, "宁夏": 640000, "青海": 630000, "西藏": 540000,
}


def fetch_census(output_dir):
    csv_path = output_dir / "census_7_province_population.csv"
    rows = [{"province": p, "adcode": ADCODES.get(p), "population_wan": pop,
             "population": pop * 10000, "year": 2020, "source": "第七次全国人口普查"}
            for p, pop in PROVINCE_POPULATION_2020.items()]
    pd.DataFrame(rows).to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"[S7-Census] {len(rows)} 省份 → {csv_path}")


def fetch_worldbank(output_dir):
    csv_path = output_dir / "worldbank_population_china.csv"
    indicators = {
        "SP.POP.TOTL": "total_population", "SP.POP.TOTL.FE.ZS": "female_pct",
        "SP.URB.TOTL.IN.ZS": "urbanization_rate", "SP.DYN.LE00.IN": "life_expectancy",
        "SP.DYN.CDRT.IN": "death_rate", "SP.DYN.CBRT.IN": "birth_rate",
        "SP.DYN.IMRT.IN": "infant_mortality", "NY.GDP.PCAP.CD": "gdp_per_capita",
        "SH.XPD.CHEX.GD.ZS": "health_expenditure_gdp", "SH.MED.PHYS.ZS": "physicians_per_1000",
        "SH.MED.BEDS.ZS": "hospital_beds_per_1000", "SP.POP.GROW": "population_growth_rate",
        "SH.XPD.CHEX.PC.CD": "per_capita_health_exp", "SI.POV.GINI": "gini_coefficient",
        "SI.POV.NAHC": "poverty_rate",
    }
    all_data = []
    for code, name in indicators.items():
        try:
            r = requests.get(f"https://api.worldbank.org/v2/country/CHN/indicator/{code}",
                           params={"format": "json", "per_page": 200}, timeout=15, proxies=PROXIES)
            data = r.json()
            if len(data) > 1:
                for rec in data[1]:
                    if rec.get("value") is not None:
                        all_data.append({"indicator_code": code, "indicator_name": name,
                                         "year": rec.get("date"), "value": rec.get("value")})
        except Exception: pass
        time.sleep(0.3)

    pd.DataFrame(all_data).to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"[S7-WB] {len(all_data)} 条 → {csv_path}")


if __name__ == "__main__":
    fetch_census(get_output_dir("s7_pop_census"))
    fetch_worldbank(get_output_dir("s7_pop_wb"))
