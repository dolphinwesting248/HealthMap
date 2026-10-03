from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from esda import Moran, Moran_Local
from libpysal.weights import KNN
from statsmodels.stats.multitest import multipletests

ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = ROOT / "data" / "integrated" / "integrated"
ACCESS_PATH = DATA_ROOT / "q2_healthcare_access" / "q2_healthcare_accessibility_city.csv"
GEO_PATH = ROOT / "data" / "cleaned" / "cleaned" / "geo_boundary.geojson"
OUTPUT_DIR = Path(__file__).resolve().parent
RESULT_PATH = OUTPUT_DIR / "q2_accessibility_moran_results.csv"
CITY_RESULT_PATH = OUTPUT_DIR / "q2_accessibility_moran_city_results.csv"
K_NEIGHBORS = 4
PERMUTATIONS = 9999
RANDOM_SEED = 42
EARTH_RADIUS_KM = 6371.0088
LISA_QUADRANTS = {1: "HH", 2: "LH", 3: "LL", 4: "HL"}


def flatten_coordinates(coordinates):
    if isinstance(coordinates[0], (int, float)):
        yield coordinates
        return
    for child in coordinates:
        yield from flatten_coordinates(child)


def city_centers() -> dict[str, tuple[float, float]]:
    geo = json.loads(GEO_PATH.read_text(encoding="utf-8"))
    centers = {}
    for feature in geo.get("features", []):
        properties = feature.get("properties", {})
        if properties.get("level") != "city":
            continue
        points = list(flatten_coordinates(feature["geometry"]["coordinates"]))
        centers[properties["name"]] = (
            float(np.mean([point[0] for point in points])),
            float(np.mean([point[1] for point in points])),
        )
    return centers


def load_city_data() -> pd.DataFrame:
    access = pd.read_csv(ACCESS_PATH)
    access["nearest_hospital_min"] = pd.to_numeric(access["nearest_hospital_min"], errors="coerce")
    access = access.dropna(subset=["nearest_hospital_min"]).copy()
    access = access.sort_values("city").reset_index(drop=True)
    centers = city_centers()
    access["longitude"] = access["city"].map(lambda city: centers.get(city, (np.nan, np.nan))[0])
    access["latitude"] = access["city"].map(lambda city: centers.get(city, (np.nan, np.nan))[1])
    access = access.dropna(subset=["longitude", "latitude"]).reset_index(drop=True)
    if access["city"].duplicated().any():
        raise ValueError("城市可达性输入存在重复城市记录")
    return access


def build_knn_weights(coordinates: np.ndarray, city_names: list[str]) -> KNN:
    if len(coordinates) <= K_NEIGHBORS:
        raise ValueError(f"有效城市数不足以构建 KNN-{K_NEIGHBORS}")
    weights = KNN.from_array(
        coordinates,
        k=K_NEIGHBORS,
        radius=EARTH_RADIUS_KM,
        ids=city_names,
    )
    weights.transform = "R"
    return weights


def run_analysis() -> dict:
    cities = load_city_data()
    coordinates = cities[["longitude", "latitude"]].to_numpy(dtype=float)
    values = cities["nearest_hospital_min"].to_numpy(dtype=float)
    city_names = cities["city"].tolist()
    weights = build_knn_weights(coordinates, city_names)

    np.random.seed(RANDOM_SEED)
    global_moran = Moran(
        values,
        weights,
        transformation="R",
        permutations=PERMUTATIONS,
        two_tailed=True,
    )
    local_moran = Moran_Local(
        values,
        weights,
        transformation="R",
        permutations=PERMUTATIONS,
        seed=RANDOM_SEED,
        n_jobs=1,
        keep_simulations=False,
    )
    fdr_significant, fdr_p_values, _, _ = multipletests(
        local_moran.p_sim,
        alpha=0.05,
        method="fdr_bh",
    )

    neighbor_names = [
        "、".join(weights.neighbors[city]) for city in city_names
    ]
    spatial_lag = np.asarray(weights.sparse @ values).ravel()
    city_results = cities[["city", "longitude", "latitude", "nearest_hospital_min"]].copy()
    city_results["knn4_neighbor_cities"] = neighbor_names
    city_results["knn4_spatial_lag_min"] = spatial_lag
    city_results["local_moran_i"] = local_moran.Is
    city_results["lisa_quadrant_code"] = local_moran.q
    city_results["lisa_quadrant"] = [LISA_QUADRANTS[int(code)] for code in local_moran.q]
    city_results["lisa_p_sim_min_tail"] = local_moran.p_sim
    city_results["lisa_fdr_q_value"] = fdr_p_values
    city_results["lisa_significant_raw_05"] = local_moran.p_sim < 0.05
    city_results["lisa_significant_fdr_05"] = fdr_significant
    city_results.to_csv(CITY_RESULT_PATH, index=False, encoding="utf-8-sig")

    result = {
        "variable": "nearest_hospital_min",
        "n_cities": int(len(cities)),
        "knn_k": K_NEIGHBORS,
        "weight_type": "binary KNN, row-standardized",
        "coordinate_method": "mean of city-boundary polygon vertices; libpysal Arc KNN, lon/lat degrees",
        "earth_radius_km": EARTH_RADIUS_KM,
        "permutations": PERMUTATIONS,
        "random_seed": RANDOM_SEED,
        "moran_i": float(global_moran.I),
        "expected_i": float(global_moran.EI),
        "p_norm_two_sided": float(global_moran.p_norm),
        "p_rand_two_sided": float(global_moran.p_rand),
        "p_sim_min_tail": float(global_moran.p_sim),
        "z_sim": float(global_moran.z_sim),
        "p_z_sim_one_sided": float(global_moran.p_z_sim),
        "lisa_quadrant_counts": {
            LISA_QUADRANTS[code]: int(np.count_nonzero(local_moran.q == code))
            for code in LISA_QUADRANTS
        },
        "lisa_raw_p_lt_005_count": int(np.count_nonzero(local_moran.p_sim < 0.05)),
        "lisa_fdr_significant_count": int(np.count_nonzero(fdr_significant)),
        "lisa_fdr_cluster_counts": {
            LISA_QUADRANTS[code]: int(np.count_nonzero(fdr_significant & (local_moran.q == code)))
            for code in LISA_QUADRANTS
        },
        "input_accessibility_path": str(ACCESS_PATH),
        "input_boundary_path": str(GEO_PATH),
        "city_results_path": str(CITY_RESULT_PATH),
    }
    pd.DataFrame([result]).to_csv(RESULT_PATH, index=False, encoding="utf-8-sig")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    run_analysis()
