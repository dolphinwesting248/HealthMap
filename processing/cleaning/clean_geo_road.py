"""
S1-Clean: OSM 路网/医疗设施提取
输入: data/raw/geo_road/china-latest.osm.pbf
输出: data/cleaned/geo_road_poi.geojson

性能说明: 全量扫描用 osmium CLI tags-filter 完成 (C++ 多线程, ~10s);
结果文件仅几 MB, 后续 Python 扫描秒级。若未安装 osmium-tool 则回退 pyosmium 全量扫描 (~70 分钟)。
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils import CLEANED_DIR, RAW_DIR, log

RAW_FILE = RAW_DIR / "geo_road" / "china-latest.osm.pbf"

# 与 TAGS 保持一致的 osmium tags-filter 表达式 (仅节点)
TAG_FILTERS = [
    "n/amenity=hospital", "n/amenity=clinic", "n/amenity=pharmacy", "n/amenity=doctors",
    "n/amenity=dentist", "n/amenity=nursing_home", "n/amenity=blood_bank",
    "n/amenity=laboratory", "n/amenity=school", "n/amenity=university",
    "n/amenity=kindergarten",
    "n/public_transport=station", "n/public_transport=stop_position",
    "n/public_transport=platform",
    "n/social_facility=shelter", "n/social_facility=food_bank",
]


def has_osmium_cli():
    try:
        subprocess.run(["osmium", "--version"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def prefilter_pbf():
    """osmium CLI 预过滤 POI 节点 → 临时小 pbf (C++ 多线程, ~12s)"""
    tmp = Path(tempfile.gettempdir()) / "china_poi_filtered.osm.pbf"
    if tmp.exists() and tmp.stat().st_mtime > RAW_FILE.stat().st_mtime:
        log(f"缓存有效, 复用: {tmp.name}")
        return tmp
    log("osmium CLI 预过滤 POI 节点 (~12s)...")
    cmd = ["osmium", "tags-filter", str(RAW_FILE), *TAG_FILTERS,
           "-o", str(tmp), "--overwrite"]
    subprocess.run(cmd, check=True, capture_output=True)
    log(f"过滤后: {tmp.stat().st_size // 1024} KB → {tmp}")
    return tmp


def clean():
    print("\n[S1] 清洗 OSM 数据...")
    if not RAW_FILE.exists():
        log(f"文件不存在: {RAW_FILE}"); return

    features = []
    tag_counts = {}
    use_cli = has_osmium_cli()
    if use_cli:
        scan_file = prefilter_pbf()
    else:
        scan_file = RAW_FILE
        log("未检测到 osmium CLI, 回退 pyosmium 全量扫描 (~70 分钟)")

    import osmium

    class POIHandler(osmium.SimpleHandler):
        def node(self, n):
            tags = dict(n.tags)
            category = "amenity" if "amenity" in tags else (
                "public_transport" if "public_transport" in tags else
                "social_facility" if "social_facility" in tags else None)
            if category is None:
                return
            val = tags.get(category)
            tag_counts[f"{category}={val}"] = tag_counts.get(f"{category}={val}", 0) + 1
            features.append({
                "osm_id": n.id, "lat": n.location.lat, "lon": n.location.lon,
                "category": category, "type": val,
                "name": tags.get("name", ""), "name_en": tags.get("name:en", ""),
                "addr_street": tags.get("addr:street", ""),
                "phone": tags.get("phone", ""), "website": tags.get("website", ""),
                "healthcare": tags.get("healthcare", ""),
            })

    handler = POIHandler()
    log("扫描过滤后文件...")
    handler.apply_file(str(scan_file), locations=True)
    log(f"提取到 {len(features)} 个 POI")
    for cat, count in sorted(tag_counts.items()):
        log(f"  {cat}: {count}")

    if features:
        geojson = {"type": "FeatureCollection", "features": [
            {"type": "Feature",
             "geometry": {"type": "Point", "coordinates": [f["lon"], f["lat"]]},
             "properties": {k: v for k, v in f.items() if k not in ("lat", "lon")}}
            for f in features]}
        out = CLEANED_DIR / "geo_road_poi.geojson"
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(geojson, fh, ensure_ascii=False)
        log(f"输出: {len(features)} 个 features → {out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    clean()
