"""
S2 清洗: 百度地图医疗机构 POI
"""
import math
import pandas as pd
from pathlib import Path

from utils import CLEANED_DIR, normalize_province, log

RAW_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "raw" / "s2_baidu" / "medical_poi_all.csv"

# BD-09 → WGS-84
BD_X_PI = 3.14159265358979324 * 3000.0 / 180.0


def bd09_to_wgs84(bd_lon, bd_lat):
    """BD-09 → GCJ-02 → WGS-84"""
    x = bd_lon - 0.0065
    y = bd_lat - 0.006
    z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * BD_X_PI)
    gcj_lon = z + math.atan2(y, x) * 180.0 / 3.14159265358979324
    gcj_lat = math.atan2(y - 0.00002 * math.sin(gcj_lon * BD_X_PI),
                          x - 0.00002 * math.cos(gcj_lon * BD_X_PI)) * 180.0 / 3.14159265358979324
    dlat = gcj_lat - 38.0
    dlon = gcj_lon - 105.0
    magic = math.sin(gcj_lat * 3.14159265358979324 / 180.0)
    magic = 1 - 0.00669342162296594323 * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((6378245.0 * (1 - 0.00669342162296594323)) / (magic * sqrtmagic) * 3.14159265358979324)
    dlon = (dlon * 180.0) / (6378245.0 / sqrtmagic * math.cos(gcj_lat * 3.14159265358979324 / 180.0) * 3.14159265358979324)
    return gcj_lon - dlon, gcj_lat - dlat


def clean_s2():
    print("\n[S2] 清洗百度地图 POI 数据...")
    if not RAW_FILE.exists():
        log(f"原始文件不存在: {RAW_FILE}")
        return

    df = pd.read_csv(RAW_FILE, dtype=str)
    log(f"原始: {df.shape[0]} 行 × {df.shape[1]} 列")

    # 1. 坐标转换 BD-09 → WGS-84
    log("坐标转换: BD-09 → WGS-84")
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

    # 2. 缺失值: 坐标缺失删除（无法空间分析）
    before = len(df)
    df = df.dropna(subset=["longitude_wgs84", "latitude_wgs84"])
    dropped = before - len(df)
    if dropped > 0:
        log(f"坐标缺失删除: {dropped} 行")

    # 3. 统一省份名（优先用 city 列）
    if "city" in df.columns:
        df["province"] = df["city"].apply(normalize_province)
    elif "district" in df.columns:
        df["province"] = df["district"].apply(normalize_province)
    else:
        df["province"] = ""

    # 4. 去重
    before = len(df)
    df = df.drop_duplicates(subset=["id"])
    log(f"去重: {before} → {len(df)} 行")

    # 5. 缺失值报告
    log(f"--- 数据质量报告 ---")
    log(f"  总行数: {len(df)}")
    for col in df.columns:
        na = df[col].isna().sum()
        if na > 0:
            log(f"  {col}: 缺失 {na} 行 ({na/len(df)*100:.1f}%)")

    # 6. 保留核心列
    keep = ["id", "name", "type", "address", "city", "district", "province",
            "telephone", "longitude", "latitude", "longitude_wgs84", "latitude_wgs84",
            "search_query"]
    df = df[[c for c in keep if c in df.columns]]

    # 7. 保存
    out = CLEANED_DIR / "s2_medical_poi.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")
    log(f"输出: {df.shape[0]} 行 × {df.shape[1]} 列 → {out}")
    log(f"省份数: {df['province'].nunique()}")
    return df


if __name__ == "__main__":
    clean_s2()
