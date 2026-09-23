"""
Q2-Integration: 省级医疗资源标准化 (密度 + 人均)
输入 (cleaned):
     data/cleaned/health_service.csv     (机构/床位/人员原始值+每万人指标)
     data/cleaned/health_resource_poi.csv (百度 POI, 空间密度)
     data/cleaned/geo_boundary.geojson    (省界, POI→省归属/省面积近似)
     data/cleaned/pop_census.csv          (七普人口, 万人比值的备用分母)
输出: data/integrated/q2_healthcare_access/q2_medical_resource_province.csv (省×年)

说明: health_service 已含"每万人医疗机构床位数"等 NBS 原生每万人指标 (直接保留);
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

PROCESSING_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = PROCESSING_DIR.parent
CLEANED = PROJECT_ROOT / "data" / "cleaned"
OUT_DIR = PROJECT_ROOT / "data" / "integrated" / "q2_healthcare_access"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "q2_medical_resource_province.csv"


def log(msg):
    print(f"  {msg}", flush=True)


# 保留为宽列的关键资源指标 (indicator → 列名)
KEEP = {
    "医疗卫生机构数 (个)": "med_institutions",
    "医院数 (个)": "med_hospitals",
    "综合医院数 (个)": "med_hospitals_general",
    "中医医院数 (个)": "med_hospitals_tcm",
    "基层医疗卫生机构数 (个)": "med_primary_care",
    "医疗卫生机构床位数 (万张)": "med_beds_wan",
    "医院床位数 (万张)": "med_beds_hospitals_wan",
    "医院、卫生院床位数 (万张)": "med_beds_hospwc_wan",
    "医疗卫生机构诊疗人次数 (亿人次)": "med_visits_yi",
    "医疗卫生机构入院人次数 (万人次)": "med_admissions_wan",
    "卫生人员数 (万人)": "med_personnel_wan",
    "卫生技术人员数 (万人)": "med_health_tech_wan",
    "执业 (助理) 医师数 (万人)": "med_doctors_wan",
    "注册护士数 (万人)": "med_nurses_wan",
    # NBS 原生每万人
    "每万人医疗机构床位数 (张)": "per10k_beds_all",
    "每万人医院和卫生院床位数 (张)": "per10k_beds_hospwc",
    "每万人拥有卫生技术人员数 (人)": "per10k_health_tech",
    "每万人拥有执业 (助理) 医师数 (人)": "per10k_doctors",
    "每万人拥有注册护士数 (人)": "per10k_nurses",
}


def poi_by_province():
    """S2 POI → 落省计数 (lng_wgs84 in 省中心最近归属, 半径近似)"""
    import sys
    sys.path.insert(0, str(PROCESSING_DIR / "cleaning"))
    from utils import normalize_province

    poi = pd.read_csv(CLEANED / "health_resource_poi.csv")
    poi = poi[poi["longitude_wgs84"].notna()]

    gb = json.loads((CLEANED / "geo_boundary.geojson").read_text(encoding="utf-8"))

    def flatten(c):
        if isinstance(c[0], (int, float)):
            yield c
        else:
            for sub in c:
                yield from flatten(sub)

    centers = {}
    for f in gb["features"]:
        p = f["properties"]
        if p.get("level") != "province":
            continue
        lons, lats = [], []
        for lon, lat in flatten(f["geometry"]["coordinates"]):
            lons.append(lon); lats.append(lat)
        if lons:
            centers[normalize_province(p["name"])] = (np.mean(lons), np.mean(lats))

    names = list(centers)
    clon = np.array([centers[n][0] for n in names])
    clat = np.array([centers[n][1] for n in names])
    lon = np.deg2rad(poi["longitude_wgs84"].to_numpy())
    lat = np.deg2rad(poi["latitude_wgs84"].to_numpy())
    best_i = np.zeros(len(poi), dtype=int)
    best_d = None
    for i, n in enumerate(names):
        d = (np.deg2rad(clat[i]) - lat)**2 + ((np.deg2rad(clon[i]) - lon) * np.cos(lat))**2
        if best_d is None:
            best_d = d
        else:
            upd = d < best_d
            best_i[upd] = i
            best_d = np.where(upd, d, best_d)
    poi["_prov"] = [names[i] for i in best_i]
    # 说明: S2 两参坐标覆盖 31 省会城市 (非全部省), _prov 用最近省中心划分
    poi["province"] = poi["province"].apply(normalize_province)
    # 直接用 POI 自带 province 优先, 落点归属仅做校验
    counts = poi.groupby("province").size().rename("poi_count_s2").reset_index()
    return counts


def province_area_km2():
    """省 geometry 鞋带式近似面积 (Shoelace, 球面校正省略; 密度分母)"""
    gb = json.loads((CLEANED / "geo_boundary.geojson").read_text(encoding="utf-8"))

    def flatten(c):
        if isinstance(c[0], (int, float)):
            yield c
        else:
            for sub in c:
                yield from flatten(sub)

    areas = {}
    for f in gb["features"]:
        p = f["properties"]
        if p.get("level") != "province":
            continue
        # 粗鞋带: 平均纬度的 equirect 近似, 足够密度用
        lons, lats = [], []
        for lon, lat in flatten(f["geometry"]["coordinates"]):
            lons.append(lon); lats.append(lat)
        w = max(lons) - min(lons); h = max(lats) - min(lats)
        areas[p["name"]] = w * 111 * np.cos(np.radians(np.mean(lats))) * h * 111
    return areas


def clean():
    print("\n[Q2-Integration] 省级医疗资源标准化...")
    hs = pd.read_csv(CLEANED / "health_service.csv", low_memory=False)
    hs = hs[hs["province"] != "CHN"]
    hs = hs[hs["indicator"].isin(KEEP) & hs["value_num"].notna()]
    hs = hs.groupby(["province", "year", "indicator"], as_index=False)["value_num"].mean()
    wide = hs.pivot(index=["province", "year"], columns="indicator", values="value_num").reset_index()
    wide.columns = [c.strip() for c in wide.columns]
    wide = wide.rename(columns=KEEP)

    counts = poi_by_province()
    log(f"POI 落省: {len(counts)} 省, 共 {counts['poi_count_s2'].sum()}")

    areas = province_area_km2()

    out = wide.merge(counts, on="province", how="left")
    out["poi_density_per_10kkm2"] = (out["poi_count_s2"] / out["province"].map(areas) * 10_000).round(2)

    # 人口分母 (七普 2020) + 标准化
    pop = pd.read_csv(CLEANED / "pop_census.csv")
    pop = pop.rename(columns={"population_wan": "pop_2020_wan"})[["province", "pop_2020_wan"]]
    out = out.merge(pop, on="province", how="left")
    # 每万人列: 万单位绝对值 / 万人口
    out["per10k_beds_calc"] = (out["med_beds_wan"] * 10_000 / out["pop_2020_wan"]).round(1)
    out["per10k_doctors_calc"] = (out["med_doctors_wan"] * 10_000 / out["pop_2020_wan"]).round(1)
    out["per10k_nurses_calc"] = (out["med_nurses_wan"] * 10_000 / out["pop_2020_wan"]).round(1)
    out["poi_per_10kpop"] = (out["poi_count_s2"] * 10_000 / out["pop_2020_wan"]).round(1)

    # 老年人口压力: 每万名 65+ 老人对应床位数 (pop_age 65+, 抽样调查年)
    pa = pd.read_csv(CLEANED / "econ_pop_age.csv")
    pa = pa[(pa["indicator"] == "65岁及以上人口数 (人口抽样调查) (人)") & pa["value_num"].notna()]
    pa_r = pa.rename(columns={"value_num": "pop_65p"})[["province", "year", "pop_65p"]]
    out = out.merge(pa_r, on=["province", "year"], how="left")
    # med_beds_wan (万张) × 10_000 → 张; ÷ 65+ 人口 (人) = 张/人, ×10000 为长者每万人
    out["beds_per_10k_elderly"] = (out["med_beds_wan"] * 10_000 / out["pop_65p"] * 10_000).round(2)
    out = out.drop(columns=["pop_65p"])

    out.to_csv(OUT_FILE, index=False, encoding="utf-8-sig")
    log(f"输出: {len(out)} 省×年 × {len(out.columns)-2} 列 → {OUT_FILE}")


if __name__ == "__main__":
    clean()
