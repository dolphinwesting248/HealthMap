"""
S2-Clean: 医疗机构 POI 清洗
输入: data/raw/health_resource/medical_poi.csv
输出: data/cleaned/health_resource_poi.csv
"""
import math
import pandas as pd
from pathlib import Path
from utils import CLEANED_DIR, normalize_province, log

BD_X_PI = 3.14159265358979324 * 3000.0 / 180.0
EE = 0.00669342162296594323
A = 6378245.0


def _transform_lat(x, y):
    ret = -100.0 + 2.0*x + 3.0*y + 0.2*y*y + 0.1*x*y + 0.2*math.sqrt(abs(x))
    ret += (20.0*math.sin(6.0*x*math.pi) + 20.0*math.sin(2.0*x*math.pi)) * 2.0/3.0
    ret += (20.0*math.sin(y*math.pi) + 40.0*math.sin(y/3.0*math.pi)) * 2.0/3.0
    ret += (160.0*math.sin(y/12.0*math.pi) + 320.0*math.sin(y*math.pi/30.0)) * 2.0/3.0
    return ret


def _transform_lng(x, y):
    ret = 300.0 + x + 2.0*y + 0.1*x*x + 0.1*x*y + 0.1*math.sqrt(abs(x))
    ret += (20.0*math.sin(6.0*x*math.pi) + 20.0*math.sin(2.0*x*math.pi)) * 2.0/3.0
    ret += (20.0*math.sin(x*math.pi) + 40.0*math.sin(x/3.0*math.pi)) * 2.0/3.0
    ret += (150.0*math.sin(x/12.0*math.pi) + 300.0*math.sin(x/30.0*math.pi)) * 2.0/3.0
    return ret


def wgs84_to_gcj02(lng, lat):
    dlat = _transform_lat(lng - 105.0, lat - 35.0)
    dlng = _transform_lng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * math.pi
    magic = 1 - EE * math.sin(radlat) ** 2
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((A * (1 - EE)) / (magic * sqrtmagic) * math.pi)
    dlng = (dlng * 180.0) / (A / sqrtmagic * math.cos(radlat) * math.pi)
    return lng + dlng, lat + dlat


def gcj02_to_wgs84(lng, lat):
    """迭代法: gcj = f(wgs) → 逆解 wgs (收敛到 <1e-6 度)"""
    wlng, wlat = lng, lat
    for _ in range(12):
        glng, glat = wgs84_to_gcj02(wlng, wlat)
        wlng += lng - glng
        wlat += lat - glat
    return wlng, wlat


def bd09_to_wgs84(bd_lon, bd_lat):
    """BD-09 → GCJ-02 (标准极坐标公式) → WGS-84 (迭代逆变换)"""
    x = bd_lon - 0.0065
    y = bd_lat - 0.006
    z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * BD_X_PI)
    theta = math.atan2(y, x) - 0.000003 * math.cos(x * BD_X_PI)
    gcj_lon, gcj_lat = z * math.cos(theta), z * math.sin(theta)
    return gcj02_to_wgs84(gcj_lon, gcj_lat)


def clean():
    print("\n[S2] 清洗医疗 POI 数据...")
    raw = Path(__file__).resolve().parent.parent.parent / "data" / "raw" / "health_resource" / "medical_poi.csv"
    if not raw.exists():
        log(f"文件不存在: {raw}"); return

    df = pd.read_csv(raw, dtype=str)
    log(f"原始: {df.shape[0]} 行 × {df.shape[1]} 列")

    # 坐标转换 BD-09 → WGS-84
    lng = pd.to_numeric(df["longitude"], errors="coerce")
    lat = pd.to_numeric(df["latitude"], errors="coerce")
    wgs = []
    for lo, la in zip(lng, lat):
        if pd.notna(lo) and pd.notna(la) and lo != 0 and la != 0:
            wgs.append(bd09_to_wgs84(lo, la))
        else:
            wgs.append((None, None))
    df["longitude_wgs84"] = [w[0] for w in wgs]
    df["latitude_wgs84"] = [w[1] for w in wgs]

    # 坐标合理性检查: WGS-84 应落在中国范围内, 否则转换有误
    in_china = df["longitude_wgs84"].between(72, 136) & df["latitude_wgs84"].between(15, 55)
    log(f"坐标在中国范围外 (转换异常): {(~in_china).sum()} 行")
    df = df[in_china]

    # 坐标缺失删除
    before = len(df)
    df = df.dropna(subset=["longitude_wgs84", "latitude_wgs84"])
    log(f"坐标缺失删除: {before - len(df)} 行")

    # 省份映射
    if "city" in df.columns:
        df["province"] = df["city"].apply(normalize_province)

    # 去重
    before = len(df)
    df = df.drop_duplicates(subset=["id"])
    log(f"去重: {before} → {len(df)} 行")

    out = CLEANED_DIR / "health_resource_poi.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")
    log(f"输出: {df.shape[0]} 行 × {df.shape[1]} 列 → {out}")


if __name__ == "__main__":
    clean()
