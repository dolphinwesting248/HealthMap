"""
Q3-Integration: Q3 分析面板 (省×年 全要素底表)
输入:
     data/integrated/q1_environment_health/q1_env_health_panel.csv     (环境+结局+收入)
     data/integrated/q2_healthcare_access/q2_medical_resource_province.csv (资源/POI)
     data/integrated/q2_healthcare_access/q2_healthcare_accessibility_city.csv (城市级可达性)
     data/cleaned/econ_labor.csv   (卫生/社会服务业就业, 控制变量)
     data/cleaned/pop_wb.csv       (World Bank 国家级背景, 按 year 挂接)
     data/cleaned/geo_boundary → 省 AREAS (通过 Q2 表已带 windows 聚合)
输出: data/integrated/q3_equity/q3_equity_panel.csv (省×年)

可达性城市级→省级聚合: 城市可达性行按所在地省名聚合 mean (city 无直接省列,
通过 geo_boundary 城市→省的映射 (city 的 parent) 得到)。
"""
import json
from pathlib import Path

import pandas as pd

PROCESSING_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = PROCESSING_DIR.parent
CLEANED = PROJECT_ROOT / "data" / "cleaned"
INTG = PROJECT_ROOT / "data" / "integrated"
Q1 = INTG / "q1_environment_health"
Q2 = INTG / "q2_healthcare_access"
OUT_DIR = INTG / "q3_equity"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "q3_equity_panel.csv"

# 列名兼容: cleaned pop_wb 用的 indicator_name 语义列名
WB_RENAME = {
    "life_expectancy": "wb_life_expectancy",
    "urbanization_rate": "wb_urbanization_rate",
    "gdp_per_capita": "wb_gdp_per_capita",
    "health_expenditure_gdp": "wb_health_exp_gdp",
    "physicians_per_1000": "wb_physicians_per_1000",
    "hospital_beds_per_1000": "wb_beds_per_1000",
    "gini_coefficient": "wb_gini",
}


def log(msg):
    print(f"  {msg}", flush=True)


def city_to_province_map():
    """cleaned geo_boundary: city feature.parent.adcode → 省名; 输出 city_name → province"""
    gb = json.loads((PROJECT_ROOT / "data" / "cleaned" / "geo_boundary.geojson")
                    .read_text(encoding="utf-8"))
    # province adcode → name
    prov_by_adcode = {str(f["properties"].get("adcode")): f["properties"]["name"][:0] or ""
                      for f in gb["features"] if f["properties"].get("level") == "province"}
    ad2name = {}
    for f in gb["features"]:
        p = f["properties"]
        if p.get("level") == "province":
            ad2name[str(p["adcode"])] = p["name"]
    cmap = {}
    for f in gb["features"]:
        p = f["properties"]
        if p.get("level") == "city":
            parent = p.get("parent") or {}
            # parent 可能是 {"adcode":...} 或直含 adcode
            pad = str(parent.get("adcode") or parent)
            if pad in ad2name:
                cmap[p["name"]] = ad2name[pad]
    return cmap


def accessibility_by_province():
    """城市级可达性 → 省级 mean 聚合"""
    acc = pd.read_csv(Q2 / "q2_healthcare_accessibility_city.csv")
    cmap = city_to_province_map()
    acc["province_raw"] = acc["city"].map(cmap)

    # 直辖市/未匹配城市: city 本身可能就是省名 (如 上海东? boundary 内直接 city="上海市")
    # fallback: 在 cmap 未命中时, 用 city 去后缀在省名单中
    provs = sorted(set(cmap.values()))
    import re
    def fallback(city):
        stem = re.sub(r"市|地区|州|盟", "", city)
        for p in provs:
            if stem in p or p in city:
                return p
        return None
    acc.loc[acc["province_raw"].isna(), "province_raw"] = \
        acc.loc[acc["province_raw"].isna(), "city"].apply(fallback)
    acc = acc.rename(columns={"province_raw": "province"})
    # 面板用中文名统一; Q1/Q2 面板键是去掉后缀的省名
    import sys
    sys.path.insert(0, str(PROCESSING_DIR / "cleaning"))
    from utils import normalize_province
    acc["province"] = acc["province"].apply(lambda s: s and s.replace("省", "").replace("市", "")
                                            .replace("壮族自治区", "").replace("回族自治区", "")
                                            .replace("自治区", "").replace("维吾尔", ""))

    acc_agg = acc.groupby("province").agg(
        acc_nearest_km_mean=("nearest_hospital_km", "mean"),
        acc_nearest_km_p90=("nearest_hospital_km", lambda s: float(s.quantile(0.9))),
        acc_nearest_min_mean=("nearest_hospital_min", "mean"),
        acc_nearest_min_p90=("nearest_hospital_min", lambda s: float(s.quantile(0.9))),
        acc_hospitals_30min_mean=("hospitals_30min", "mean"),
        acc_major_nearest_km_mean=("major_nearest_km", "mean"),
        acc_major_nearest_km_p90=("major_nearest_km", lambda s: float(s.quantile(0.9))),
        acc_mean_roundtrip_km=("mean_hospital_km_roundtrip", "mean"),
    ).reset_index()
    return acc_agg


def clean():
    print("\n[Q3-Integration] Q3 分析面板构建...")

    q1 = pd.read_csv(Q1 / "q1_env_health_panel.csv")
    q2_res = pd.read_csv(Q2 / "q2_medical_resource_province.csv")
    acc = accessibility_by_province()

    df = q1.merge(q2_res, on=["province", "year"], how="outer", suffixes=("", "_q2"))
    df = df.merge(acc, on="province", how="left")

    # econ_labor: 卫生与社会工作就业 (万人)
    lab = pd.read_csv(CLEANED / "econ_labor.csv", low_memory=False)
    lab = lab[(lab["indicator"].str.contains("卫生和社会工作", na=False) &
               lab["indicator"].str.contains("城镇单位就业人员", na=False))
              & lab["value_num"].notna()]
    lab_p = lab.pivot_table(index=["province", "year"], columns="indicator",
                            values="value_num", aggfunc="mean").reset_index()
    lab_p.columns = [c.strip() for c in lab_p.columns]
    for c in list(lab_p.columns):
        if "卫生和社会工作" in c:
            lab_p = lab_p.rename(columns={c: "ctrl_healthcare_employment_wan"})
    ctrl = [c for c in lab_p.columns if c in ("province", "year") or c.startswith("ctrl_")]
    df = df.merge(lab_p[ctrl], on=["province", "year"], how="outer")

    # pop_wb 国家级背景 (按 year 挂接)
    wb = pd.read_csv(CLEANED / "pop_wb.csv")
    name_col = "indicator_name" if "indicator_name" in wb.columns else "indicator"
    keep_ind = {"life_expectancy", "urbanization_rate", "gdp_per_capita",
                "health_expenditure_gdp", "physicians_per_1000",
                "hospital_beds_per_1000", "gini_coefficient"}
    wb = wb[wb[name_col].isin(keep_ind)]
    wb_p = wb.pivot_table(index="year", columns=name_col, values="value", aggfunc="mean")
    wb_p.columns = [WB_RENAME.get(c, f"wb_{c}") for c in wb_p.columns]
    wb_p = wb_p.reset_index()
    df = df.merge(wb_p, on="year", how="left")

    df.to_csv(OUT_FILE, index=False, encoding="utf-8-sig")
    log(f"输出: {len(df)} 省×年 × {len(df.columns)-2} 列 → {OUT_FILE}")


if __name__ == "__main__":
    clean()
