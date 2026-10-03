from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = ROOT / "data" / "integrated" / "integrated"
CLEANED_GEO = ROOT / "data" / "cleaned" / "cleaned" / "geo_boundary.geojson"
Q1_PATH = DATA_ROOT / "q1_environment_health" / "q1_env_health_panel.csv"
Q2_RESOURCE_PATH = DATA_ROOT / "q2_healthcare_access" / "q2_medical_resource_province.csv"
Q2_ACCESS_PATH = DATA_ROOT / "q2_healthcare_access" / "q2_healthcare_accessibility_city.csv"
RESULT_PATH = Path(__file__).resolve().parent / "q2_analysis_results.csv"


def city_to_province_map() -> dict[str, str]:
    if not CLEANED_GEO.exists():
        return {}
    with open(CLEANED_GEO, "r", encoding="utf-8") as f:
        geo = json.load(f)

    prov_by_adcode = {
        str(feature["properties"].get("adcode")): feature["properties"]["name"]
        for feature in geo.get("features", [])
        if feature.get("properties", {}).get("level") == "province"
    }

    cmap: dict[str, str] = {}
    for feature in geo.get("features", []):
        props = feature.get("properties", {})
        if props.get("level") != "city":
            continue
        parent = props.get("parent") or {}
        adcode = str(parent.get("adcode") or parent)
        if adcode in prov_by_adcode:
            cmap[props["name"]] = prov_by_adcode[adcode]
    return cmap


def normalize_province(value: object) -> object:
    if not isinstance(value, str):
        return value
    cleaned = value.strip()
    replacements = {
        "省": "",
        "市": "",
        "壮族自治区": "",
        "回族自治区": "",
        "自治区": "",
        "维吾尔": "",
        "特别行政区": "",
        "香港": "",
        "澳门": "",
    }
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)
    return cleaned


def attach_city_province(access: pd.DataFrame) -> pd.DataFrame:
    city_df = access.copy()
    province_map = city_to_province_map()
    city_df["province_raw"] = city_df["city"].map(province_map)

    province_names = sorted({v for v in province_map.values() if isinstance(v, str)})
    for idx, city_name in city_df["city"].items():
        if pd.isna(city_df.at[idx, "province_raw"]):
            stem = re.sub(r"市|地区|州|盟", "", str(city_name))
            match = next((p for p in province_names if stem in p or p in stem), None)
            city_df.at[idx, "province_raw"] = match

    city_df["province"] = city_df["province_raw"].apply(normalize_province)
    return city_df


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    resource = pd.read_csv(Q2_RESOURCE_PATH)
    access = pd.read_csv(Q2_ACCESS_PATH)
    q1 = pd.read_csv(Q1_PATH)
    return resource, access, q1


def build_panel(resource: pd.DataFrame, q1: pd.DataFrame) -> pd.DataFrame:
    cols = ["province", "year", "econ_income_total", "econ_income_urban", "econ_income_rural"]
    q1_core = q1[cols].copy()
    q1_core["year"] = pd.to_numeric(q1_core["year"], errors="coerce")
    df = resource.merge(q1_core, on=["province", "year"], how="inner")
    df = df.dropna(subset=["per10k_beds_calc", "econ_income_total", "econ_income_urban", "econ_income_rural"]).copy()
    df["ln_income_total"] = np.log(df["econ_income_total"])
    df["urban_rural_gap"] = df["econ_income_urban"] - df["econ_income_rural"]
    return df


def province_resource_summary(panel: pd.DataFrame) -> dict:
    corr = panel["per10k_beds_calc"].corr(panel["ln_income_total"])
    basic_model = sm.OLS(
        panel["per10k_beds_calc"],
        sm.add_constant(panel["ln_income_total"]),
    ).fit()

    province_dummies = pd.get_dummies(panel["province"], prefix="province", drop_first=True)
    year_dummies = pd.get_dummies(panel["year"], prefix="year", drop_first=True)
    panel_x = pd.concat([
        panel[["ln_income_total", "urban_rural_gap"]].reset_index(drop=True),
        province_dummies.reset_index(drop=True),
        year_dummies.reset_index(drop=True),
    ], axis=1).astype(float)
    panel_model = sm.OLS(
        panel["per10k_beds_calc"].reset_index(drop=True).astype(float),
        sm.add_constant(panel_x, has_constant="add"),
    ).fit(cov_type="cluster", cov_kwds={"groups": panel["province"].reset_index(drop=True)})

    reverse_y = panel["ln_income_total"].reset_index(drop=True).astype(float)
    reverse_x = pd.concat([
        panel[["per10k_beds_calc", "urban_rural_gap"]].reset_index(drop=True),
        province_dummies.reset_index(drop=True),
        year_dummies.reset_index(drop=True),
    ], axis=1).astype(float)
    reverse_model = sm.OLS(
        reverse_y,
        sm.add_constant(reverse_x, has_constant="add"),
    ).fit(cov_type="cluster", cov_kwds={"groups": panel["province"].reset_index(drop=True)})

    annual = (
        panel.groupby("year", as_index=False)[["per10k_beds_calc", "per10k_doctors_calc", "per10k_nurses_calc"]]
        .mean()
        .sort_values("year")
    )

    return {
        "sample_rows": int(len(panel)),
        "sample_years": f"{int(panel['year'].min())}-{int(panel['year'].max())}",
        "corr_per10k_beds_vs_ln_income": round(float(corr), 4),
        "ols_intercept": round(float(basic_model.params.iloc[0]), 4),
        "ols_slope_ln_income": round(float(basic_model.params.iloc[1]), 4),
        "ols_r2": round(float(basic_model.rsquared), 4),
        "panel_fe_model": {
            "dependent": "per10k_beds_calc",
            "model_spec": "per10k_beds_calc ~ log(econ_income_total) + (econ_income_urban - econ_income_rural) + year FE + province FE",
            "nobs": int(len(panel)),
            "coef_ln_income_total": round(float(panel_model.params.get("ln_income_total", np.nan)), 4),
            "coef_urban_rural_gap": round(float(panel_model.params.get("urban_rural_gap", np.nan)), 4),
            "r2": round(float(panel_model.rsquared), 4),
            "adjusted_r2": round(float(panel_model.rsquared_adj), 4),
            "clustering": "province",
            "fixed_effects": ["province", "year"],
        },
        "reverse_panel_fe_model": {
            "dependent": "ln_income_total",
            "key_regressor": "per10k_beds_calc",
            "coef_per10k_beds_calc": round(float(reverse_model.params.get("per10k_beds_calc", np.nan)), 4),
            "coef_urban_rural_gap": round(float(reverse_model.params.get("urban_rural_gap", np.nan)), 4),
            "r2": round(float(reverse_model.rsquared), 4),
            "adjusted_r2": round(float(reverse_model.rsquared_adj), 4),
        },
        "annual_mean_per10k_beds": {
            str(int(y)): round(float(v), 2)
            for y, v in zip(annual["year"], annual["per10k_beds_calc"])
        },
    }


def city_accessibility_summary(access: pd.DataFrame, q1: pd.DataFrame) -> dict:
    access = attach_city_province(access)
    for col in ["nearest_hospital_min", "major_nearest_min", "nearest_hospital_km", "major_nearest_km"]:
        access[col] = pd.to_numeric(access[col], errors="coerce")

    valid = access["nearest_hospital_min"].dropna()
    major_valid = access["major_nearest_min"].dropna()
    major_unreachable = int((access["major_nearest_min"].fillna(999) > 30).sum())

    province_income = q1.groupby("province", as_index=False)[["econ_income_total"]].mean().rename(columns={"econ_income_total": "econ_income_mean"})
    access_with_income = access.merge(province_income, on="province", how="left")
    reg_df = access_with_income.dropna(subset=["major_nearest_km", "econ_income_mean"]).copy()
    reg_df["major_nearest_km"] = pd.to_numeric(reg_df["major_nearest_km"], errors="coerce")

    if not reg_df.empty:
        city_model = sm.OLS(reg_df["major_nearest_km"], sm.add_constant(reg_df["econ_income_mean"])).fit()
        city_coef = round(float(city_model.params.get("econ_income_mean", np.nan)), 8)
        city_r2 = round(float(city_model.rsquared), 4)
        city_intercept = round(float(city_model.params.get("const", np.nan)), 4)
    else:
        city_coef = None
        city_r2 = None
        city_intercept = None

    province_mean_access = (
        reg_df.groupby("province", as_index=False)["major_nearest_km"].mean()
        .merge(province_income, on="province", how="inner")
    )
    if not province_mean_access.empty:
        province_model = sm.OLS(province_mean_access["major_nearest_km"], sm.add_constant(province_mean_access["econ_income_mean"])).fit()
        prov_coef = round(float(province_model.params.get("econ_income_mean", np.nan)), 8)
        prov_r2 = round(float(province_model.rsquared), 4)
    else:
        prov_coef = None
        prov_r2 = None

    summary = {
        "city_sample_count_all": int(len(access)),
        "city_sample_count_regression": int(len(reg_df)),
        "city_sample_count_province_mean": int(province_mean_access["province"].nunique()),
        "nearest_hospital_min_median": round(float(valid.median()), 2),
        "nearest_hospital_min_p25": round(float(valid.quantile(0.25)), 2),
        "nearest_hospital_min_p75": round(float(valid.quantile(0.75)), 2),
        "nearest_hospital_min_p90": round(float(valid.quantile(0.9)), 2),
        "nearest_hospital_min_max": round(float(valid.max()), 2),
        "major_nearest_min_median": round(float(major_valid.median()), 2),
        "major_hospital_30min_unreachable_count": major_unreachable,
        "major_hospital_30min_unreachable_share": round(float(major_unreachable / len(access) * 100), 2),
        "city_cross_section_regression": {
            "model_spec": "major_nearest_km ~ econ_income_mean (province average)",
            "nobs": int(len(reg_df)),
            "nprovinces": int(reg_df["province"].nunique()),
            "coef_econ_income_mean": city_coef,
            "intercept": city_intercept,
            "r2": city_r2,
        },
        "province_mean_cross_section_regression": {
            "model_spec": "mean(major_nearest_km) ~ econ_income_mean (province average)",
            "nobs": int(len(province_mean_access)),
            "coef_econ_income_mean": prov_coef,
            "r2": prov_r2,
        },
    }
    return summary


def main() -> None:
    resource, access, q1 = load_data()
    panel = build_panel(resource, q1)
    province_summary = province_resource_summary(panel)
    city_summary = city_accessibility_summary(access, q1)

    result = {
        "analysis_scope": "Q2: 医疗资源、可达性与区域经济",
        "analysis_sequence": [
            "descriptive_summary",
            "province_panel_fixed_effects_regression",
            "city_accessibility_summary"
        ],
        "province_summary": province_summary,
        "city_summary": city_summary,
        "data_source": {
            "resource": str(Q2_RESOURCE_PATH),
            "accessibility": str(Q2_ACCESS_PATH),
            "income_panel": str(Q1_PATH),
        },
    }

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([result]).to_csv(RESULT_PATH, index=False, encoding="utf-8-sig")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
