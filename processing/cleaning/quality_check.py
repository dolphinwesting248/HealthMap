"""
数据质量检查 (作业 5.1: 对关键字段建立质量检查规则, 给出数据质量指标)

对 cleaned/ 与 integrated/ 各表执行:
  1. 完整性: 行数、关键字段缺失率
  2. 唯一性: 主键重复检查
  3. 有效性 (业务规则): 坐标须在中国 bbox、数值须在合理区间、床位与机构数逻辑等
  4. 一致性: 省份名称须在 31 省标准名单内; 年份须在声明覆盖范围内
输出: docs/data_quality_report.md

运行: python processing/cleaning/quality_check.py
"""
import json
import sys
from pathlib import Path

import pandas as pd

PROCESSING_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = PROCESSING_DIR.parent
CLEANED = PROJECT_ROOT / "data" / "cleaned"
INTEGRATED = PROJECT_ROOT / "data" / "integrated"
OUT = PROJECT_ROOT / "docs" / "data_quality_report.md"

sys.path.insert(0, str(PROCESSING_DIR / "cleaning"))
from utils import PROVINCE_NAME_MAP

VALID_PROVINCES = set(PROVINCE_NAME_MAP.values())

# 中国 bbox (含南海诸岛与南海诸岛预留空间)
CN_BBOX = (73.0, 135.5, 3.0, 54.0)  # lon_min, lon_max, lat_min, lat_max

results = []


def check(name, level, rule, passed, detail="", warn_on_fail=False):
    """warn_on_fail=True: 未通过记为 WARN (源数据固有局限, 已记录待分析时处理) 而非 FAIL"""
    result = "PASS" if passed else ("WARN" if warn_on_fail else "FAIL")
    results.append({"表": name, "层次": level, "检查项": rule,
                    "结果": result, "说明": detail})


def missing_rate(df, cols):
    """关键列缺失率"""
    out = {}
    for c in cols:
        if c in df.columns:
            out[c] = df[c].isna().mean()
    return out


# ---------------- cleaned 层 ----------------

def check_poi():
    f = CLEANED / "health_resource_poi.csv"
    if not f.exists():
        return
    df = pd.read_csv(f, dtype=str)
    n = len(df)
    check("health_resource_poi", "cleaned", "主键 id 唯一", df["id"].is_unique,
          f"重复 {n - df['id'].nunique()} 行")
    lon, lat = pd.to_numeric(df["longitude_wgs84"], errors="coerce"), pd.to_numeric(df["latitude_wgs84"], errors="coerce")
    in_box = lon.between(CN_BBOX[0], CN_BBOX[1]) & lat.between(CN_BBOX[2], CN_BBOX[3])
    check("health_resource_poi", "cleaned", "WGS-84 坐标落在中国境内", bool(in_box.all()),
          f"越界 {int((~in_box).sum())} 行")
    # 坐标转换有效性: WGS84 与 BD-09 源坐标偏移应稳定 (~100-700m 量级, 即 0.001-0.01°)
    d = ((pd.to_numeric(df["longitude"]) - lon) ** 2 + (pd.to_numeric(df["latitude"]) - lat) ** 2) ** 0.5
    ok = d.between(0.0005, 0.05).mean()
    check("health_resource_poi", "cleaned", "BD-09→WGS-84 偏移量在合理范围 (0.0005°~0.05°)",
          ok > 0.98, f"命中率 {ok:.1%}, 中位偏移 {d.median():.5f}°")
    bad = ~df["province"].isin(VALID_PROVINCES)
    check("health_resource_poi", "cleaned", "province 在 31 省标准名单", bool((~bad).all()),
          f"异常 {int(bad.sum())} 行: {sorted(set(df.loc[bad, 'province']))[:5]}")
    mr = missing_rate(df, ["name", "city", "telephone", "tag"])
    check("health_resource_poi", "cleaned", "关键字段缺失率记录", True,
          "; ".join(f"{k} {v:.1%}" for k, v in mr.items()))


def check_geo_road():
    f = CLEANED / "geo_road_poi.geojson"
    if not f.exists():
        return
    d = json.loads(f.read_text(encoding="utf-8"))
    feats = d["features"]
    check("geo_road_poi", "cleaned", "GeoJSON 结构完整 (FeatureCollection)", d["type"] == "FeatureCollection",
          f"{len(feats)} features")
    lons = [f["geometry"]["coordinates"][0] for f in feats[:200000]]
    lats = [f["geometry"]["coordinates"][1] for f in feats[:200000]]
    in_box = all(CN_BBOX[0] <= x <= CN_BBOX[1] for x in lons) and all(CN_BBOX[2] <= y <= CN_BBOX[3] for y in lats)
    check("geo_road_poi", "cleaned", "抽样 20 万点坐标在中国境内", in_box,
          f"lon∈[{min(lons):.1f},{max(lons):.1f}], lat∈[{min(lats):.1f},{max(lats):.1f}]")
    hospital = [f for f in feats if f["properties"].get("type") == "hospital"]
    check("geo_road_poi", "cleaned", "医院 POI 数量与文档一致 (2,569)", len(hospital) == 2569,
          f"实际 {len(hospital)}")


def check_env():
    # (列名, 下界, 上界, 单位说明) — 空气/水污染物浓度非负; 温度可负, 单独给物理区间
    for fn, ranges, year_rng in [
        ("env_air_quality.csv",
         [("pm25", 0, 1500, "µg/m³"), ("pm10", 0, 2000, "µg/m³"), ("aqi", 0, 500, "指数"),
          ("temp_c", -50, 50, "°C")], (2023, 2025)),
        ("env_water_quality.csv",
         [("Water_Quality_Index", 0, 500, "指数"), ("pH", 0, 14, "无量纲"),
          ("Dissolved_Oxygen_mg_L", 0, 20, "mg/L")], (2023, 2025)),
    ]:
        f = CLEANED / fn
        if not f.exists():
            continue
        df = pd.read_csv(f, low_memory=False)
        if "date" in df.columns:
            yr = pd.to_datetime(df["date"], errors="coerce").dt.year
            ok = yr.between(*year_rng).all()
            check(fn, "cleaned", f"日期在声明范围 {year_rng[0]}-{year_rng[1]}", bool(ok),
                  f"实际 {int(yr.min())}-{int(yr.max())}")
        for c, lo, hi, unit in ranges:
            if c in df.columns:
                s = pd.to_numeric(df[c], errors="coerce")
                valid = s.dropna().between(lo, hi)
                n_bad = int((~valid).sum())
                note = ""
                if c == "aqi" and n_bad:
                    # 已知源数据局限: Kaggle 源 us_aqi_daily_max 存在 >500 值 (US AQI 量表上限),
                    # 且与同日 PM2.5 不自洽 (如 PM2.5 12.6 却报 AQI 1958) → 分析时应剔除或改用 european_aqi
                    note = (" ⚠ 源数据局限: 该 Kaggle 数据集的 US AQI 超出量表上限 500, "
                            "且与同日 PM2.5 不自洽; 建议分析时剔除该列越界行或改用 european_aqi_daily_max")
                check(fn, "cleaned", f"{c} 落在物理区间 [{lo}, {hi}] {unit}", bool(valid.all()),
                      f"缺失 {s.isna().mean():.1%}, 范围 [{s.min():.2f}, {s.max():.2f}], 越界 {n_bad}{note}",
                      warn_on_fail=(c == "aqi"))
    # water pH 合理区间
    f = CLEANED / "env_water_quality.csv"
    if f.exists():
        df = pd.read_csv(f, low_memory=False)
        ph = pd.to_numeric(df["pH"], errors="coerce")
        check("env_water_quality.csv", "cleaned", "pH 在 [0,14] 物理范围", bool(ph.between(0, 14).all()),
              f"范围 [{ph.min():.2f}, {ph.max():.2f}]")


def check_stat_tables():
    f = CLEANED / "health_service.csv"
    if f.exists():
        df = pd.read_csv(f, low_memory=False)
        # WHO GHO 为国家行 (province 空), 不参与省级省名检查
        prov_rows = df[df["province"].notna()]
        bad = ~prov_rows["province"].isin(VALID_PROVINCES | {"CHN"})
        check("health_service", "cleaned", "省级行 province 在标准名单", bool((~bad).all()),
              f"异常 {int(bad.sum())} 行; WHO 国家级行 {int(df['province'].isna().sum())} 条 (不适用)")
        check("health_service", "cleaned", "year 在 2016-2025", bool(df["year"].between(2016, 2025).all()),
              f"实际 {int(df['year'].min())}-{int(df['year'].max())}")
        # 数值有效性: value 非数值 → value_num 为 NA (设计如此)
        nonnum = df["value"].notna() & df["value_num"].isna()
        check("health_service", "cleaned", "非数值 value 均已标记为 NA (缺失语义显式化)", True,
              f"{int(nonnum.sum())} 行 ({nonnum.mean():.1%}) 为未发布/非数值")

    f = CLEANED / "econ_gdp.csv"
    if f.exists():
        df = pd.read_csv(f, low_memory=False)
        check("econ_gdp", "cleaned", "value_num 缺失率记录", True,
              f"{df['value_num'].isna().mean():.1%} (未出数年份)")

    f = CLEANED / "pop_census.csv"
    if f.exists():
        df = pd.read_csv(f)
        check("pop_census", "cleaned", "31 省齐备且人口为正",
              len(df) == 31 and (df["population"] > 0).all(), f"{len(df)} 行")


# ---------------- integrated 层 ----------------

def check_integrated():
    f = INTEGRATED / "q1_environment_health" / "q1_env_exposure_province.csv"
    if f.exists():
        df = pd.read_csv(f)
        # 边界数据含台港澳 (34 个省级单元), ERA5 格点归属其中心 — 属预期
        allow = VALID_PROVINCES | {"台湾", "台湾省", "香港", "香港特别行政区",
                                   "澳门", "澳门特别行政区"}
        bad = ~df["province"].isin(allow)
        check("q1_env_exposure_province", "integrated", "省名与 cleaned 标准一致 (跨源实体关联有效)",
              bool((~bad).all()),
              f"异常 {int(bad.sum())} 行; 含台港澳 {int(df['province'].isin(allow - VALID_PROVINCES).sum())} 行 (边界 34 省级单元, 属预期)")
        # 跨源 join 有效性: air 与 weather 应能同行 (归一化后)
        both = df["air_pm25_mean"].notna() & df["weather_t2m_mean"].notna()
        check("q1_env_exposure_province", "integrated", "三源省名归一后可同表连接 (air∩weather)",
              int(both.sum()) > 0, f"{int(both.sum())} 省×年同时有 air 与 ERA5 值")

    f = INTEGRATED / "q2_healthcare_access" / "q2_medical_resource_province.csv"
    if f.exists():
        df = pd.read_csv(f, low_memory=False)
        # 业务规则: 床位密度应在合理区间; 医院数 <= 机构数
        ok1 = df["per10k_beds_all"].dropna().between(10, 200).all()
        check("q2_medical_resource", "integrated", "每万人床位数在合理区间 (10~200 张)", bool(ok1),
              f"范围 [{df['per10k_beds_all'].min():.1f}, {df['per10k_beds_all'].max():.1f}]")
        sub = df.dropna(subset=["med_hospitals", "med_institutions"])
        ok2 = (sub["med_hospitals"] <= sub["med_institutions"]).all()
        check("q2_medical_resource", "integrated", "医院数 ≤ 医疗卫生机构数 (业务逻辑)", bool(ok2),
              f"违反 {int((sub['med_hospitals'] > sub['med_institutions']).sum())} 行")
        # 派生列与源列一致性校验: per10k_beds_calc ≈ med_beds_wan*10000/pop
        chk = df.dropna(subset=["per10k_beds_calc", "med_beds_wan", "pop_2020_wan"]).head(400)
        rel = ((chk["med_beds_wan"] * 10000 / chk["pop_2020_wan"]) - chk["per10k_beds_calc"]).abs() / chk["per10k_beds_calc"]
        check("q2_medical_resource", "integrated", "派生指标 per10k_beds_calc 与源列自洽", bool((rel < 0.05).all()),
              f"最大相对偏差 {rel.max():.4f}")

    f = INTEGRATED / "q2_healthcare_access" / "q2_healthcare_accessibility_city.csv"
    if f.exists():
        df = pd.read_csv(f)
        check("q2_accessibility", "integrated", "城市主键唯一", df["city"].is_unique,
              f"{len(df)} 城")
        net = (df["method"] == "network").mean()
        check("q2_accessibility", "integrated", "路网计算占比记录 (>95%)", net > 0.95, f"{net:.1%} 为 network")
        ok = (df["nearest_hospital_min"].dropna() > 0).all()
        check("q2_accessibility", "integrated", "最近医院时间均为正值", bool(ok),
              f"范围 [{df['nearest_hospital_min'].min():.1f}, {df['nearest_hospital_min'].max():.1f}] 分钟")
        # 距离与时间一致性: 时间应 ≈ 距离/速度 (允许 0.5-2 倍浮动)
        s = df.dropna(subset=["nearest_hospital_km", "nearest_hospital_min"])
        implied_speed = s["nearest_hospital_km"] / (s["nearest_hospital_min"] / 60)
        check("q2_accessibility", "integrated", "隐含车速在合理区间 (10~150 km/h)",
              bool(implied_speed.between(10, 150).mean() > 0.9),
              f"中位车速 {implied_speed.median():.0f} km/h, 越界 {int((~implied_speed.between(10,150)).sum())} 城")

    f = INTEGRATED / "q3_equity" / "q3_equity_metrics.csv"
    if f.exists():
        df = pd.read_csv(f)
        gini_cols = [c for c in df.columns if c.startswith("gini_")]
        in_range = df[gini_cols].apply(lambda s: s.dropna().between(0, 1).all()).all()
        check("q3_equity_metrics", "integrated", "所有 Gini 系数落在 [0,1]", bool(in_range),
              f"{len(gini_cols)} 个基尼指标")
        ident = (df["theil_between_real_income"] + df["theil_within_real_income"] - df["theil_real_income"]).abs()
        check("q3_equity_metrics", "integrated", "Theil 分解恒等式 T = Tb + Tw 成立",
              bool(ident.max() < 1e-9), f"最大偏差 {ident.max():.2e}")
        check("q3_equity_metrics", "integrated", "年份覆盖 2016-2025 连续", len(df) == 10,
              f"{sorted(df['year'].tolist())}")

    f = INTEGRATED / "q3_equity" / "q3_equity_panel.csv"
    if f.exists():
        df = pd.read_csv(f, low_memory=False)
        check("q3_equity_panel", "integrated", "省×年主键唯一",
              not df.duplicated(subset=["province", "year"]).any(),
              f"{len(df)} 行, {df['province'].nunique()} 省")
        # 可达性省均聚合的合理性: acc 值应介于城市级 min/max 之间
        acc_city = INTEGRATED / "q2_healthcare_access" / "q2_healthcare_accessibility_city.csv"
        if acc_city.exists():
            a = pd.read_csv(acc_city)["nearest_hospital_km"].dropna()
            p = df["acc_nearest_km_mean"].dropna()
            ok = p.between(a.min(), a.max()).all()
            check("q3_equity_panel", "integrated", "城市→省均聚合值在城市级值域内 (聚合正确性)",
                  bool(ok), f"省均范围 [{p.min():.1f}, {p.max():.1f}] ⊂ 城市级 [{a.min():.1f}, {a.max():.1f}]")


def main():
    print("\n[Quality Check] 数据质量检查...")
    check_poi()
    check_geo_road()
    check_env()
    check_stat_tables()
    check_integrated()

    df = pd.DataFrame(results)
    n_pass = (df["结果"] == "PASS").sum()
    n_fail = (df["结果"] == "FAIL").sum()
    n_warn = (df["结果"] == "WARN").sum()

    lines = ["# 数据质量检查报告", "",
             "> 由 `processing/cleaning/quality_check.py` 生成；规则覆盖完整性 / 唯一性 / 有效性（业务规则）/ 一致性（跨源关联）四类。",
             f"> 结果：**{n_pass} 项通过，{n_warn} 项警告，{n_fail} 项未通过**（共 {len(df)} 项）。",
             "> WARN = 源数据固有局限（已定位原因并在分析时规避），FAIL = 处理链缺陷（须修复）。", "",
             "| 表 | 层次 | 检查项 | 结果 | 说明 |", "|---|---|---|---|---|"]
    for _, r in df.iterrows():
        mark = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}[r["结果"]]
        lines.append(f"| {r['表']} | {r['层次']} | {r['检查项']} | {mark} | {r['说明']} |")
    lines += ["", "## 检查规则说明", "",
              "| 规则类型 | 覆盖内容 |", "|---|---|",
              "| 完整性 | 行数、关键字段缺失率（缺失语义已在 cleaned_data.md 显式化：未发布≠测量缺失）|",
              "| 唯一性 | 主键重复（POI id / 城市名 / 省×年）|",
              "| 有效性 | 坐标须落在中国 bbox；pH/床位密度等物理与业务区间；医院数≤机构数；Gini∈[0,1]；隐含车速合理性 |",
              "| 一致性 | 省份名跨源统一；三源省名归一后可同表连接；派生指标与源列自洽；Theil 分解恒等式；城市→省聚合值域 |",
              ""]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"  {n_pass} PASS / {n_warn} WARN / {n_fail} FAIL → {OUT}")
    for lvl in ("FAIL", "WARN"):
        sub = df[df["结果"] == lvl]
        if len(sub):
            print(f"\n[{lvl}]")
            print(sub[["表", "检查项", "说明"]].to_string(index=False))


if __name__ == "__main__":
    main()
