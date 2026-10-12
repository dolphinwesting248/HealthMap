#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HealthMap · Q3 公平性分析（一键运行版）

覆盖 docs/analysis.md 中 Q3 的全部要求：
  3.1 年度公平性趋势      -> 4 子图趋势 / 泰尔分解堆叠柱 / 三轴图 / Kendall 趋势检验
  3.2 医疗资源公平性横截面 -> 资源基尼趋势(含三大地带) / 洛伦兹曲线 / 省级排名 /
                            资源-经济散点 / 老龄化床位压力 / 收入 vs 环境收敛速度 /
                            (可选) 城市级 hospital_count 洛伦兹 + Moran's I
  3.3 面板回归            -> 急诊病死率 ~ 收入 + 可达性P90 + PM2.5 + 床位 + 卫生就业 (+FE)
                            含 P90 vs mean 对比、三者交互与边际效应

依赖: numpy, pandas, matplotlib, scipy（不需要 statsmodels；OLS 与聚类稳健标准误为手写实现）

用法（在项目任意位置）:
    python analysis/q3_equity/q3_equity.py
    python analysis/q3_equity/q3_equity.py --root D:\\信管\\DASHUJU\\HealthMap-main
    python analysis/q3_equity/q3_equity.py --no-city        # 跳过城市级可选模块

输出:
    analysis/q3_equity/outputs/   表格(csv) + q3_report.md（自动生成、含真实数值）
    visualization/q3_equity/      全部图表(png)
"""
from __future__ import annotations

import argparse
import json
import traceback
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker  # noqa: F401
from matplotlib import font_manager as fm
from scipy import stats

# ============================================================
# 0. 常量与配置
# ============================================================
REGION3 = {  # 三大地带（与 processing/integrating/q3_equity_metrics.py 口径一致）
    "东部": ["北京", "天津", "河北", "上海", "江苏", "浙江", "福建", "山东", "广东", "海南", "辽宁"],
    "中部": ["山西", "吉林", "黑龙江", "安徽", "江西", "河南", "湖北", "湖南"],
    "西部": ["内蒙古", "广西", "重庆", "四川", "贵州", "云南", "西藏", "陕西", "甘肃", "青海", "宁夏", "新疆"],
}
P2Z = {p: z for z, ps in REGION3.items() for p in ps}
STD31 = set(P2Z)
ZONE_COLORS = {"东部": "#1f77b4", "中部": "#ff7f0e", "西部": "#2ca02c"}

RESOURCES = [  # (panel列名, 中文名, metrics 中的基尼列名)
    ("per10k_beds_all", "每万人床位", "gini_per10k_beds_all"),
    ("per10k_doctors", "每万人医生", "gini_per10k_doctors"),
    ("per10k_nurses", "每万人护士", "gini_per10k_nurses"),
]

REG_VARS = [  # 回归核心变量 (列名, 中文名)
    ("econ_income_total", "收入"),
    ("acc_nearest_km_p90", "可达性P90(km)"),
    ("air_pm25_mean", "PM2.5"),
    ("per10k_beds_all", "每万人床位"),
    ("ctrl_healthcare_employment_wan", "卫生就业(万人)"),
]

HERE = Path(__file__).resolve().parent
LOG: list[str] = []          # 进入报告“数据检查”部分
FAILED: list[str] = []       # 记录失败的图/表，写进报告


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.append(msg)


def setup_font() -> None:
    names = {f.name for f in fm.fontManager.ttflist}
    for n in ["Microsoft YaHei", "SimHei", "PingFang SC", "Heiti SC", "Noto Sans CJK SC",
              "Source Han Sans SC", "WenQuanYi Micro Hei", "Arial Unicode MS"]:
        if n in names:
            plt.rcParams["font.sans-serif"] = [n, "DejaVu Sans"]
            break
    else:
        cjk = sorted(n for n in names if any(k in n for k in ("CJK", "Han Sans", "YaHei", "Hei", "Song", "Ming")))
        if cjk:
            plt.rcParams["font.sans-serif"] = [cjk[0], "DejaVu Sans"]
        else:
            print("[警告] 未找到中文字体，图中中文可能显示为方框")
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["axes.spines.top"] = False
    plt.rcParams["axes.spines.right"] = False
    plt.rcParams["figure.dpi"] = 100


def find_root(arg: str | None) -> Path:
    if arg:
        return Path(arg)
    for p in [HERE, *HERE.parents]:
        if (p / "processing").exists() and (p / "analysis").exists():
            return p
    return HERE.parents[1]


def find_file(root: Path, name: str, dirs: list[Path]) -> Path | None:
    for d in dirs:
        if (d / name).exists():
            return d / name
    hits = sorted(root.rglob(name))
    return hits[0] if hits else None


def pick(df: pd.DataFrame, *cands: str) -> str | None:
    for c in cands:
        if c in df.columns:
            return c
    return None


# ============================================================
# 1. 统计工具
# ============================================================
def lorenz(values, weights=None):
    """返回 (人口/单元累计份额, 资源累计份额, 基尼)。weights=None 为省等权。
    weights 给定时，values 视为“人均量”，总量 = values*weights（人口加权洛伦兹）。"""
    v = np.asarray(values, float)
    w = np.ones_like(v) if weights is None else np.asarray(weights, float)
    ok = ~(np.isnan(v) | np.isnan(w)) & (w > 0)
    v, w = v[ok], w[ok]
    order = np.argsort(v)
    v, w = v[order], w[order]
    x = np.r_[0, np.cumsum(w) / w.sum()]
    y = np.r_[0, np.cumsum(v * w) / (v * w).sum()]
    g = 1 - float(np.sum(np.diff(x) * (y[1:] + y[:-1])))
    return x, y, g


def kendall(years, vals):
    s = pd.DataFrame({"y": years, "v": vals}).dropna()
    if len(s) < 4:
        return np.nan, np.nan
    tau, p = stats.kendalltau(s["y"], s["v"])
    return float(tau), float(p)


def direction(pct, tol=5.0):
    if pd.isna(pct):
        return "—"
    if abs(pct) < tol:
        return "基本稳定"
    return "上升" if pct > 0 else "下降"


def sig_word(p):
    if pd.isna(p):
        return "—"
    return "显著(p<0.05)" if p < 0.05 else ("边际显著(p<0.10)" if p < 0.10 else "不显著")


def morans_i(values, lon, lat, k=4, perms=999, seed=42):
    """全局 Moran's I（KNN 空间权重，行标准化；球面距离近似）。"""
    z = np.asarray(values, float)
    lon, lat = np.radians(np.asarray(lon, float)), np.radians(np.asarray(lat, float))
    n = len(z)
    dlat = lat[:, None] - lat[None, :]
    dlon = lon[:, None] - lon[None, :]
    a = np.sin(dlat / 2) ** 2 + np.cos(lat[:, None]) * np.cos(lat[None, :]) * np.sin(dlon / 2) ** 2
    d = 2 * 6371.0088 * np.arcsin(np.sqrt(a))
    np.fill_diagonal(d, np.inf)
    nbr = np.argsort(d, axis=1)[:, :k]
    W = np.zeros((n, n))
    for i in range(n):
        W[i, nbr[i]] = 1.0 / k

    def stat(x):
        x = x - x.mean()
        return float(x @ W @ x / (x @ x))

    I = stat(z)
    rng = np.random.default_rng(seed)
    sims = np.array([stat(rng.permutation(z)) for _ in range(perms)])
    p = (np.sum(np.abs(sims - sims.mean()) >= abs(I - sims.mean())) + 1) / (perms + 1)
    return I, float(sims.mean()), float(p)


def fit_ols(y, X, names, groups):
    """OLS + CRV1 聚类稳健标准误。
    X 中列顺序 = [常数, 固定效应哑变量..., 解释变量...]；按顺序做 Gram-Schmidt，
    后出现且与前面线性相关的列（如被省 FE 吸收的单快照可达性）会被剔除并记录。"""
    n = len(y)
    keep, dropped = [], []
    Q = np.empty((n, 0))
    for j, nm in enumerate(names):
        col = X[:, j].astype(float)
        r = col.copy()
        for _ in range(2):
            if Q.shape[1]:
                r = r - Q @ (Q.T @ r)
        n0, nr = np.linalg.norm(col), np.linalg.norm(r)
        if n0 == 0 or nr / n0 < 1e-8:
            dropped.append(nm)
            continue
        Q = np.column_stack([Q, r / nr])
        keep.append(j)
    Xk = X[:, keep]
    k = Xk.shape[1]
    G = len(np.unique(groups))
    if n - k <= 0 or G < 2:
        return None
    XtXi = np.linalg.pinv(Xk.T @ Xk)
    beta = XtXi @ Xk.T @ y
    u = y - Xk @ beta
    meat = np.zeros((k, k))
    for g in np.unique(groups):
        s = Xk[groups == g].T @ u[groups == g]
        meat += np.outer(s, s)
    c = G / (G - 1) * (n - 1) / (n - k)
    V = c * XtXi @ meat @ XtXi
    se = np.sqrt(np.clip(np.diag(V), 0, None))
    with np.errstate(divide="ignore", invalid="ignore"):
        t = beta / se
    p = 2 * stats.t.sf(np.abs(t), G - 1)
    tcrit = stats.t.ppf(0.975, G - 1)
    ssr, tss = float(u @ u), float(((y - y.mean()) ** 2).sum())
    r2 = 1 - ssr / tss if tss > 0 else np.nan
    return dict(names=[names[j] for j in keep], beta=beta, se=se, t=t, p=p,
                lo=beta - tcrit * se, hi=beta + tcrit * se, V=V, n=n, k=k, G=G,
                r2=r2, adj_r2=1 - (1 - r2) * (n - 1) / (n - k) if n > k else np.nan,
                dropped=dropped)


def run_model(df, label, y, xs, fe, interactions=(), cluster="province"):
    """z-score 解释变量后拟合；返回 (结果表, 元信息, 原始拟合)。"""
    need = [y, *xs, *fe, cluster]
    d = df.dropna(subset=need).copy()
    if len(d) == 0:
        return None
    sd = {}
    for x in xs:
        sd[x] = d[x].std(ddof=0)
        d[x + "__z"] = (d[x] - d[x].mean()) / sd[x] if sd[x] > 0 else 0.0
    cols_x = [x + "__z" for x in xs]
    names_x = list(xs)
    for a, b in interactions:
        d[f"{a}×{b}"] = d[a + "__z"] * d[b + "__z"]
        cols_x.append(f"{a}×{b}")
        names_x.append(f"{a}×{b}")
    dm = pd.get_dummies(d[fe].astype(str), columns=fe, drop_first=True, dtype=float) if fe else pd.DataFrame(index=d.index)
    X = np.column_stack([np.ones(len(d)), dm.values, d[cols_x].values])
    names = ["const", *dm.columns, *names_x]
    fit = fit_ols(d[y].values.astype(float), X, names, d[cluster].values)
    if fit is None:
        return None
    rows = []
    for nm in names_x:
        if nm in fit["dropped"]:
            rows.append(dict(model=label, term=nm, coef_per_sd=np.nan, se=np.nan, p=np.nan,
                             ci_low=np.nan, ci_high=np.nan, coef_raw=np.nan,
                             note="与固定效应共线，被吸收（该变量在 FE 内无独立变化）"))
            continue
        i = fit["names"].index(nm)
        base = nm if nm in sd else None
        rows.append(dict(model=label, term=nm, coef_per_sd=fit["beta"][i], se=fit["se"][i], p=fit["p"][i],
                         ci_low=fit["lo"][i], ci_high=fit["hi"][i],
                         coef_raw=fit["beta"][i] / sd[base] if base and sd[base] > 0 else np.nan, note=""))
    tab = pd.DataFrame(rows)
    meta = dict(model=label, n=fit["n"], n_provinces=d[cluster].nunique(),
                years=",".join(map(str, sorted(d["year"].unique()))), k_params=fit["k"],
                df_resid=fit["n"] - fit["k"], r2=fit["r2"], adj_r2=fit["adj_r2"],
                fe="+".join(fe), dropped=";".join(fit["dropped"]),
                warning=("自由度过少(<10)，结果极不稳定" if fit["n"] - fit["k"] < 10 else
                         ("聚类数<10，聚类SE偏乐观" if fit["G"] < 10 else "")))
    return tab, meta, fit


def marginal_effects(fit, main_terms, label):
    """交互模型：每个变量在其它变量取 -1/0/+1 SD 时的边际效应（z 尺度）。"""
    names, V, beta = fit["names"], fit["V"], fit["beta"]
    out = []
    for a in main_terms:
        if a not in names:
            continue
        for b in main_terms:
            if b == a:
                continue
            inter = next((nm for nm in (f"{a}×{b}", f"{b}×{a}") if nm in names), None)
            for lvl in (-1, 0, 1):
                g = np.zeros(len(names))
                g[names.index(a)] = 1
                if inter:
                    g[names.index(inter)] = lvl
                me = float(g @ beta)
                se = float(np.sqrt(g @ V @ g))
                t = me / se if se > 0 else np.nan
                p = 2 * stats.t.sf(abs(t), fit["G"] - 1) if se > 0 else np.nan
                out.append(dict(model=label, variable=a, moderator=b, moderator_level_sd=lvl,
                                marginal_effect_per_sd=me, se=se, p=p))
    return pd.DataFrame(out)


# ============================================================
# 2. 读数
# ============================================================
def load_data(root: Path, metrics_arg, panel_arg):
    dirs = [root / "analysis" / "data" / "integrated" / "q3_equity",
            root / "data" / "integrated" / "q3_equity"]
    mpath = Path(metrics_arg) if metrics_arg else find_file(root, "q3_equity_metrics.csv", dirs)
    ppath = Path(panel_arg) if panel_arg else find_file(root, "q3_equity_panel.csv", dirs)
    if not mpath or not ppath or not mpath.exists() or not ppath.exists():
        raise FileNotFoundError("找不到 q3_equity_metrics.csv / q3_equity_panel.csv，"
                                "请用 --root 或 --metrics/--panel 指定路径")
    log(f"- metrics: `{mpath}`")
    log(f"- panel:   `{ppath}`")
    m = pd.read_csv(mpath).sort_values("year").reset_index(drop=True)
    p = pd.read_csv(ppath, low_memory=False)
    p["province"] = p["province"].astype(str).str.strip()
    extra = sorted(set(p["province"]) - STD31)
    if extra:
        log(f"- 面板含 {len(extra)} 个非 31 省标准名条目，已剔除: {', '.join(extra)}")
        p = p[p["province"].isin(STD31)].copy()
    dup = int(p.duplicated(["province", "year"]).sum())
    if dup:
        log(f"- 发现 {dup} 个重复的省-年行，已按数值列取均值合并（请回 processing/integrating 核查来源）")
        p = p.groupby(["province", "year"], as_index=False).mean(numeric_only=True)
    p["zone"] = p["province"].map(P2Z)
    log(f"- metrics: {len(m)} 年 × {m.shape[1]} 列；panel: {len(p)} 行，{p['province'].nunique()} 省，"
        f"{int(p['year'].min())}–{int(p['year'].max())}，重复省-年 {dup}")
    wb = [c for c in p.columns if c.startswith("wb_")]
    if wb:
        log(f"- 面板含 {len(wb)} 个 wb_* 国家级列：全省同值，本分析**不**将其与省变量回归")
    return m, p


def latest_year(p: pd.DataFrame, col: str, min_n: int = 20):
    if col not in p.columns:
        return None
    c = p.dropna(subset=[col]).groupby("year")["province"].nunique()
    c = c[c >= min_n]
    return int(c.index.max()) if len(c) else None


# ============================================================
# 3. 图表
# ============================================================
def savefig(fig, path: Path):
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def annotate_ends(ax, x, y, fmt="{:.3f}"):
    s = pd.DataFrame({"x": x, "y": y}).dropna()
    if s.empty:
        return
    for r in (s.iloc[0], s.iloc[-1]):
        ax.annotate(fmt.format(r["y"]), (r["x"], r["y"]), textcoords="offset points",
                    xytext=(0, 8), ha="center", fontsize=8)


def fig_trends_4panel(m, C, path):
    specs = [(C["gini_inc"], "收入基尼系数（实际收入）", "#1f77b4", "{:.3f}", False),
             (C["p9010"], "收入 P90/P10 分位比", "#d62728", "{:.2f}", False),
             (C["tb_share"], "泰尔指数：地带间份额", "#2ca02c", "{:.1%}", False),
             (C["gini_beds"], "床位基尼系数（每万人床位，纵轴从 0 起）", "#9467bd", "{:.3f}", True)]
    fig, axes = plt.subplots(2, 2, figsize=(11, 7.5))
    for ax, (col, title, color, fmt, zero) in zip(axes.ravel(), specs):
        if col is None or col not in m or m[col].notna().sum() == 0:
            ax.set_visible(False)
            continue
        ax.plot(m["year"], m[col], marker="o", color=color, lw=2)
        annotate_ends(ax, m["year"], m[col], fmt)
        ax.set_title(title, fontsize=11)
        ax.set_xticks(m["year"].dropna().astype(int))
        ax.tick_params(axis="x", rotation=45)
        ax.grid(alpha=.3)
        if zero:
            ax.set_ylim(0, m[col].max() * 1.6)
        else:
            lo, hi = m[col].min(), m[col].max()
            pad = (hi - lo) * 0.25 or abs(hi) * 0.05
            ax.set_ylim(lo - pad, hi + pad * 1.4)
        if "share" in title or "份额" in title:
            ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    fig.suptitle("Q3-3.1 年度公平性趋势（31 省横截面，省等权）", fontsize=13)
    savefig(fig, path)


def fig_theil_stack(m, C, path):
    sh = C["tb_share"]
    b = m[sh].values
    w = 1 - b
    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    yrs = m["year"].astype(int).values
    ax.bar(yrs, b, color="#1f77b4", label="地带间（东/中/西差距）")
    ax.bar(yrs, w, bottom=b, color="#ff9f4a", label="地带内")
    for x, bb, ww in zip(yrs, b, w):
        if not np.isnan(bb):
            ax.text(x, bb / 2, f"{bb:.0%}", ha="center", va="center", color="white", fontsize=9)
            ax.text(x, bb + ww / 2, f"{ww:.0%}", ha="center", va="center", fontsize=9)
    ax.set_ylim(0, 1.14)
    ax.set_xticks(yrs)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    ax.set_ylabel("占泰尔指数的份额")
    if C["theil"] and C["theil"] in m:
        for x, t in zip(yrs, m[C["theil"]]):
            if not np.isnan(t):
                ax.text(x, 1.02, f"T={t:.3f}", ha="center", va="bottom", fontsize=8)
    ax.legend(loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.08))
    ax.set_title("Q3-3.1 泰尔指数分解：地带间 vs 地带内份额（T = Tb + Tw）")
    savefig(fig, path)


def fig_three_axis(m, C, path):
    need = [C["gini_inc"], C["p9010"]]
    if any(c is None for c in need):
        raise ValueError("缺少基尼或 P90/P10 列")
    yrs = m["year"].astype(int)
    tb = m[C["tb"]] if C["tb"] else m[C["tb_share"]] * m[C["theil"]]
    tw = m[C["tw"]] if C["tw"] else m[C["theil"]] - tb
    fig, ax1 = plt.subplots(figsize=(10, 5.8))
    fig.subplots_adjust(right=0.78)
    l1 = ax1.plot(yrs, tb, color="#1f77b4", marker="o", label="泰尔·地带间 Tb（左轴）")
    l1 += ax1.plot(yrs, tw, color="#1f77b4", marker="s", ls="--", label="泰尔·地带内 Tw（左轴）")
    ax1.set_ylabel("泰尔分量", color="#1f77b4")
    ax2 = ax1.twinx()
    l2 = ax2.plot(yrs, m[C["gini_inc"]], color="#d62728", marker="^", label="收入基尼（右轴1）")
    ax2.set_ylabel("基尼系数", color="#d62728")
    ax3 = ax1.twinx()
    ax3.spines["right"].set_position(("outward", 60))
    l3 = ax3.plot(yrs, m[C["p9010"]], color="#2ca02c", marker="D", label="P90/P10（右轴2）")
    ax3.set_ylabel("P90/P10", color="#2ca02c")
    for a in (ax2, ax3):
        a.spines["right"].set_visible(True)
    ax1.set_xticks(yrs)
    ax1.grid(alpha=.3)
    ls = l1 + l2 + l3
    ax1.legend(ls, [l.get_label() for l in ls], loc="upper center", ncol=2, fontsize=9, frameon=False,
               bbox_to_anchor=(0.5, -0.08))
    ax1.set_title("Q3-3.1 三轴图：泰尔分量 / 基尼 / P90-P10（均为实际收入）")
    savefig(fig, path)


def fig_resource_gini(m, C, path):
    res = [(C[k], lab) for k, lab in
           [("gini_beds", "床位"), ("gini_docs", "医生"), ("gini_nurs", "护士"), ("gini_tech", "卫生技术人员")]
           if C[k]]
    zones = [(f"gini_beds_{z}", z) for z in REGION3 if f"gini_beds_{z}" in m.columns]
    fig, axes = plt.subplots(1, 2 if zones else 1, figsize=(12 if zones else 7, 5.2), squeeze=False)
    ax = axes[0][0]
    for col, lab in res:
        s = m[["year", col]].dropna()
        ax.plot(s["year"], s[col], marker="o", label=lab)
    ax.set_title("省级医疗资源基尼系数（每万人口）")
    ax.set_ylabel("基尼系数")
    ax.set_ylim(bottom=0)
    ax.grid(alpha=.3)
    ax.legend(frameon=False)
    if zones:
        ax = axes[0][1]
        for col, z in zones:
            s = m[["year", col]].dropna()
            ax.plot(s["year"], s[col], marker="o", color=ZONE_COLORS[z], label=f"{z}")
        ax.set_title("三大地带内部床位基尼（地带内差异）")
        ax.set_ylim(bottom=0)
        ax.grid(alpha=.3)
        ax.legend(frameon=False)
    fig.suptitle("Q3-3.2 医疗资源公平性的年际变化", fontsize=13)
    savefig(fig, path)


def fig_lorenz(p, path, table_rows):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5))
    colors = ["#1f77b4", "#d62728", "#2ca02c"]
    pop = "pop_2020_wan" if "pop_2020_wan" in p.columns else None
    for ax, weighted in zip(axes, (False, True)):
        if weighted and not pop:
            ax.set_visible(False)
            continue
        ax.plot([0, 1], [0, 1], "k--", lw=1, label="完全公平")
        for (col, lab, _), c in zip(RESOURCES, colors):
            yr = latest_year(p, col)
            if yr is None:
                continue
            d = p[p["year"] == yr].dropna(subset=[col] + ([pop] if weighted else []))
            x, y, g = lorenz(d[col].values, d[pop].values if weighted else None)
            ax.plot(x, y, color=c, lw=2, label=f"{lab}（{yr}）G={g:.3f}")
            table_rows.append(dict(resource=col, year=yr, weighting="人口加权(pop_2020)" if weighted else "省等权",
                                   n_provinces=len(d), gini=g))
        ax.set_xlabel("人口累计份额" if weighted else "省份累计份额（按人均量升序）")
        ax.set_ylabel("资源累计份额")
        ax.set_title("人口加权洛伦兹曲线" if weighted else "省等权洛伦兹曲线")
        ax.set_aspect("equal")
        ax.grid(alpha=.3)
        ax.legend(frameon=False, loc="upper left", fontsize=9)
    fig.suptitle("Q3-3.2 省级医疗资源洛伦兹曲线", fontsize=13)
    savefig(fig, path)


def fig_province_rank(p, path):
    fig, axes = plt.subplots(1, 3, figsize=(18, 9))
    for ax, (col, lab, _) in zip(axes, RESOURCES):
        yr = latest_year(p, col)
        if yr is None:
            ax.set_visible(False)
            continue
        d = p[p["year"] == yr].dropna(subset=[col]).sort_values(col)
        ax.barh(d["province"], d[col], color=[ZONE_COLORS[z] for z in d["zone"]])
        ax.axvline(d[col].mean(), color="k", ls="--", lw=1)
        ax.set_title(f"{lab}（{yr}）  虚线=省均值", fontsize=11)
        ax.tick_params(axis="y", labelsize=8)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in ZONE_COLORS.values()]
    fig.legend(handles, ZONE_COLORS.keys(), loc="lower center", ncol=3, frameon=False)
    fig.suptitle("Q3-3.2 各省医疗资源横截面排名（颜色=三大地带）", fontsize=13)
    fig.tight_layout(rect=(0, 0.04, 1, 0.97))
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def fig_resource_income(p, path, table_rows):
    if "econ_income_total" not in p.columns:
        raise ValueError("缺少 econ_income_total")
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.5))
    for ax, (col, lab, _) in zip(axes, RESOURCES):
        d = p.dropna(subset=["econ_income_total", col])
        if d.empty:
            ax.set_visible(False)
            continue
        sc = ax.scatter(d["econ_income_total"], d[col], c=d["year"], cmap="viridis", s=28, alpha=.8)
        slope, icpt, r, pv, _ = stats.linregress(d["econ_income_total"], d[col])
        xs = np.linspace(d["econ_income_total"].min(), d["econ_income_total"].max(), 50)
        ax.plot(xs, icpt + slope * xs, color="#d62728", lw=2, label=f"拟合线 r={r:.2f}, p={pv:.3g}")
        yr = d["year"].max()
        for _, row in d[d["year"] == yr].iterrows():
            ax.annotate(row["province"], (row["econ_income_total"], row[col]), fontsize=6.5,
                        xytext=(3, 3), textcoords="offset points", alpha=.8)
        ax.set_xlabel("人均可支配收入 econ_income_total")
        ax.set_ylabel(lab)
        ax.set_title(f"{lab} vs 收入（标注为 {int(yr)} 年）")
        ax.grid(alpha=.3)
        ax.legend(frameon=False, fontsize=9)
        table_rows.append(dict(resource=col, n=len(d), pearson_r=r, slope=slope, p_value=pv))
    fig.colorbar(sc, ax=axes, label="年份", shrink=.8)
    fig.suptitle("Q3-3.2 医疗资源-经济 散点（合并各年，无控制变量；相关≠因果）", fontsize=13)
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def fig_elderly(p, path, table_rows):
    """老龄化床位压力。
    beds_per_10k_elderly 的绝对量级与 2019→2021 的口径存在断层（分母疑为抽样样本量，见 q3_report.md），
    因此图中使用“相对当年全省均值的指数(=100)”，只比较同一年内不同组别的相对位置。"""
    col = "beds_per_10k_elderly"
    if col not in p.columns:
        raise ValueError("缺少 beds_per_10k_elderly")
    d = p.dropna(subset=[col]).copy()
    if d.empty:
        raise ValueError("beds_per_10k_elderly 全为空")
    d["idx"] = d[col] / d.groupby("year")[col].transform("mean") * 100
    if "econ_income_total" in d.columns:
        d["tier"] = d.groupby("year")["econ_income_total"].transform(
            lambda s: pd.qcut(s, 3, labels=["低收入省", "中收入省", "高收入省"]) if s.notna().sum() >= 6 else np.nan)
    yrs = sorted(d["year"].unique())
    fig, axes = plt.subplots(1, 2 if "tier" in d else 1, figsize=(14 if "tier" in d else 7.5, 5.5), squeeze=False)
    groups = [(list(ZONE_COLORS), "zone", ZONE_COLORS, "按三大地带")]
    if "tier" in d:
        groups.append((["低收入省", "中收入省", "高收入省"], "tier",
                       {"低收入省": "#9ecae1", "中收入省": "#4292c6", "高收入省": "#08519c"}, "按收入三分位"))
    for ax, (levels, key, colors, title) in zip(axes[0], groups):
        w = 0.8 / len(levels)
        for i, lv in enumerate(levels):
            g = d[d[key] == lv].groupby("year")["idx"].mean().reindex(yrs)
            raw = d[d[key] == lv].groupby("year")[col].mean().reindex(yrs)
            ax.bar(np.arange(len(yrs)) + i * w - 0.4 + w / 2, g.values, w, label=lv, color=colors[lv])
            for yv in g.dropna().index:
                table_rows.append(dict(group_by=key, group=lv, year=int(yv),
                                       beds_per_10k_elderly_mean_raw=raw[yv], index_vs_all_province_mean=g[yv]))
        ax.axhline(100, color="gray", ls=":")
        ax.set_xticks(range(len(yrs)))
        ax.set_xticklabels([int(y) for y in yrs])
        ax.set_ylabel("相对当年全省均值的指数（=100）")
        ax.set_title(f"老龄化床位压力（{title}）")
        ax.set_ylim(0, max(140, d["idx"].max() * 1.05))
        ax.legend(frameon=False, loc="upper center", ncol=3, bbox_to_anchor=(0.5, -0.08))
        ax.grid(axis="y", alpha=.3)
    fig.suptitle("Q3-3.2 老龄化床位压力（相对指数；仅含有 65+ 人口的年份，原始量级与 2021 年口径存疑）", fontsize=12)
    savefig(fig, path)


def fig_convergence(m, C, path):
    inc, env = C["gini_inc"], C["gini_env"]
    if not inc or not env:
        raise ValueError("缺少收入基尼或环境基尼列")
    d = m[["year", inc, env]].dropna()
    if len(d) < 2:
        raise ValueError("环境基尼有效年份不足 2 年")
    d = d.copy()
    d["income_index"] = d[inc] / d[inc].iloc[0] * 100
    d["env_index"] = d[env] / d[env].iloc[0] * 100
    span = d["year"].iloc[-1] - d["year"].iloc[0]
    rows = []
    for lab, col in (("收入基尼", inc), ("PM2.5 基尼（环境）", env)):
        a, b = d[col].iloc[0], d[col].iloc[-1]
        rows.append(dict(indicator=lab, start_year=int(d["year"].iloc[0]), end_year=int(d["year"].iloc[-1]),
                         start=a, end=b, pct_change=(b / a - 1) * 100, pct_per_year=(b / a - 1) * 100 / span,
                         verdict="趋于收敛(下降)" if b < a else "趋于发散(上升)"))
    # 收入基尼全期
    s = m[["year", inc]].dropna()
    a, b = s[inc].iloc[0], s[inc].iloc[-1]
    spn = s["year"].iloc[-1] - s["year"].iloc[0]
    rows.append(dict(indicator="收入基尼（全期，参照）", start_year=int(s["year"].iloc[0]), end_year=int(s["year"].iloc[-1]),
                     start=a, end=b, pct_change=(b / a - 1) * 100, pct_per_year=(b / a - 1) * 100 / spn,
                     verdict="趋于收敛(下降)" if b < a else "趋于发散(上升)"))
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    ax = axes[0]
    ax.plot(d["year"], d["income_index"], marker="o", color="#1f77b4", label="收入基尼")
    ax.plot(d["year"], d["env_index"], marker="s", color="#d62728", label="PM2.5 基尼（环境）")
    ax.axhline(100, color="gray", ls=":")
    ax.set_xticks(d["year"].astype(int))
    ax.set_ylabel(f"指数（{int(d['year'].iloc[0])} = 100）")
    ax.set_title("同期收敛速度对比（<100 = 更公平）")
    ax.legend(frameon=False)
    ax.grid(alpha=.3)
    ax = axes[1]
    ax.plot(d["year"], d[inc], marker="o", color="#1f77b4", label="收入基尼（左）")
    ax.set_ylabel("收入基尼", color="#1f77b4")
    ax2 = ax.twinx()
    ax2.plot(d["year"], d[env], marker="s", color="#d62728", label="PM2.5 基尼（右）")
    ax2.set_ylabel("PM2.5 基尼", color="#d62728")
    ax2.spines["right"].set_visible(True)
    ax.set_xticks(d["year"].astype(int))
    ax.set_title("原始水平（双轴）")
    ax.grid(alpha=.3)
    fig.suptitle("Q3-3.2 收入公平性 vs 环境公平性：谁收敛更快？（仅环境有值的年份）", fontsize=13)
    savefig(fig, path)
    return pd.DataFrame(rows), d


def fig_coef(res_tabs, path):
    sel = [(lab, t) for lab, t in res_tabs if lab in ("M1 省+年FE(需求设定)", "M2 地带+年FE", "M3 地带+年FE+交互")]
    core = [v for v, _ in REG_VARS]
    names = dict(REG_VARS)
    fig, ax = plt.subplots(figsize=(10, 5.8))
    colors = ["#7f7f7f", "#1f77b4", "#d62728"]
    for j, (lab, t) in enumerate(sel):
        tt = t[t["term"].isin(core)].set_index("term").reindex(core)
        ypos = np.arange(len(core)) + (j - 1) * 0.25
        ax.errorbar(tt["coef_per_sd"], ypos, xerr=[tt["coef_per_sd"] - tt["ci_low"], tt["ci_high"] - tt["coef_per_sd"]],
                    fmt="o", color=colors[j], capsize=3, label=lab)
    ax.axvline(0, color="k", lw=1)
    ax.set_yticks(range(len(core)))
    ax.set_yticklabels([names[c] for c in core])
    ax.invert_yaxis()
    ax.set_xlabel("系数：解释变量每增加 1 个标准差，急诊病死率的变化（95% CI，省聚类稳健）")
    ax.legend(frameon=False, fontsize=9)
    ax.grid(axis="x", alpha=.3)
    ax.set_title("Q3-3.3 面板回归系数（某模型缺点 = 该变量被固定效应吸收）")
    savefig(fig, path)


def fig_city(path, city_df, col, lon_ok, moran_res):
    x, y, g = lorenz(city_df[col].values)
    fig, ax = plt.subplots(figsize=(6.5, 6))
    ax.plot([0, 1], [0, 1], "k--", lw=1)
    ax.plot(x, y, color="#1f77b4", lw=2, label=f"{col}  G={g:.3f}")
    ax.set_title(f"城市级洛伦兹曲线（{len(city_df)} 城）" +
                 (f"\nMoran's I={moran_res[0]:.3f}, p={moran_res[2]:.3f}" if moran_res else ""))
    ax.set_xlabel("城市累计份额")
    ax.set_ylabel("资源累计份额")
    ax.set_aspect("equal")
    ax.grid(alpha=.3)
    ax.legend(frameon=False)
    savefig(fig, path)
    return g


# ============================================================
# 4. 城市级可选模块
# ============================================================
def flatten(coords):
    if isinstance(coords[0], (int, float)):
        yield coords
        return
    for ch in coords:
        yield from flatten(ch)


def city_module(root: Path, figdir: Path, outdir: Path):
    cpath = find_file(root, "q2_healthcare_accessibility_city.csv", [])
    if not cpath:
        log("- 城市级模块：未找到 q2_healthcare_accessibility_city.csv，已跳过")
        return None
    df = pd.read_csv(cpath)
    col = pick(df, "hospital_count_window", "hospitals_window", "hospitals_30min")
    if col is None:
        log(f"- 城市级模块：{cpath.name} 中无 hospital_count_window / hospitals_30min 列，已跳过")
        return None
    df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=[col]).copy()
    res = dict(variable=col, n_cities=len(df), file=str(cpath))
    gpath = find_file(root, "geo_boundary.geojson", [])
    moran = None
    if gpath:
        geo = json.loads(gpath.read_text(encoding="utf-8"))
        cen = {}
        for f in geo.get("features", []):
            pr = f.get("properties", {})
            if pr.get("level") != "city":
                continue
            pts = np.array(list(flatten(f["geometry"]["coordinates"])), float)
            cen[pr["name"]] = (pts[:, 0].mean(), pts[:, 1].mean())
        df["lon"] = df["city"].map(lambda c: cen.get(c, (np.nan, np.nan))[0])
        df["lat"] = df["city"].map(lambda c: cen.get(c, (np.nan, np.nan))[1])
        dm = df.dropna(subset=["lon", "lat"])
        if len(dm) >= 30:
            moran = morans_i(dm[col].values, dm["lon"].values, dm["lat"].values)
            res.update(n_with_coords=len(dm), moran_I=moran[0], moran_expected_perm=moran[1], moran_p_perm=moran[2])
    else:
        log("- 城市级模块：未找到 geo_boundary.geojson，仅做洛伦兹/基尼，未算 Moran's I")
    g = fig_city(figdir / "q3_2_city_lorenz.png", df, col, bool(gpath), moran)
    res["gini"] = g
    pd.DataFrame([res]).to_csv(outdir / "q3_2_city_equity.csv", index=False, encoding="utf-8-sig")
    return res


# ============================================================
# 5. 主流程
# ============================================================
def safe(name, fn, *a, **k):
    try:
        return fn(*a, **k)
    except Exception as e:  # noqa: BLE001
        FAILED.append(f"{name}: {type(e).__name__}: {e}")
        print(f"[失败] {name}: {e}")
        traceback.print_exc()
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root")
    ap.add_argument("--metrics")
    ap.add_argument("--panel")
    ap.add_argument("--no-city", action="store_true")
    args = ap.parse_args()

    setup_font()
    root = find_root(args.root)
    outdir = HERE / "outputs"
    figdir = root / "visualization" / "q3_equity"
    outdir.mkdir(parents=True, exist_ok=True)
    figdir.mkdir(parents=True, exist_ok=True)
    log(f"- 项目根目录: `{root}`")
    m, p = load_data(root, args.metrics, args.panel)

    gm = lambda *c: pick(m, *c)  # noqa: E731
    C = dict(
        gini_inc=gm("gini_real_income"), p9010=gm("income_p90_p10"),
        theil=gm("theil_real_income"), tb=gm("theil_between_real_income"), tw=gm("theil_within_real_income"),
        tb_share=gm("theil_between_share", "theil_between_share_real_income"),
        gini_beds=gm("gini_per10k_beds_all"), gini_docs=gm("gini_per10k_doctors"),
        gini_nurs=gm("gini_per10k_nurses"), gini_tech=gm("gini_per10k_health_tech"),
        gini_env=gm("gini_air_pm25", "gini_air_pm25_mean"),
    )
    if C["tb_share"] is None and C["tb"] and C["theil"]:
        m["theil_between_share"] = m[C["tb"]] / m[C["theil"]]
        C["tb_share"] = "theil_between_share"
    miss = [k for k, v in C.items() if v is None]
    if miss:
        log(f"- metrics 缺少列（相关图表将跳过）: {', '.join(miss)}")

    # ---------------- 3.1 ----------------
    trend_items = [("收入基尼（实际收入）", C["gini_inc"]), ("收入 P90/P10", C["p9010"]),
                   ("泰尔 T（实际收入）", C["theil"]), ("泰尔：地带间份额", C["tb_share"]),
                   ("床位基尼", C["gini_beds"]), ("医生基尼", C["gini_docs"]), ("护士基尼", C["gini_nurs"]),
                   ("卫生技术人员基尼", C["gini_tech"]), ("PM2.5 基尼（环境）", C["gini_env"])]
    trend_items += [(f"床位基尼·{z}内部", f"gini_beds_{z}") for z in REGION3 if f"gini_beds_{z}" in m.columns]
    rows = []
    for lab, col in trend_items:
        if not col or col not in m:
            continue
        s = m[["year", col]].dropna()
        if len(s) < 2:
            continue
        a, b = s[col].iloc[0], s[col].iloc[-1]
        pct = (b / a - 1) * 100 if a else np.nan
        tau, pv = kendall(s["year"], s[col])
        rows.append(dict(indicator=lab, column=col, n_years=len(s), start_year=int(s["year"].iloc[0]),
                         start=a, end_year=int(s["year"].iloc[-1]), end=b, abs_change=b - a, pct_change=pct,
                         direction=direction(pct), kendall_tau=tau, kendall_p=pv))
    trend = pd.DataFrame(rows)
    trend.to_csv(outdir / "q3_1_trend_summary.csv", index=False, encoding="utf-8-sig")

    safe("fig 3.1 四子图", fig_trends_4panel, m, C, figdir / "q3_1_equity_trends_4panel.png") if C["gini_inc"] else None
    safe("fig 3.1 泰尔堆叠", fig_theil_stack, m, C, figdir / "q3_1_theil_decomposition.png") if C["tb_share"] else None
    safe("fig 3.1 三轴图", fig_three_axis, m, C, figdir / "q3_1_three_axis.png")

    # ---------------- 3.2 ----------------
    gcols = {"year": m["year"]}
    for k in ("gini_beds", "gini_docs", "gini_nurs", "gini_tech"):
        if C[k]:
            gcols[C[k]] = m[C[k]]
    for z in REGION3:
        if f"gini_beds_{z}" in m.columns:
            gcols[f"gini_beds_{z}"] = m[f"gini_beds_{z}"]
    pd.DataFrame(gcols).to_csv(outdir / "q3_2_resource_gini_by_year.csv", index=False, encoding="utf-8-sig")
    safe("fig 3.2 资源基尼趋势", fig_resource_gini, m, C, figdir / "q3_2_resource_gini_trend.png")

    lor_rows, sc_rows, eld_rows = [], [], []
    safe("fig 3.2 洛伦兹", fig_lorenz, p, figdir / "q3_2_resource_lorenz.png", lor_rows)
    safe("fig 3.2 省级排名", fig_province_rank, p, figdir / "q3_2_resource_province_rank.png")
    safe("fig 3.2 资源-收入散点", fig_resource_income, p, figdir / "q3_2_resource_vs_income.png", sc_rows)
    safe("fig 3.2 老龄化", fig_elderly, p, figdir / "q3_2_elderly_beds_pressure.png", eld_rows)
    if lor_rows:
        pd.DataFrame(lor_rows).to_csv(outdir / "q3_2_resource_lorenz_gini.csv", index=False, encoding="utf-8-sig")
    if sc_rows:
        pd.DataFrame(sc_rows).to_csv(outdir / "q3_2_resource_income_corr.csv", index=False, encoding="utf-8-sig")
    if eld_rows:
        pd.DataFrame(eld_rows).to_csv(outdir / "q3_2_elderly_beds_by_group.csv", index=False, encoding="utf-8-sig")
    lat_cols = [c for c, _, _ in RESOURCES if c in p.columns]
    snap = []
    for c in lat_cols:
        yr = latest_year(p, c)
        if yr:
            snap.append(p[p["year"] == yr][["province", "zone", c]].set_index(["province", "zone"]).rename(columns={c: f"{c}_{yr}"}))
    if snap:
        pd.concat(snap, axis=1).reset_index().to_csv(outdir / "q3_2_resource_province_latest.csv",
                                                     index=False, encoding="utf-8-sig")
    conv = safe("fig 3.2 收敛对比", fig_convergence, m, C, figdir / "q3_2_income_vs_env_convergence.png")
    conv_tab = None
    if conv:
        conv_tab, _ = conv
        conv_tab.to_csv(outdir / "q3_2_convergence.csv", index=False, encoding="utf-8-sig")
    city = None if args.no_city else safe("城市级模块", city_module, root, figdir, outdir)

    # ---------------- 3.3 ----------------
    y_col = pick(p, "outcome_er_mortality_rate", "outcome_er_mortality")
    reg_tabs, metas, mes = [], [], []
    diag = []
    if y_col is None:
        FAILED.append("3.3 回归: 面板缺少 outcome_er_mortality_rate")
    else:
        xs = [v for v, _ in REG_VARS if v in p.columns]
        for v in [y_col] + xs + ["acc_nearest_km_mean"]:
            if v not in p.columns:
                continue
            s = p.dropna(subset=[v])
            bw = s[v] - s.groupby("province")[v].transform("mean")
            diag.append(dict(variable=v, n_nonnull=len(s),
                             years=",".join(map(str, sorted(s["year"].unique().astype(int)))),
                             n_provinces=s["province"].nunique(),
                             within_province_var_share=(bw.var() / s[v].var()) if s[v].var() > 0 else np.nan))
        cc = p.dropna(subset=[y_col] + xs)
        diag.append(dict(variable="[完整样本: 因变量+全部核心变量]", n_nonnull=len(cc),
                         years=",".join(map(str, sorted(cc["year"].unique().astype(int)))),
                         n_provinces=cc["province"].nunique(), within_province_var_share=np.nan))
        pd.DataFrame(diag).to_csv(outdir / "q3_3_diagnostics.csv", index=False, encoding="utf-8-sig")

        specs = [("M1 省+年FE(需求设定)", xs, ["province", "year"], []),
                 ("M2 地带+年FE", xs, ["zone", "year"], []),
                 ("M2' 地带+年FE(可达性用均值,对照P90)",
                  [("acc_nearest_km_mean" if v == "acc_nearest_km_p90" else v) for v in xs],
                  ["zone", "year"], [])]
        trio = [v for v in ("econ_income_total", "acc_nearest_km_p90", "air_pm25_mean") if v in xs]
        inter = [(trio[i], trio[j]) for i in range(len(trio)) for j in range(i + 1, len(trio))]
        specs.append(("M3 地带+年FE+交互", xs, ["zone", "year"], inter))
        for lab, xv, fe, it in specs:
            if any(v not in p.columns for v in xv):
                continue
            r = run_model(p, lab, y_col, xv, fe, it)
            if r is None:
                FAILED.append(f"3.3 回归 {lab}: 样本或自由度不足")
                continue
            tab, meta, fit = r
            reg_tabs.append((lab, tab))
            metas.append(meta)
            if it:
                mes.append(marginal_effects(fit, trio, lab))
        if reg_tabs:
            allreg = pd.concat([t for _, t in reg_tabs], ignore_index=True)
            allreg = allreg.merge(pd.DataFrame(metas)[["model", "n", "n_provinces", "years", "df_resid", "r2", "fe", "warning"]],
                                  on="model", how="left")
            allreg.to_csv(outdir / "q3_3_regression.csv", index=False, encoding="utf-8-sig")
            safe("fig 3.3 系数图", fig_coef, reg_tabs, figdir / "q3_3_regression_coefficients.png")
        if mes:
            pd.concat(mes).to_csv(outdir / "q3_3_marginal_effects.csv", index=False, encoding="utf-8-sig")

    write_report(outdir, m, p, C, trend, lor_rows, sc_rows, conv_tab, city, y_col, reg_tabs, metas,
                 pd.concat(mes) if mes else None, pd.DataFrame(diag))
    print(f"\nQ3 完成。表格与报告: {outdir}\n图表: {figdir}")


# ============================================================
# 6. 自动报告
# ============================================================
def fnum(x, d=3):
    return "—" if pd.isna(x) else f"{x:.{d}f}"


def write_report(outdir, m, p, C, trend, lor_rows, sc_rows, conv, city, y_col, reg_tabs, metas, mes, diag):
    L = ["# Q3 公平性分析报告（脚本自动生成，数值均来自本次运行）", "",
         "## 0. 数据检查", *LOG, ""]
    if FAILED:
        L += ["**本次运行未成功的部分：**", *[f"- {f}" for f in FAILED], ""]

    L += ["## 1. 年度公平性趋势（q3_equity_metrics）", "",
          "| 指标 | 起点 | 终点 | 变化 | 方向 | Kendall τ (p) |", "|---|---|---|---|---|---|"]
    for _, r in trend.iterrows():
        L.append(f"| {r['indicator']} | {int(r['start_year'])}: {fnum(r['start'])} | {int(r['end_year'])}: {fnum(r['end'])} | "
                 f"{r['pct_change']:+.1f}% | {r['direction']} | {fnum(r['kendall_tau'], 2)} ({fnum(r['kendall_p'], 3)}) |")
    L += ["", "> 基尼/泰尔为省等权口径；年度点数 ≤10，Kendall 检验功效有限；“基本稳定”指累计变化 <5%。", ""]
    if C["tb_share"]:
        s = m[["year", C["tb_share"]]].dropna()
        L.append(f"- 泰尔分解：地带间份额从 {s['year'].iloc[0]:.0f} 年 {s.iloc[0, 1]:.1%} 变为 {s['year'].iloc[-1]:.0f} 年 "
                 f"{s.iloc[-1, 1]:.1%}，"
                 f"{'仍超过一半，东/中/西地带间的结构性差距是收入不平等的主要来源' if s.iloc[-1, 1] > 0.5 else '已降至一半以下，地带内差异占比上升'}。")
    L.append("")

    L += ["## 2. 医疗资源公平性横截面", ""]
    if lor_rows:
        L += ["**洛伦兹/基尼（各资源取有 ≥20 省数据的最近一年）**", "", "| 资源 | 年份 | 口径 | 省数 | 基尼 |", "|---|---|---|---|---|"]
        for r in lor_rows:
            L.append(f"| {r['resource']} | {r['year']} | {r['weighting']} | {r['n_provinces']} | {r['gini']:.3f} |")
        L.append("")
    if sc_rows:
        L += ["**资源-收入相关（合并各年，描述性）**", "", "| 资源 | n | Pearson r | p |", "|---|---|---|---|"]
        for r in sc_rows:
            L.append(f"| {r['resource']} | {r['n']} | {r['pearson_r']:.2f} | {r['p_value']:.3g} |")
        L.append("")
    if conv is not None:
        L += ["**收入公平性 vs 环境公平性（仅环境有值的年份比较）**", "",
              "| 指标 | 区间 | 起 | 止 | 累计变化 | 年均变化 | 判断 |", "|---|---|---|---|---|---|---|"]
        for _, r in conv.iterrows():
            L.append(f"| {r['indicator']} | {r['start_year']}–{r['end_year']} | {fnum(r['start'])} | {fnum(r['end'])} | "
                     f"{r['pct_change']:+.1f}% | {r['pct_per_year']:+.2f}%/年 | {r['verdict']} |")
        L += ["", "> 环境基尼仅 2–3 个年份有值，只能比较方向与大致速度，不能做显著性判断。", ""]
    if city:
        L += ["**城市级（可选）**", "",
              f"- 变量 `{city['variable']}`，{city['n_cities']} 城，基尼 {city['gini']:.3f}"
              + (f"，Moran's I = {city['moran_I']:.3f}（置换 p = {city['moran_p_perm']:.3f}）" if 'moran_I' in city else "（未计算 Moran's I）"),
              "- 可达性为单快照，仅作横截面解读，不做时序。", ""]

    L += ["## 3. 面板回归（公平性驱动因素）", ""]
    if y_col and reg_tabs:
        L.append(f"因变量：`{y_col}`。解释变量先标准化，`coef_per_sd` = 解释变量变化 1 个标准差时因变量的变化。标准误按省聚类（CRV1，t(G-1) 分布）。")
        L += ["", "**样本诊断（决定了模型能识别什么）**", "",
              "| 变量 | 非空行 | 有值年份 | 省内变异占比 |", "|---|---|---|---|"]
        for _, r in diag.iterrows():
            L.append(f"| {r['variable']} | {r['n_nonnull']} | {r['years']} | {fnum(r['within_province_var_share'], 2)} |")
        L += ["", "> “省内变异占比”≈0 的变量（如可达性快照）在含省固定效应的模型里无法识别，会被自动剔除。", ""]
        for (lab, tab), meta in zip(reg_tabs, metas):
            L += [f"### {lab}", f"- n={meta['n']}，省={meta['n_provinces']}，年份={meta['years']}，参数数={meta['k_params']}，"
                  f"残差自由度={meta['df_resid']}，R²={fnum(meta['r2'])}，FE={meta['fe']}"
                  + (f"，**警告：{meta['warning']}**" if meta["warning"] else ""), "",
                  "| 变量 | 系数/SD | 聚类SE | p | 判断 |", "|---|---|---|---|---|"]
            for _, r in tab.iterrows():
                if r["note"]:
                    L.append(f"| {r['term']} | — | — | — | {r['note']} |")
                else:
                    L.append(f"| {r['term']} | {r['coef_per_sd']:.4f} | {r['se']:.4f} | {r['p']:.3f} | {sig_word(r['p'])} |")
            L.append("")
        if mes is not None and len(mes):
            L += ["### 边际效应（M3；其它变量取 −1/0/+1 SD 时）", "",
                  "完整表见 `q3_3_marginal_effects.csv`。", ""]
            sig = mes[mes["p"] < 0.10]
            L.append("- 达到 p<0.10 的边际效应：" + ("、".join(
                f"{r.variable} 在 {r.moderator}={int(r.moderator_level_sd):+d}SD 时 {r.marginal_effect_per_sd:+.3f}(p={r.p:.3f})"
                for r in sig.itertuples()) if len(sig) else "无"))
            L.append("")
    else:
        L.append("回归未能运行，见上方“未成功的部分”。")
        L.append("")

    L += ["## 4. 解读边界", "",
          "1. 环境(PM2.5)仅 2023–2025 有值、资源至 2024 年、结局年份有限 → 回归重叠样本很小，结果只作探索性关联，**不是因果**。",
          "2. `acc_*` 是单快照（363 城 network 法），在省内不随时间变化：含省 FE 的模型无法估计其系数（M1 中被吸收）；因此另设地带+年 FE 的 M2/M3 利用其横截面差异，代价是遗漏省级不可观测特征。",
          "3. P90 与均值的对比见 M2 vs M2'：若 P90 的系数/显著性与均值不同，说明分布尾部的可达性差距携带了均值看不到的信息。",
          "4. 基尼/泰尔为省等权，不代表居民个体层面不平等；人口加权洛伦兹使用 `pop_2020_wan`（静态人口）。",
          "5. 2025 年的空值是“未发布”，不是 0，脚本未做任何填补。",
          "6. `wb_*` 为国家级同值变量，未与省变量做回归。", ""]
    (outdir / "q3_report.md").write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    main()
