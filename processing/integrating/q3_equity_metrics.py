"""
Q3-Integration: 跨省公平性度量 (基尼系数 + 变异系数)
输入:
     data/integrated/q2_healthcare_access/q2_medical_resource_province.csv (资源)
     data/integrated/q1_environment_health/q1_env_exposure_province.csv   (环境)
     data/integrated/q1_environment_health/q1_health_outcome_province.csv (健康)
     data/cleaned/econ_income.csv  (名义收入)
     data/cleaned/econ_price.csv   (CPI, 平减分母)
输出: data/integrated/q3_equity/q3_equity_metrics.csv (年度公平性指标横截面)

方法: 每年基于 31 省横截面:
  - Gini: 常规排序 ( haystacks) 计算, 对 population 加权时人口分母使用五年平均预留 v2
  - CV (标准差/均值) for 资源密度与实际收入
  - 实际收入 = 名义人均可支配收入 / (CPI/100, 上年=100)
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROCESSING_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = PROCESSING_DIR.parent
CLEANED = PROJECT_ROOT / "data" / "cleaned"
Q1 = PROJECT_ROOT / "data" / "integrated" / "q1_environment_health"
Q2 = PROJECT_ROOT / "data" / "integrated" / "q2_healthcare_access"
OUT_DIR = PROJECT_ROOT / "data" / "integrated" / "q3_equity"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "q3_equity_metrics.csv"


def log(msg):
    print(f"  {msg}", flush=True)


def gini(x):
    """Gini 系数 (无权重, 31 横截面)"""
    x = np.sort(np.asarray(x, dtype=float)[~np.isnan(x)])
    n = len(x)
    if n == 0 or x.sum() == 0:
        return np.nan
    cum = np.cumsum(x) / x.sum()
    return float((n + 1 - 2 * np.sum(cum)) / n)


def cv(x):
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    if len(x) == 0 or x.mean() == 0:
        return np.nan
    return float(x.std() / x.mean())


def theil(x):
    """泰尔 T 指数 (0=完全平均, 越大越不均)"""
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    if x.sum() <= 0 or len(x) == 0:
        return np.nan
    mu = x.mean()
    ratio = np.where(x > 0, x / mu, np.nan)
    r = ratio[~np.isnan(ratio)]
    if len(r) == 0:
        return np.nan
    return float(np.mean(r * np.log(r)))


def theil_decompose(x, zone, pop):
    """标准 Theil-T 组分解 (Shorrocks / Bourguignon 口径, 人口权重):"""
    y = np.asarray(x, dtype=float)
    z = np.asarray(zone, dtype=object)
    w = np.asarray(pop, dtype=float)

    mask = ~(np.isnan(y) | (y <= 0) | pd.isna(w) | (w <= 0))
    y, z, w = y[mask], z[mask], w[mask]
    n = y.sum()
    if len(y) == 0 or n <= 0:
        return np.nan, np.nan, np.nan
    # 标准 Theil-T 分解 (income share 权重, Shorrocks 1980):
    mu = y.mean()
    Y = y.sum()
    T_total = float(np.mean((y / mu) * np.log(y / mu)))
    T_between = 0.0
    T_within = 0.0
    for zb in sorted(set(z)):
        m = (z == zb)
        yz = y[m]
        if yz.sum() <= 0 or len(yz) == 0:
            continue
        s_z = yz.sum() / Y          # 收入份额
        mu_z = yz.mean()
        t_z = theil(yz)
        T_between += float(s_z * np.log(mu_z / mu))
        T_within += float(s_z * t_z)
    return T_total, T_between, T_within


REGION3 = {  # 三大地带 (国家统计局口径)
    "东部": ["北京", "天津", "河北", "上海", "江苏", "浙江",
             "福建", "山东", "广东", "海南", "辽宁"],
    "中部": ["山西", "吉林", "黑龙江", "安徽", "江西", "河南", "湖北", "湖南"],
    "西部": ["内蒙古", "广西", "重庆", "四川", "贵州", "云南", "西藏",
             "陕西", "甘肃", "青海", "宁夏", "新疆"],
}
P2Z = {p: z for z, ps in REGION3.items() for p in ps}


def pop_weights():
    """抽样调查人口 (千人) → 省×年 权重帧; 用于加权 gini / theil 分解"""
    pa = pd.read_csv(CLEANED / "econ_pop_age.csv")
    pa = pa[(pa["indicator"] == "人口数 (人口抽样调查) (人)") & pa["value_num"].notna()]
    pa = pa.rename(columns={"value_num": "pop_wan"})[["province", "year", "pop_wan"]]
    return pa


def clean():
    print("\n[Q3-Integration] 跨省公平性度量...")

    # 1. 名义收入 + CPI 来源
    inc = pd.read_csv(CLEANED / "econ_income.csv")
    inc = inc[inc["value_num"].notna() &
              inc["indicator"].str.contains("全体居民人均可支配收入")]
    inc = inc.rename(columns={"value_num": "nominal_income"})[["province", "year", "nominal_income"]]

    # CPI: 居民消费价格指数 (上年=100) — 用于实际购买力 (cumprod 从 base 年 2016 起算)
    cpi = pd.read_csv(CLEANED / "econ_price.csv", low_memory=False)
    cpi = cpi[cpi["indicator"] == "居民消费价格指数 (上年=100)"]
    cpi = cpi[cpi["value_num"].notna()]
    cpi = cpi.rename(columns={"value_num": "cpi_yoy"})[["province", "year", "cpi_yoy"]]
    cpi = cpi.drop_duplicates(["province", "year"], keep="first")
    # 累计 levels (2016=基准 1.0, 每年 cpi_yoy/100 累乘)
    idx_base = {}
    rows = []
    for (prov), grp in cpi.groupby("province"):
        lvl = 1.0
        for y in sorted(grp["year"].unique()):
            sub = grp[grp["year"] == y]["cpi_yoy"].iloc[0]
            if y > 2016:
                lvl *= float(sub) / 100
            rows.append({"province": prov, "year": y, "cpi_cum": lvl})
    cpi_cum = pd.DataFrame(rows)

    inc = inc.merge(cpi_cum, on=["province", "year"], how="left")
    inc["real_income"] = inc["nominal_income"] / inc["cpi_cum"]

    # 2. 医疗资源 per10k 指标 (床/医/护)
    res = pd.read_csv(Q2 / "q2_medical_resource_province.csv", low_memory=False)
    cols_res = ["per10k_beds_all", "per10k_doctors", "per10k_nurses", "per10k_health_tech", "med_hospitals"]

    # 3. 预期寿命 + 环境
    le = pd.read_csv(Q1 / "q1_health_outcome_province.csv", low_memory=False)
    cols_le = ["outcome_life_expectancy"]
    exp = pd.read_csv(Q1 / "q1_env_exposure_province.csv")
    col_env = "air_pm25_mean"

    merged = res.merge(inc[["province", "year", "real_income", "nominal_income"]],
                       on=["province", "year"], how="outer")
    exp_small = exp[["province", "year", "air_pm25_mean"]]
    merged = merged.merge(exp_small, on=["province", "year"], how="outer")
    merged = merged.merge(pop_weights(), on=["province", "year"], how="left")
    merged["zone"] = merged["province"].map(P2Z)
    merged["zone"] = merged["zone"].fillna("其他")

    rows = []
    for year, g in merged.groupby("year"):
        rec = {"year": int(year)}
        for c in cols_res:
            if c in g:
                rec[f"gini_{c}"] = gini(g[c])
                rec[f"cv_{c}"] = cv(g[c])
        rec["gini_real_income"] = gini(g["real_income"])
        rec["cv_real_income"] = cv(g["real_income"])
        rec["gini_nominal_income"] = gini(g["nominal_income"])
        # 泰尔 SDNA 分解 (Theil-T + 组间/组内, 规范 Shorrocks 公式; real_income 为例)
        gw = g.dropna(subset=["real_income"])
        if len(gw) >= 6:
            T, Tb, Tw = theil_decompose(gw["real_income"], gw["zone"],
                                        gw["pop_wan"].fillna(0) + 1)  # +1 防零权
            rec["theil_real_income"] = T
            rec["theil_within_real_income"] = Tw
            rec["theil_between_real_income"] = Tb
            rec["theil_between_share_real_income"] = Tb / T if T and T > 0 else np.nan
        # 分位比 (实际收入)
        ri = g["real_income"].dropna()
        if len(ri) >= 10:
            rec["income_p90_p10"] = float(np.percentile(ri, 90) / np.percentile(ri, 10))
            rec["income_max_min"] = float(ri.max() / ri.min())
        for c in cols_le:
            if c in g:
                rec[f"gini_{c}"] = gini(g[c])
                rec[f"cv_{c}"] = cv(g[c])
        rec["gini_air_pm25_mean"] = gini(g["air_pm25_mean"]) if "air_pm25_mean" in g else np.nan
        rec["cv_air_pm25_mean"] = cv(g["air_pm25_mean"]) if "air_pm25_mean" in g else np.nan
        # 区域内总体: 3 地带基尼 (资源)
        for zone in ["东部", "中部", "西部"]:
            gz = g[g["zone"] == zone]
            if len(gz) >= 5 and "per10k_beds_all" in gz:
                rec[f"gini_beds_{zone}"] = gini(gz["per10k_beds_all"])
        rows.append(rec)

    out = pd.DataFrame(rows).sort_values("year").reset_index(drop=True)
    out.to_csv(OUT_FILE, index=False, encoding="utf-8-sig")
    log(f"输出: {len(out)} 年 × {len(out.columns)-1} 指标 → {OUT_FILE}")


if __name__ == "__main__":
    clean()
