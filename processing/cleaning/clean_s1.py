"""
S1 清洗: OpenStreetMap 路网数据
"""
import json
from pathlib import Path

from utils import CLEANED_DIR, log

RAW_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "raw" / "s1_osm" / "china-latest.pbf"

# OSM 中医疗相关标签
MEDICAL_TAGS = {
    "amenity": ["hospital", "clinic", "pharmacy", "doctors", "dentist"],
}


def clean_s1():
    print("\n[S1] 清洗 OSM 路网数据（提取医疗设施）...")
    if not RAW_FILE.exists():
        log(f"原始文件不存在: {RAW_FILE}")
        return

    try:
        import osmium
    except ImportError:
        log("请先安装 osmium: pip install osmium")
        log("或使用 Overpass API 单独导出医疗设施")
        return

    features = []

    class MedicalHandler(osmium.SimpleHandler):
        def node(self, n):
            tags = dict(n.tags)
            for tag_key, values in MEDICAL_TAGS.items():
                if tag_key in tags and tags[tag_key] in values:
                    features.append({
                        "osm_id": n.id,
                        "lat": n.location.lat,
                        "lon": n.location.lon,
                        "amenity": tags.get("amenity", ""),
                        "name": tags.get("name", ""),
                        "name_en": tags.get("name:en", ""),
                        "addr_street": tags.get("addr:street", ""),
                        "addr_city": tags.get("addr:city", ""),
                        "addr_housenumber": tags.get("addr:housenumber", ""),
                        "phone": tags.get("phone", ""),
                        "website": tags.get("website", ""),
                        "healthcare": tags.get("healthcare", ""),
                    })

    handler = MedicalHandler()
    handler.apply_file(str(RAW_FILE), locations=True)
    log(f"提取到 {len(features)} 个医疗设施")

    if features:
        out = CLEANED_DIR / "s1_osm_hospitals.geojson"
        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [f["lon"], f["lat"]]},
                    "properties": {k: v for k, v in f.items() if k not in ("lat", "lon")},
                }
                for f in features
            ],
        }
        with open(out, "w", encoding="utf-8") as f:
            json.dump(geojson, f, ensure_ascii=False)
        log(f"输出: {len(features)} 个 features → {out}")


if __name__ == "__main__":
    clean_s1()
