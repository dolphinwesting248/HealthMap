"""
Q1-Integration: 省级环境暴露聚合
输入 (cleaned):
     data/cleaned/env_air_quality.csv     (省会城市×日)
     data/cleaned/env_water_quality.csv   (监测站点×日)
     data/cleaned/env_weather_{y}.csv     (ERA5 格点×日时次)
     data/cleaned/geo_boundary.geojson    (省级边界, 格点→省归属)
输出: data/integrated/q1_environment_health/q1_env_exposure_province.csv (省×年宽表)

方法: 空气按省会城市→省 mean/max; 水按 station→省 mean;
     ERA5 格点中心 → 最近省中心归属后聚合年均值。
"""
import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROCESSING_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = PROCESSING_DIR.parent
CLEANED = PROJECT_ROOT / "data" / "cleaned"
OUT_DIR = PROJECT_ROOT / "data" / "integrated" / "q1_environment_health"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "q1_env_exposure_province.csv"
sys.path.insert(0, str(PROCESSING_DIR / "cleaning"))
from utils import normalize_province


def log(msg):
    print(f"  {msg}", flush=True)


def province_centers():
    """cleaned geo_boundary → 34 省级 feature 平均中心 (lon, lat)"""
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
            centers[p["name"]] = (float(np.mean(lons)), float(np.mean(lats)))
    return centers


def _match_province(df, lon_col, lat_col, centers):
    """格点/站点 → 最近省中心归属 (向量逐省比较, O(点×省))"""
    names = list(centers)
    clon = np.array([centers[n][0] for n in names])
    clat = np.array([centers[n][1] for n in names])
    glon = np.deg2rad(df[lon_col].to_numpy(float))
    glat = np.deg2rad(df[lat_col].to_numpy(float))
    best_i = np.zeros(len(df), dtype=int)
    best_d = None
    for i, n in enumerate(names):
        d = (np.deg2rad(clat[i]) - glat) ** 2 + \
            ((np.deg2rad(clon[i]) - glon) * np.cos(glat)) ** 2
        if best_d is None:
            best_i[:] = i
            best_d = d
        else:
            upd = d < best_d
            best_i[upd] = i
            best_d = np.where(upd, d, best_d)
    df = df.copy()
    df["province"] = [names[i] for i in best_i]
    return df


def air_exposure():
    """省会城市×日 → 省×年"""
    df = pd.read_csv(CLEANED / "env_air_quality.csv")
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    g = df.groupby(["province", "year"]).agg(
        air_pm25_mean=("pm25", "mean"), air_pm25_max=("pm25", "max"),
        air_pm10_mean=("pm10", "mean"),
        air_aqi_mean=("aqi", "mean"), air_aqi_max=("aqi", "max"),
        air_o3_mean=("o3", "mean"),
        air_days_aqi_gt100=("aqi", lambda s: int((s > 100).sum())),
        air_temp_mean=("temp_c", "mean"), air_precip_sum=("precipitation", "sum"),
        air_no2_mean=("no2", "mean"),
        air_precip_days=("precipitation", lambda s: int((s > 1).sum())),
    ).reset_index()
    g["province"] = g["province"].apply(normalize_province)  # 英文名 → 标准中文短名
    log(f"air: {len(g)} 省×年 (来自 31 省会, 2016-2025 中仅覆盖实际有数据年份)")
    return g


def water_exposure():
    """水体检出: 自带 province 列 (英文名, 仅10省覆盖), 直接 normalize, 不用坐标匹配。
    附带全谱指标 (pH/营养盐/重金属/微生物/污染等级超标率)"""
    df = pd.read_csv(CLEANED / "env_water_quality.csv")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["year"] = df["date"].dt.year
    df["province"] = df["province"].apply(normalize_province)
    g = df.groupby(["province", "year"]).agg(
        water_wqi_mean=("Water_Quality_Index", "mean"),
        water_wqi_min=("Water_Quality_Index", "min"),
        water_do_mean=("Dissolved_Oxygen_mg_L", "mean"),
        water_cod_mean=("COD_mg_L", "mean"),
        water_nh3n_mean=("Ammonia_N_mg_L", "mean"),
        water_pH_mean=("pH", "mean"),
        water_total_nitrogen=("Total_Nitrogen_mg_L", "mean"),
        water_total_phos_mean=("Total_Phosphorus_mg_L", "mean"),
        water_nitrate_mean=("Nitrate_mg_L", "mean"),
        water_nitrite_mean=("Nitrite_mg_L", "mean"),
        water_bod_mean=("BOD_mg_L", "mean"),
        water_pM_mean=("Heavy_Metals_Pb_ug_L", "mean"),
        water_cd_mean=("Heavy_Metals_Cd_ug_L", "mean"),
        water_hg_mean=("Heavy_Metals_Hg_ug_L", "mean"),
        water_coliform_mean=("Coliform_Count_CFU_100mL", "mean"),
        water_polluted_frac=("Pollution_Level",
                             lambda s: float((s.astype(str).str.lower() != "excellent").mean())),
        water_stations=("Monitoring_Station", "nunique"),
    ).reset_index()
    log(f"water: {len(g)} 省×年 (自带 province 覆盖 10 主要省)")
    return g


def era5_exposure():
    """ERA5 栅格 → 省×年

    空间关联升级: 用严格 Point-in-Polygon 判定格点归属 (验证显示"最近省中心"近似
    与 PIP 仅 33% 一致)。落在国界/海上的格点不属于任何省 → 直接剔除, 不参与省均,
    避免把海洋格点算进沿海省份的气象均值。
    """
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))  # 同目录 spatial_join

    from spatial_join import assign_by_polygon, province_polygons
    polys = province_polygons()
    if not polys:
        log("无省多边形可匹配")
        return None
    frames = []
    for fp in sorted(glob.glob(str(CLEANED / "env_weather_*.csv"))):
        year = int(fp.rsplit("_", 1)[-1].split(".")[0])
        log(f"  ERA5 {year}: 格点→省匹配 (PIP)")
        df = pd.read_csv(fp, usecols=["latitude", "longitude",
                                      "wind_u_10m", "wind_v_10m",
                                      "dewpoint_2m_K", "temperature_2m_K"])
        df["wind_speed"] = np.hypot(df["wind_u_10m"], df["wind_v_10m"])
        df["year"] = year
        df = assign_by_polygon(df, "longitude", "latitude", polys)
        n_all = len(df)
        df = df[df["province_pip"].notna()]
        log(f"    国境内格点/时次 {len(df)} ({len(df)/n_all:.1%}), 境外(海/邻国)剔除 {n_all-len(df)}")
        g = df.groupby(["province_pip", "year"]).agg(
            weather_t2m_mean=("temperature_2m_K", "mean"),
            weather_d2m_mean=("dewpoint_2m_K", "mean"),
            weather_wind_mean=("wind_speed", "mean"),
            weather_wind_max=("wind_speed", "max"),
            weather_n_grid=("longitude", "count"),
        ).reset_index().rename(columns={"province_pip": "province"})
        frames.append(g)
    out = pd.concat(frames, ignore_index=True)
    log(f"era5: {len(out)} 省×年")
    return out


def clean():
    print("\n[Q1-Integration] 省级环境暴露聚合...")
    air = air_exposure()
    water = water_exposure()
    wth = era5_exposure()

    df = air.merge(water, on=["province", "year"], how="outer")
    if wth is not None:
        df = df.merge(wth, on=["province", "year"], how="outer")

    df.to_csv(OUT_FILE, index=False, encoding="utf-8-sig")
    log(f"输出: {len(df)} 省×年 → {OUT_FILE}")


if __name__ == "__main__":
    clean()
