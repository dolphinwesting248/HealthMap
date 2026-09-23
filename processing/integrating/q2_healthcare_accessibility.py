"""
Integration: 就医可达性计算 (#5, Q2 医疗资源可达性)
输入 (全部为 cleaned data):
     data/cleaned/geo_road_poi.geojson     → OSM 医院 POI (目的地)
     data/cleaned/geo_boundary.geojson     → 行政边界 (省会城市名 + 中心点)
     data/cleaned/health_resource_poi.csv  → 省会城市清单 (S2 POI 覆盖范围)
     data/raw/geo_road/china-latest.osm.pbf → 路网 (原始, 仅此一个 raw 输入)
输出: data/integrated/q2_healthcare_access/q2_healthcare_accessibility_city.csv

性能说明: 每城市以 osmium CLI extract 从全国 pbf 剪出 0.6° 窗口子网 (C++, 1-3s/城),
随后 pyosmium 秒级建图; 禁用此优化时回退 pyosmium 全量扫描 (每城 ~5-70 分钟, 不推荐)。
"""
import heapq
import json
import math
import osmium
import subprocess
import tempfile
from pathlib import Path

PROCESSING_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = PROCESSING_DIR.parent

INPUT_CLEANED = PROJECT_ROOT / "data" / "cleaned"
INPUT_RAW = PROJECT_ROOT / "data" / "raw"       # 仅路网 pbf (无 cleaned 形态)
OUTPUT_DIR = PROJECT_ROOT / "data" / "integrated" / "q2_healthcare_access"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "q2_healthcare_accessibility_city.csv"

# 每城窗口 ~60km 半径 × 0.6°
WINDOW_DEG = 0.6
SPEED = {"motorway": 100, "trunk": 80, "primary": 70, "secondary": 50,
         "tertiary": 40, "residential": 30, "unclassified": 30, "service": 25}
DEFAULT_SPEED = 30
AVG_SPEED_FALLBACK = 40.0


def log(msg):
    print(f"  {msg}", flush=True)


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * r * math.asin(math.sqrt(a))


# ---------- 清洗数据加载 ----------

def _load_hospitals():
    """cleaned geo_road_poi.geojson → 医院 POI (lat, lon, name, healthcare)"""
    gf = INPUT_CLEANED / "geo_road_poi.geojson"
    if not gf.exists():
        log(f"输入不存在: {gf} (先运行 processing/cleaning/clean_geo_road.py)"); return None
    data = json.loads(gf.read_text(encoding="utf-8"))
    hospitals = [
        (f["geometry"]["coordinates"][1], f["geometry"]["coordinates"][0],
         f.get("properties", {}).get("name") or "",
         f.get("properties", {}).get("healthcare") or "")
        for f in data.get("features", [])
        if f.get("properties", {}).get("category") == "amenity"
        and f.get("properties", {}).get("type") == "hospital"
    ]
    log(f"OSM 医院 POI: {len(hospitals)} 个")
    return hospitals


def _load_city_centers():
    """cleaned geo_boundary.geojson → 全部城市级 feature 中心点

    旧版本只对 S2 POI 出现的 60 城 (省会为主) 做可达性;
    现在扩展到 boundary 中全部 363 个城市级 (地级市/直辖市市辖区)。
    S2 只有 60 城 POI, OSM 医院为目的地, 与 S2 城市无关。
    """
    import numpy as np

    gb = json.loads((INPUT_CLEANED / "geo_boundary.geojson").read_text(encoding="utf-8"))
    centers = {}

    def flatten(c):
        if isinstance(c[0], (int, float)):
            yield c
        else:
            for sub in c:
                yield from flatten(sub)

    for feat in gb.get("features", []):
        props = feat.get("properties", {})
        name = (props.get("name") or "")
        if props.get("level") != "city":
            continue
        geom = feat.get("geometry", {})
        lons, lats = [], []
        for lon, lat in flatten(geom.get("coordinates", [])):
            lons.append(lon); lats.append(lat)
        if lons:
            centers[name] = (float(np.mean(lats)), float(np.mean(lons)))
    log(f"城市中心点: {len(centers)} 个 (全部城市级 boundary)")
    return centers


# ---------- 路网子图构建 ----------

def _osmium_extract(center_lon, center_lat, window=WINDOW_DEG):
    """osmium CLI 按窗口剪出子 pbf (C++, 1-3s); 失败返回 None"""
    try:
        subprocess.run(["osmium", "--version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    tmp = _window_cache_path(center_lat, center_lon)
    if tmp.exists():
        if tmp.stat().st_size > 1000:  # 有效缓存
            return tmp
        tmp.unlink()  # 空缓存 (上次可能被中断), 重新提取
    raw = INPUT_RAW / "geo_road" / "china-latest.osm.pbf"
    bbox = f"{center_lon - window},{center_lat - window},{center_lon + window},{center_lat + window}"
    # osmium 依赖输出文件名推断格式, .tmp 后缀不可识别 → 显式指定格式
    subprocess.run(["osmium", "extract", "-b", bbox, str(raw),
                    "-o", str(tmp) + ".tmp", "--overwrite", "--output-format", "osm.pbf"],
                   check=True, capture_output=True)
    # 原子改名, 防止半成品 blob 被复用
    Path(str(tmp) + ".tmp").rename(tmp)
    return tmp


class RoadGraphHandler(osmium.SimpleHandler):
    """从 pbf 提取窗口内 highway 路段为 networkx 图"""

    def __init__(self):
        import networkx as nx
        self.G = nx.Graph()

    def way(self, w):
        if "highway" not in w.tags:
            return
        nodes = [(nd.ref, (nd.location.lat, nd.location.lon)) for nd in w.nodes
                 if nd.location.valid]
        if len(nodes) < 2:
            return
        hw = w.tags["highway"]
        speed = SPEED.get(hw, DEFAULT_SPEED)
        for (u, (ul, uo)), (v, (vl, vo)) in zip(nodes, nodes[1:]):
            d = haversine_km(ul, uo, vl, vo)
            if d <= 0:
                continue
            t = d / speed * 60
            for nid, nloc in ((u, (ul, uo)), (v, (vl, vo))):
                if nid not in self.G:
                    self.G.add_node(nid, lat=nloc[0], lon=nloc[1])
            if self.G.has_edge(u, v):
                if t < self.G[u][v]["time_min"]:
                    self.G[u][v]["time_min"] = t
                    self.G[u][v]["dist_km"] = d
            else:
                self.G.add_edge(u, v, time_min=t, dist_km=d)


class NodeGrid:
    """0.02° 网格索引: 最近节点查询从 O(N) 降到 O(邻桶节点数)"""

    CELL = 0.02

    def __init__(self, G):
        self.grid = {}
        for nid, data in G.nodes(data=True):
            key = (int(data["lat"] / self.CELL), int(data["lon"] / self.CELL))
            self.grid.setdefault(key, []).append((nid, data["lat"], data["lon"]))

    def nearest(self, lat, lon):
        import math as m
        gy, gx = int(lat / self.CELL), int(lon / self.CELL)
        for radius in range(0, 30):
            best, bestd = None, float("inf")
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if max(abs(dy), abs(dx)) != radius:
                        continue
                    bucket = self.grid.get((gy + dy, gx + dx))
                    if not bucket:
                        continue
                    for nid, nlat, nlon in bucket:
                        d = (nlat - lat) ** 2 + ((nlon - lon) * 0.86) ** 2
                        if d < bestd:
                            best, bestd = nid, d
            if best is not None:
                return best, m.sqrt(bestd) * 111.0
        return None, float("inf")


# ---------- 医院分级 / 等时圈 ----------

def _classify_hospital(name, healthcare=""):
    """根据名称与 tag 粗分大医院 / 普通医院 / 基层"""
    if not name:
        return "other"
    n = name.lower()
    if any(k in n for k in ["大学", "附属", "学院附属", "省立", "协和", "中心医院", "总医院", "市一医院", "人民医院"]) \
       or "hospital" in n:
        return "major"
    return "basic"


def _process_city(city, clat, clon, hospitals):
    """单城计算 (进程池 worker): 返回该城一行记录; 无结果返回 None"""
    try:
        sub = _osmium_extract(clon, clat)
    except Exception as e:
        log(f"  {city} 提取失败 {e}")
        return None
    if sub is None:
        return None

    handler = RoadGraphHandler()
    handler.apply_file(str(sub), locations=True)
    G = handler.G
    if G.number_of_nodes() == 0:
        ds = sorted(haversine_km(clat, clon, hl, ho) for hl, ho, _, _ in hospitals)
        return {"city": city,
                "nearest_hospital_km": round(ds[0], 2) if ds else None,
                "nearest_hospital_min": round(ds[0]/AVG_SPEED_FALLBACK*60, 1) if ds else None,
                "hospitals_15min": 0, "hospitals_30min": 0, "hospitals_60min": 0,
                "hospitals_window": 0,
                "major_nearest_km": None, "major_nearest_min": None,
                "major_30min": 0,
                "window_area_km2": None,
                "method": "euclidean"}

    targets = [(lat, lon, _classify_hospital(name, hc))
               for lat, lon, name, hc in hospitals
               if abs(lat - clat) <= WINDOW_DEG and abs(lon - clon) <= WINDOW_DEG]
    if not targets:
        return {"city": city, "hospitals_window": 0,
                "nearest_hospital_km": None, "nearest_hospital_min": None,
                "hospitals_15min": 0, "hospitals_30min": 0, "hospitals_60min": 0,
                "major_nearest_km": None, "major_nearest_min": None, "major_30min": 0,
                "window_area_km2": None,
                "mean_hospital_km_roundtrip": None, "method": "network"}

    grid = NodeGrid(G)
    src, src_gap = grid.nearest(clat, clon)
    if src is None:
        return None

    # 一次性单源最短路径 (同时时间与距离)
    INF = float("inf")
    times = {src: src_gap / AVG_SPEED_FALLBACK * 60}
    dists = {src: src_gap}
    pq = [(times[src], dists[src], src)]
    while pq:
        d, dk, u = heapq.heappop(pq)
        for v, edata in G[u].items():
            nd, ndk = d + edata["time_min"], dk + edata["dist_km"]
            if nd < times.get(v, INF):
                times[v] = nd
                dists[v] = ndk
                heapq.heappush(pq, (nd, ndk, v))

    best_dists, best_times, grades = [], [], []
    for hl, ho, grade in targets:
        tgt, gap = grid.nearest(hl, ho)
        if tgt is None or times.get(tgt, INF) == INF:
            euc = haversine_km(clat, clon, hl, ho)
            best_dists.append(euc)
            best_times.append(euc / AVG_SPEED_FALLBACK * 60)
            grades.append(grade)
            continue
        best_dists.append(dists[tgt] + gap)
        best_times.append(times[tgt] + gap / AVG_SPEED_FALLBACK * 60)
        grades.append(grade)

    i_min = best_times.index(min(best_times))
    iso = {t: sum(1 for x in best_times if x <= t) for t in [15, 30, 60]}
    majors = [(d, t) for d, t, g in zip(best_dists, best_times, grades) if g == "major"]
    window_area_km2 = (2*WINDOW_DEG*111*math.cos(math.radians(clat))) * (2*WINDOW_DEG*111)
    return {
        "city": city,
        "hospitals_window": len(targets),
        "nearest_hospital_km": round(best_dists[i_min], 2),
        "nearest_hospital_min": round(best_times[i_min], 1),
        "hospitals_15min": iso[15], "hospitals_30min": iso[30], "hospitals_60min": iso[60],
        "major_nearest_km": round(majors[0][0], 2) if majors else None,
        "major_nearest_min": round(majors[0][1], 1) if majors else None,
        "major_30min": sum(1 for _, t in majors if t <= 30),
        "mean_hospital_km_roundtrip": round(sum(best_dists)/len(best_dists)*2, 1),
        "window_area_km2": round(window_area_km2, 1),
        "method": "network",
    }




_N_WORKERS = 6  # 8 核机器, worker 峰值 ~1-5GB, 留系统余量


def _worker_init():
    import os
    os.nice(5)


def _preextract_all(todo_items):
    """阶段 A: 串行预提取所有城市窗口 pbf (避免多路 osmium 同时读大 pbf 的 OOM)"""
    have = sum(1 for city, clat, clon in todo_items if _window_cache_path(clat, clon).exists())
    log(f"预提取: {have}/{len(todo_items)} 已缓存")
    for i, (city, clat, clon) in enumerate(todo_items, 1):
        if _window_cache_path(clat, clon).exists():
            continue
        try:
            _osmium_extract(clon, clat)
        except Exception as e:
            log(f"  {city} 预提取失败: {e}")
        if i % 20 == 0:
            log(f"  预提取进度 {i}/{len(todo_items)}")


def _window_cache_path(clat, clon):
    return Path(tempfile.gettempdir()) / f"road_window_{clat:.2f}_{clon:.2f}.osm.pbf"


def compute_accessibility():
    """并行版可达性: 阶段A 串行预提取 + 阶段B 多进程计算 (worker 只读小文件)"""
    import pandas as pd
    from concurrent.futures import ProcessPoolExecutor, as_completed

    hospitals = _load_hospitals()
    if not hospitals:
        return

    centers = _load_city_centers()
    if not centers:
        log("无法取得城市中心点"); return

    out = OUTPUT_FILE
    todo = dict(centers)
    if out.exists():
        df_done = pd.read_csv(out)
        for c in df_done["city"]:
            todo.pop(c, None)
        log(f"断点续跑: 已有 {len(centers)-len(todo)} 城, 剩余 {len(todo)}")
    if not todo:
        log("全部城市已完成"); return

    # 阶段 A: 串行预提取
    _preextract_all([(c, lat, lon) for c, (lat, lon) in sorted(todo.items())])

    # 阶段 B: 并行计算
    done_rows = []
    with ProcessPoolExecutor(max_workers=min(_N_WORKERS, len(todo)),
                             initializer=_worker_init) as pool:
        futures = {pool.submit(_process_city, city, clat, clon, hospitals): city
                   for city, (clat, clon) in sorted(todo.items())}
        flushed = 0
        for i, fut in enumerate(as_completed(futures), 1):
            city = futures[fut]
            try:
                row = fut.result()
            except Exception as e:
                log(f"{city}: 失败 {e}"); continue
            if row:
                done_rows.append(row)
                log(f"[{i}/{len(todo)}] {city}: "
                    f"{row['nearest_hospital_km']} km / {row['nearest_hospital_min']} min")
            if len(done_rows) - flushed >= 30:
                flushed = len(done_rows)
                _flush(out, done_rows)

    if done_rows:
        _flush(out, done_rows)
        log(f"可达性输出完成 → {out}")


def _flush(out, done_rows):
    """
    增量合并写盘: 新行按 city 去重后并入已有 csv
    追加输入非 None 才会写入; done_rows 始终为新增
    """
    import pandas as pd
    df_new = pd.DataFrame(done_rows)
    if out.exists():
        df_old = pd.read_csv(out)
        df_new = df_new[~df_new["city"].isin(df_old["city"])]
        df_new = pd.concat([df_old, df_new], ignore_index=True)
    df_new.to_csv(out, index=False, encoding="utf-8-sig")
    log(f"  落盘累计 {len(df_new)} 城")


if __name__ == "__main__":
    print("\n[Integration] 就医可达性计算...")
    compute_accessibility()
