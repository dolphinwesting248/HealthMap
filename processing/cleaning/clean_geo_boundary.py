"""
S8-Clean: 行政区划边界清洗
输入: data/raw/geo_boundary/*.json
输出: data/cleaned/geo_boundary.geojson
"""
import json
from pathlib import Path
from utils import CLEANED_DIR, log


def clean():
    print("\n[S8] 清洗行政区划边界...")
    raw_dir = Path(__file__).resolve().parent.parent.parent / "data" / "raw" / "geo_boundary"

    all_features = []
    for f in sorted(raw_dir.glob("*.json")):
        try:
            with open(f, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            features = data.get("features", [])
            for feat in features:
                props = feat.get("properties", {})
                adcode = str(props.get("adcode", ""))
                name = props.get("name", "")
                if not name:
                    name = adcode
                feat["properties"] = {"adcode": adcode, "name": name,
                                       "level": props.get("level", ""), "parent": props.get("parent", "")}
            all_features.extend(features)
        except Exception as e:
            log(f"  {f.name}: 错误 {e}")

    geojson = {"type": "FeatureCollection", "features": all_features}
    out = CLEANED_DIR / "geo_boundary.geojson"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(geojson, fh, ensure_ascii=False)
    log(f"输出: {len(all_features)} 个 features → {out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    clean()
