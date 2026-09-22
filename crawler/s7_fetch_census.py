"""
S7: 中国人口普查数据采集
- 第七次全国人口普查各省常住人口（2020）
- World Bank 人口时间序列
"""
import time

import pandas as pd
import requests

from config import get_output_dir, PROXIES

# 第七次全国人口普查（2020年）各省常住人口
PROVINCE_POPULATION_2020 = {
    "广东": 12601, "山东": 10153, "河南": 9937, "江苏": 8475,
    "四川": 8368, "河北": 7461, "湖南": 6644, "浙江": 6457,
    "安徽": 6103, "湖北": 5775, "广西": 5013, "云南": 4721,
    "江西": 4519, "辽宁": 4259, "福建": 4154, "陕西": 3953,
    "贵州": 3856, "山西": 3492, "重庆": 3206, "黑龙江": 3185,
    "新疆": 2585, "甘肃": 2502, "上海": 2487, "内蒙古": 2405,
    "吉林": 2407, "北京": 2189, "天津": 1387, "海南": 1008,
    "宁夏": 720, "青海": 592, "西藏": 365,
}

PROVINCE_ADCODES = {
    "广东": 440000, "山东": 370000, "河南": 410000, "江苏": 320000,
    "四川": 510000, "河北": 130000, "湖南": 430000, "浙江": 330000,
    "安徽": 340000, "湖北": 420000, "广西": 450000, "云南": 530000,
    "江西": 360000, "辽宁": 210000, "福建": 350000, "陕西": 610000,
    "贵州": 520000, "山西": 140000, "重庆": 500000, "黑龙江": 230000,
    "新疆": 650000, "甘肃": 620000, "上海": 310000, "内蒙古": 150000,
    "吉林": 220000, "北京": 110000, "天津": 120000, "海南": 460000,
    "宁夏": 640000, "青海": 630000, "西藏": 540000,
}


def collect_province_population():
    """编译第七次人口普查各省常住人口"""
    print("[S7] 编译省级人口数据...")
    rows = []
    for prov, pop in PROVINCE_POPULATION_2020.items():
        rows.append({
            "province": prov, "adcode": PROVINCE_ADCODES.get(prov),
            "population_wan": pop, "population": pop * 10000,
            "year": 2020, "source": "第七次全国人口普查",
        })
    df = pd.DataFrame(rows)
    out = OUTPUT_DIR / "census_7_province_population.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"  {len(df)} 省份 → {out}")


def collect_worldbank_population():
    """从 World Bank 获取人口时间序列"""
    print("[S7] 采集 World Bank 人口指标...")
    indicators = {
        "SP.POP.TOTL": "total_population",
        "SP.POP.TOTL.FE.ZS": "female_pct",
        "SP.URB.TOTL.IN.ZS": "urbanization_rate",
        "SP.DYN.LE00.IN": "life_expectancy",
    }
    all_data = []
    for code, name in indicators.items():
        url = f"https://api.worldbank.org/v2/country/CHN/indicator/{code}"
        try:
            resp = requests.get(url, params={"format": "json", "per_page": 100}, timeout=30, proxies=PROXIES)
            data = resp.json()
            if len(data) > 1:
                for rec in data[1]:
                    all_data.append({
                        "indicator": name,
                        "year": rec.get("date"),
                        "value": rec.get("value"),
                    })
                print(f"  {name}: {len(data[1])} 条")
        except Exception as e:
            print(f"  {name}: 失败 ({e})")
        time.sleep(0.3)

    df = pd.DataFrame(all_data)
    out = OUTPUT_DIR / "worldbank_population_china.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"  总计 {len(df)} 条 → {out}")


if __name__ == "__main__":
    OUTPUT_DIR = get_output_dir("census")
    collect_province_population()
    collect_worldbank_population()
    print("[S7] 完成！")
