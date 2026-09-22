"""
S8 清洗: 行政区划边界矢量数据
"""
import json
from pathlib import Path

from utils import CLEANED_DIR, log

RAW_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "raw" / "s8_admin_boundary"

ADCODE_NAME = {
    "100000": "全国", "110000": "北京", "120000": "天津", "130000": "河北",
    "140000": "山西", "150000": "内蒙古", "210000": "辽宁", "220000": "吉林",
    "230000": "黑龙江", "310000": "上海", "320000": "江苏", "330000": "浙江",
    "340000": "安徽", "350000": "福建", "360000": "江西", "370000": "山东",
    "410000": "河南", "420000": "湖北", "430000": "湖南", "440000": "广东",
    "450000": "广西", "460000": "海南", "500000": "重庆", "510000": "四川",
    "520000": "贵州", "530000": "云南", "540000": "西藏", "610000": "陕西",
    "620000": "甘肃", "630000": "青海", "640000": "宁夏", "650000": "新疆",
}


def clean_s8():
    print("\n[S8] 清洗行政区划边界数据...")

    all_features = []
    na_count = 0

    for json_file in sorted(RAW_DIR.glob("*.json")):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            features = data.get("features", [])
            for feat in features:
                props = feat.get("properties", {})
                adcode = str(props.get("adcode", ""))
                name = props.get("name", "")

                # 缺失值处理: name 为空时用 adcode 映射表填充
                if not name and adcode in ADCODE_NAME:
                    name = ADCODE_NAME[adcode]
                    na_count += 1

                feat["properties"] = {
                    "adcode": adcode,
                    "name": name,
                    "level": props.get("level", ""),
                    "parent": props.get("parent", ""),
                }
            all_features.extend(features)
            log(f"  {json_file.name}: {len(features)} 个 features")
        except Exception as e:
            log(f"  {json_file.name}: 错误 {e}")

    geojson = {
        "type": "FeatureCollection",
        "features": all_features,
    }

    out = CLEANED_DIR / "s8_admin_boundary.geojson"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False)

    # 质量报告
    total = len(all_features)
    na_name = sum(1 for f in all_features if not f["properties"].get("name"))
    log(f"--- 数据质量报告 ---")
    log(f"  总 features: {total}")
    log(f"  name 缺失(已用adcode填充): {na_count} 个")
    log(f"  name 仍为空: {na_name} 个")
    log(f"  输出: {out} ({out.stat().st_size // 1024} KB)")
    return geojson


if __name__ == "__main__":
    clean_s8()
