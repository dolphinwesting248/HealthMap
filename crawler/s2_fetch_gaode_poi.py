"""
S2: 百度地图医疗机构 POI 数据采集

百度地图 POI 搜索 API
- 注册: https://lbsyun.baidu.com/
- 坐标系: BD-09 (后续需转 WGS-84)
"""
import json
import os
import sys
import time
from pathlib import Path

import pandas as pd
import requests

from config import get_output_dir, PROXIES

# 读取百度 AK
BAIDU_AK = os.getenv("BAIDU_AK", "")

BAIDU_POI_API = "https://api.map.baidu.com/place/v2/search"

# 医疗机构关键词
MEDICAL_QUERIES = [
    "医院", "诊所", "卫生所", "卫生院", "社区卫生服务中心",
    "妇幼保健院", "中医院", "体检中心", "药店",
]

# 全部地级市
ALL_CITIES = [
    # 直辖市
    ("北京", "北京"), ("上海", "上海"), ("天津", "天津"), ("重庆", "重庆"),
    # 华北
    ("石家庄", "石家庄"), ("唐山", "唐山"), ("邯郸", "邯郸"), ("保定", "保定"),
    ("太原", "太原"), ("大同", "大同"), ("济南", "济南"), ("青岛", "青岛"),
    ("烟台", "烟台"), ("潍坊", "潍坊"), ("廊坊", "廊坊"),
    # 东北
    ("沈阳", "沈阳"), ("大连", "大连"), ("长春", "长春"), ("哈尔滨", "哈尔滨"),
    # 华东
    ("南京", "南京"), ("苏州", "苏州"), ("无锡", "无锡"), ("常州", "常州"),
    ("杭州", "杭州"), ("宁波", "宁波"), ("温州", "温州"),
    ("合肥", "合肥"), ("芜湖", "芜湖"),
    ("福州", "福州"), ("厦门", "厦门"), ("泉州", "泉州"),
    ("南昌", "南昌"), ("赣州", "赣州"),
    # 华中
    ("郑州", "郑州"), ("洛阳", "洛阳"),
    ("武汉", "武汉"), ("宜昌", "宜昌"),
    ("长沙", "长沙"), ("株洲", "株洲"),
    # 华南
    ("广州", "广州"), ("深圳", "深圳"), ("东莞", "东莞"), ("佛山", "佛山"),
    ("珠海", "珠海"), ("中山", "中山"),
    ("南宁", "南宁"), ("北海", "北海"),
    ("海口", "海口"),
    # 西南
    ("成都", "成都"), ("绵阳", "绵阳"),
    ("贵阳", "贵阳"), ("昆明", "昆明"),
    # 西北
    ("西安", "西安"), ("兰州", "兰州"), ("乌鲁木齐", "乌鲁木齐"),
    ("西宁", "西宁"), ("银川", "银川"),
    # 补充地级市
    ("淄博", "淄博"), ("济宁", "济宁"), ("泰安", "泰安"), ("德州", "德州"),
    ("滨州", "滨州"), ("东营", "东营"), ("菏泽", "菏泽"), ("聊城", "聊城"),
    ("日照", "日照"), ("威海", "威海"),
    ("平顶山", "平顶山"), ("焦作", "焦作"), ("濮阳", "濮阳"), ("新乡", "新乡"),
    ("许昌", "许昌"), ("信阳", "信阳"), ("南阳", "南阳"),
    ("商丘", "商丘"), ("三门峡", "三门峡"),
    ("上饶", "上饶"), ("景德镇", "景德镇"), ("鹰潭", "鹰潭"), ("萍乡", "萍乡"),
    ("新余", "新余"),
    ("黄石", "黄石"), ("十堰", "十堰"), ("荆州", "荆州"),
    ("襄阳", "襄阳"), ("荆门", "荆门"), ("孝感", "孝感"), ("黄冈", "黄冈"),
    ("咸宁", "咸宁"), ("随州", "随州"),
    ("岳阳", "岳阳"), ("常德", "常德"), ("益阳", "益阳"), ("衡阳", "衡阳"),
    ("郴州", "郴州"), ("邵阳", "邵阳"), ("永州", "永州"), ("怀化", "怀化"),
    ("娄底", "娄底"), ("张家界", "张家界"),
    ("韶关", "韶关"), ("惠州", "惠州"), ("江门", "江门"),
    ("茂名", "茂名"), ("阳江", "阳江"), ("清远", "清远"), ("揭阳", "揭阳"),
    ("潮州", "潮州"), ("汕尾", "汕尾"), ("河源", "河源"), ("梅州", "梅州"),
    ("湛江", "湛江"), ("肇庆", "肇庆"), ("云浮", "云浮"),
    ("柳州", "柳州"), ("桂林", "桂林"), ("梧州", "梧州"),
    ("防城港", "防城港"), ("贵港", "贵港"), ("玉林", "玉林"),
    ("百色", "百色"), ("河池", "河池"), ("崇左", "崇左"), ("来宾", "来宾"),
    ("三亚", "三亚"), ("东方", "东方"), ("琼海", "琼海"), ("万宁", "万宁"),
    ("遵义", "遵义"), ("六盘水", "六盘水"), ("安顺", "安顺"),
    ("大理", "大理"), ("曲靖", "曲靖"), ("玉溪", "玉溪"), ("红河", "红河"),
    ("楚雄", "楚雄"), ("文山", "文山"), ("西双版纳", "西双版纳"),
    ("宝鸡", "宝鸡"), ("汉中", "汉中"), ("咸阳", "咸阳"), ("渭南", "渭南"),
    ("商洛", "商洛"), ("安康", "安康"),
    ("白银", "白银"), ("天水", "天水"), ("平凉", "平凉"), ("庆阳", "庆阳"),
    ("武威", "武威"), ("酒泉", "酒泉"),
    ("包头", "包头"), ("赤峰", "赤峰"), ("通辽", "通辽"),
    ("鄂尔多斯", "鄂尔多斯"), ("巴彦淖尔", "巴彦淖尔"),
    ("石嘴山", "石嘴山"), ("固原", "固原"), ("中卫", "中卫"),
    ("哈密", "哈密"), ("吐鲁番", "吐鲁番"), ("阿克苏", "阿克苏"),
]


# ── 断点续传 ──────────────────────────────────────────────────────────

def load_progress(path: Path) -> set[str]:
    if path.exists():
        return set(json.loads(path.read_text(encoding="utf-8")))
    return set()


def save_progress(path: Path, done: set[str]):
    path.write_text(json.dumps(sorted(done), ensure_ascii=False), encoding="utf-8")


def append_csv(rows: list[dict], csv_path: Path):
    if not rows:
        return
    df = pd.DataFrame(rows)
    write_header = not csv_path.exists() or csv_path.stat().st_size == 0
    df.to_csv(csv_path, mode="a", index=False, header=write_header, encoding="utf-8-sig")


# ── 自检 ──────────────────────────────────────────────────────────────

def check_quota(ak: str) -> bool:
    """测试 API Key 是否可用"""
    try:
        resp = requests.get(BAIDU_POI_API, params={
            "query": "医院", "region": "北京", "ak": ak,
            "output": "json", "scope": 1, "page_size": 1,
        }, timeout=15, proxies=PROXIES)
        data = resp.json()
        status = data.get("status")
        if status == 0:
            total = data.get("total", 0)
            print(f"  API Key 有效, 额度正常 (北京医院总数: {total})")
            return True
        elif status == 240:
            print(f"  API Key 无效或被禁用 (status=240)")
            return False
        elif status == 302:
            print(f"  配额超限 (status=302)")
            return False
        else:
            print(f"  异常: status={status}, message={data.get('message','')}")
            return False
    except Exception as e:
        print(f"  网络错误: {e}")
        return False


# ── POI 搜索 ──────────────────────────────────────────────────────────

def search_pois(ak: str, query: str, region: str) -> list[dict]:
    """搜索某个城市的某个关键词的 POI"""
    all_pois = []
    page = 0
    while page < 20:  # 百度最多返回 400 条（20页 × 20条）
        try:
            resp = requests.get(BAIDU_POI_API, params={
                "query": query, "region": region, "ak": ak,
                "output": "json", "scope": 2,
                "page_size": 20, "page_num": page,
            }, timeout=15, proxies=PROXIES)
            data = resp.json()
            if data.get("status") != 0:
                break
            results = data.get("results", [])
            total = data.get("total", 0)
            if not results:
                break
            for r in results:
                loc = r.get("location", {})
                all_pois.append({
                    "id": r.get("uid", ""),
                    "name": r.get("name", ""),
                    "address": r.get("address", ""),
                    "city": r.get("city", ""),
                    "district": r.get("area", ""),
                    "telephone": r.get("telephone", ""),
                    "longitude": loc.get("lng", 0),
                    "latitude": loc.get("lat", 0),
                    "detail": r.get("detail", ""),
                    "tag": r.get("tag", ""),
                })
            if len(all_pois) >= total:
                break
            page += 1
            time.sleep(0.1)
        except Exception:
            break
    return all_pois


# ── 主流程 ────────────────────────────────────────────────────────────

def collect(ak: str):
    OUTPUT_DIR = get_output_dir("baidu")
    csv_path = OUTPUT_DIR / "medical_poi_all.csv"
    progress_path = OUTPUT_DIR / "progress.json"

    done = load_progress(progress_path)
    print(f"[S2] 百度地图 POI 采集")
    print(f"  已完成 {len(done)} 个任务")

    batch = []
    total_new = 0

    for i, (city, region) in enumerate(ALL_CITIES):
        for query in MEDICAL_QUERIES:
            task_key = f"{city}_{query}"
            if task_key in done:
                continue

            pois = search_pois(ak, query, region)
            done.add(task_key)

            # 去重（按 uid）
            seen = set()
            new = []
            for p in pois:
                if p["id"] and p["id"] not in seen:
                    seen.add(p["id"])
                    p["search_query"] = query
                    new.append(p)

            batch.extend(new)
            total_new += len(new)

            if new:
                print(f"  [{i+1}/{len(ALL_CITIES)}] {city} / {query}: +{len(new)}")

            # 每 50 条保存一次
            if len(batch) >= 50:
                append_csv(batch, csv_path)
                save_progress(progress_path, done)
                batch = []

            time.sleep(0.15)

    # 保存剩余
    if batch:
        append_csv(batch, csv_path)
        save_progress(progress_path, done)

    if csv_path.exists():
        df = pd.read_csv(csv_path)
        print(f"\n  本次新增 {total_new} 条, 总计 {len(df)} 条 → {csv_path}")
        print(f"  文件大小: {csv_path.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    ak = sys.argv[1] if len(sys.argv) > 1 else BAIDU_AK
    if not ak:
        print("用法: python s2_fetch_gaode_poi.py [BAIDU_AK]")
        print("或在 .env 中设置 BAIDU_AK=xxx")
        print("注册: https://lbsyun.baidu.com/")
        sys.exit(1)

    print("[S2] 检查 API 额度...")
    if not check_quota(ak):
        print("  请检查 Key 或等待额度重置")
        sys.exit(1)

    collect(ak)
    print("\n[S2] 完成！")
