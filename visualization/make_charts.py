# -*- coding: utf-8 -*-
"""HealthMap 汇报 PPT 数据可视化图表生成（简体中文）
所有数字均来自仓库 README / docs/analysis.md / analysis_q2_focused.md / analysis_q2_spatial.md
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import os

FONT_PATH = "/System/Library/AssetsV2/com_apple_MobileAsset_Font7/eb257c12d1a51c8c661b89f30eec56cacf9b8987.asset/AssetData/STHEITI.ttf"
fm.fontManager.addfont(FONT_PATH)
_fp = fm.FontProperties(fname=FONT_PATH)
plt.rcParams["font.family"] = _fp.get_name()
plt.rcParams["axes.unicode_minus"] = False

PRIMARY = "#16597A"
TEAL    = "#2E8B8B"
ORANGE  = "#E8833A"
RED     = "#C0392B"
GRAY    = "#6B7280"
LIGHT   = "#EAF1F5"
# 图表输出到仓库根的 imgs/ 目录（从 visualization/ 上一级）
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "imgs")
os.makedirs(OUT, exist_ok=True)

def style_ax(ax, xgrid=False, ygrid=True):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#C9D2DA")
    ax.tick_params(colors="#3A4552", labelsize=11)
    if ygrid:
        ax.grid(axis="y", color="#E3E9EF", linewidth=0.8)
    if xgrid:
        ax.grid(axis="x", color="#E3E9EF", linewidth=0.8)
    ax.set_axisbelow(True)

def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved", name)

# ---------------------------------------------------------------- 1. 数据源体积
def chart_data_sources():
    names = ["S1 OSM 中国路网", "S2 百度医疗POI", "S3 环境数据", "S4 ERA5 气象",
             "S5 健康与医疗服务", "S6 省级经济指标", "S7 人口数据", "S8 行政区划边界"]
    mb    = [1536, 1.4, 13, 1600, 74, 11.2, 0.039, 4.6]
    types = ["矢量", "结构化", "结构化", "栅格", "统计", "统计", "统计", "矢量"]
    cmap  = {"矢量": PRIMARY, "结构化": TEAL, "栅格": ORANGE, "统计": "#7A93A8"}
    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    y = np.arange(len(names))[::-1]
    bars = ax.barh(y, mb, height=0.62, color=[cmap[t] for t in types])
    ax.set_xscale("log")
    ax.set_xlim(0.02, 6000)
    for yi, v in zip(y, mb):
        label = f"{v/1024:.1f} GB" if v >= 1024 else (f"{v:.1f} MB" if v >= 1 else f"{v*1000:.0f} KB")
        ax.text(v * 1.35, yi, label, va="center", fontsize=11, color="#3A4552")
    ax.set_yticks(y); ax.set_yticklabels(names, fontsize=11.5)
    ax.set_xticks([0.1, 1, 10, 100, 1000])
    ax.set_xticklabels(["0.1", "1", "10", "100", "1000"])
    ax.set_xlabel("数据体积（MB，对数刻度）", fontsize=11, color=GRAY)
    style_ax(ax, xgrid=True, ygrid=False)
    handles = [plt.Rectangle((0,0),1,1,color=c) for c in cmap.values()]
    ax.legend(handles, [f"{k}型数据" for k in cmap], fontsize=10.5, frameon=False,
              loc="lower right", ncol=4, bbox_to_anchor=(1.0, -0.22))
    save(fig, "data_sources.png")

# ---------------------------------------------------------------- 2. PM2.5 年均值
def chart_pm25():
    years = ["2023", "2024", "2025"]
    vals  = [40.3, 39.3, 44.7]
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    bars = ax.bar(years, vals, width=0.5, color=[PRIMARY, PRIMARY, ORANGE])
    for b, v in zip(bars, vals):
        ax.text(b.get_x()+b.get_width()/2, v+1.2, f"{v}", ha="center",
                fontsize=14, fontweight="bold", color="#25313D")
    ax.axhline(35, color=TEAL, ls="--", lw=1.6)
    ax.text(2.42, 35.6, "国家年均二级标准 35 µg/m³", color=TEAL, fontsize=10.5, ha="right")
    ax.axhline(5, color=RED, ls=":", lw=1.6)
    ax.text(2.42, 6.2, "WHO 2021 指导值 5 µg/m³", color=RED, fontsize=10.5, ha="right")
    ax.set_ylim(0, 52)
    ax.set_ylabel("PM2.5 年均值（µg/m³）", fontsize=11.5, color="#3A4552")
    ax.set_title("31 省 PM2.5 年均值：连续三年高于国家标准", fontsize=13.5,
                 color="#25313D", pad=12, loc="left")
    style_ax(ax)
    save(fig, "pm25.png")

# ---------------------------------------------------------------- 3. 每万人床位趋势
def chart_beds_trend():
    years = list(range(2016, 2025))
    vals  = [53.15, 56.94, 60.05, 62.86, 64.69, 67.04, 68.73, 71.83, 72.70]
    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    ax.plot(years, vals, marker="o", ms=6, lw=2.4, color=PRIMARY, zorder=3)
    ax.fill_between(years, vals, 45, color=PRIMARY, alpha=0.08)
    for x, v in zip(years, vals):
        ax.annotate(f"{v:.1f}", (x, v), textcoords="offset points", xytext=(0, 9),
                    ha="center", fontsize=10.5, color="#25313D")
    ax.set_ylim(45, 80)
    ax.set_xticks(years)
    ax.set_ylabel("每万人医疗卫生机构床位数（张）", fontsize=11.5, color="#3A4552")
    ax.set_title("2016–2024 年省级医疗资源稳步扩张（+37%）", fontsize=13.5,
                 color="#25313D", pad=12, loc="left")
    style_ax(ax)
    save(fig, "beds_trend.png")

# ---------------------------------------------------------------- 4. 就医可达性
def chart_accessibility():
    fig = plt.figure(figsize=(9.8, 4.6))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.5, 1], wspace=0.30)
    # 左：对数刻度分布带
    ax = fig.add_subplot(gs[0])
    ax.set_xscale("log")
    ax.add_patch(plt.Rectangle((20.65, 0.36), 54.52-20.65, 0.28, color=PRIMARY, alpha=0.88))
    ax.plot([35.30, 35.30], [0.36, 0.64], color="white", lw=2.4)
    ax.plot([77.20, 77.20], [0.30, 0.70], color=ORANGE, lw=2.4)
    ax.plot([1461.7, 1461.7], [0.30, 0.70], color=RED, lw=2.4)
    ax.plot([12, 20.65], [0.5, 0.5], color="#9AA7B2", lw=1.4)
    ax.plot([54.52, 77.20], [0.5, 0.5], color="#9AA7B2", lw=1.4)
    ax.text(20.65, 0.70, "P25 20.7", fontsize=10.5, ha="center", color="#3A4552")
    ax.text(54.52, 0.70, "P75 54.5", fontsize=10.5, ha="center", color="#3A4552")
    ax.text(35.30, 0.20, "中位数 35.3 分钟", fontsize=11, ha="center", color=PRIMARY,
            fontweight="bold")
    ax.text(77.20, 0.88, "P90 77.2", fontsize=10.5, ha="center", color="#B05E1C")
    ax.annotate("最大值 1461.7 分钟\n（边远城市极端值）", xy=(1461.7, 0.52), xytext=(430, 0.60),
                fontsize=10.5, color=RED, ha="center",
                arrowprops=dict(arrowstyle="->", color=RED, lw=1.2))
    ax.set_xlim(11, 2600); ax.set_ylim(0.10, 1.02)
    ax.set_yticks([])
    ticks = [12, 20, 35, 50, 100, 200, 500, 1000, 2000]
    ax.set_xticks(ticks)
    ax.set_xticklabels([str(t) for t in ticks], fontsize=10)
    ax.minorticks_off()
    ax.set_xlabel("最近医院就医时间 nearest_hospital_min（分钟，对数刻度，363 城快照）",
                  fontsize=10.5, color="#3A4552")
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#C9D2DA")
    ax.set_title("就医时间分布明显右偏", fontsize=13, color="#25313D", loc="left", pad=10)
    # 右：环形图
    ax2 = fig.add_subplot(gs[1])
    sizes = [90.63, 9.37]
    colors = [RED, "#D9E2E9"]
    ax2.pie(sizes, colors=colors, startangle=90, counterclock=False,
            wedgeprops=dict(width=0.34, edgecolor="white"))
    ax2.text(0, 0.12, "90.63%", ha="center", fontsize=25, fontweight="bold", color=RED)
    ax2.text(0, -0.22, "城市大医院\n30 分钟内不可达", ha="center", fontsize=11.5, color="#3A4552")
    ax2.set_title("329 / 363 城（操作性口径）", fontsize=12.5, color="#25313D", pad=6)
    save(fig, "accessibility.png")

# ---------------------------------------------------------------- 5. Q3 公平性斜率图
def chart_equity_slope():
    fig, axes = plt.subplots(1, 3, figsize=(10.6, 3.9))
    panels = [
        ("居民收入基尼系数", 0.191, 0.168, "0.191", "0.168", PRIMARY, False),
        ("收入 P90/P10",     2.04,  1.79,  "2.04",  "1.79",  PRIMARY, False),
        ("泰尔指数区间贡献占比", 55.9, 51.9, "55.9%", "51.9%", ORANGE, True),
    ]
    for ax, (title, v0, v1, s0, s1, c, pct) in zip(axes, panels):
        ax.plot([0, 1], [v0, v1], marker="o", ms=9, lw=3, color=c)
        ax.text(-0.06, v0, s0, ha="right", va="center", fontsize=13, fontweight="bold", color=c)
        ax.text(1.06, v1, s1, ha="left", va="center", fontsize=13, fontweight="bold", color=c)
        ax.set_xlim(-0.45, 1.45); ax.set_ylim(min(v0, v1)-0.12*abs(v1-v0)-1e-9, max(v0, v1)+0.12*abs(v1-v0)+1e-9)
        ax.set_xticks([0, 1]); ax.set_xticklabels(["2016", "2025"], fontsize=11.5)
        ax.set_yticks([])
        ax.set_title(title, fontsize=12.5, color="#25313D", pad=10)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.spines["bottom"].set_color("#C9D2DA")
        delta = v1 - v0
        ax.text(0.5, min(v0, v1) - 0.09*abs(v1-v0) - 1e-9, f"{'▼' if delta<0 else '▲'} {abs(delta):.3f}" if not pct else f"▼ {abs(delta):.1f} 个百分点",
                ha="center", fontsize=11, color="#1F7A4D" if delta < 0 else RED)
    fig.suptitle("2016→2025 公平性指标：全部单调改善（省等权口径）", fontsize=13.5,
                 color="#25313D", x=0.02, ha="left")
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    save(fig, "equity_slope.png")

# ---------------------------------------------------------------- 6. 地带基尼
def chart_zone_gini():
    zones = ["东部", "中部", "西部", "全国"]
    vals  = [0.574, 0.664, 0.727, 0.679]
    cols  = [PRIMARY, PRIMARY, RED, GRAY]
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    bars = ax.bar(zones, vals, width=0.52, color=cols)
    for b, v in zip(bars, vals):
        ax.text(b.get_x()+b.get_width()/2, v+0.012, f"{v:.3f}", ha="center",
                fontsize=13, fontweight="bold", color="#25313D")
    ax.set_ylim(0, 0.85)
    ax.set_ylabel("医院数分布基尼系数（城市级）", fontsize=11.5, color="#3A4552")
    ax.set_title("西部医院分布最不均衡：地带梯度成立", fontsize=13.5,
                 color="#25313D", pad=12, loc="left")
    style_ax(ax)
    save(fig, "zone_gini.png")

# ---------------------------------------------------------------- 7. 省份聚类（分组条形）
def chart_kmeans():
    fig, axes = plt.subplots(1, 2, figsize=(9.8, 4.0))
    groups = ["高收入高可达\n粤·苏·浙·闽", "边远低可达\n新·藏·蒙·黔·青·琼"]
    inc = [55, 31]; acc = [31, 78]
    cols = [PRIMARY, ORANGE]
    for ax, vals, ylab, title, fmt in (
        (axes[0], inc, "居民收入均值（千元）", "收入水平对比", "{:.0f}k"),
        (axes[1], acc, "平均大医院可达距离（km）", "可达性对比", "{:.0f} km"),
    ):
        bars = ax.bar(groups, vals, width=0.46, color=cols)
        for b, v in zip(bars, vals):
            ax.text(b.get_x()+b.get_width()/2, v*1.02, fmt.format(v), ha="center",
                    fontsize=13, fontweight="bold", color="#25313D")
        ax.set_ylabel(ylab, fontsize=11, color="#3A4552")
        ax.set_title(title, fontsize=12.5, color="#25313D", pad=10, loc="left")
        ax.set_ylim(0, max(vals)*1.22)
        ax.tick_params(axis="x", labelsize=11)
        style_ax(ax)
    fig.suptitle("KMeans 省份分层（k=3，2024 横截面，第三类为中间形态）", fontsize=13.5,
                 color="#25313D", x=0.02, ha="left")
    fig.tight_layout(rect=[0, 0, 1, 0.90])
    save(fig, "kmeans.png")

# ---------------------------------------------------------------- 8. 空间关联验证
def chart_pip_validation():
    fig, ax = plt.subplots(figsize=(8.8, 4.1))
    # 口径：两法一致率（数据源 docs/spatial_association_validation.md）
    items = ["S2 医疗 POI\n（9,893 点）", "363 城中心点\n（363 点）", "ERA5 气象格点\n（3,818 点，境外剔除）"]
    agree = [84.75, 79.06, 33.08]
    cols = [ORANGE, "#C98A3D", RED]
    y = np.arange(len(items))[::-1]
    ax.barh(y, agree, height=0.52, color=cols)
    for yi, v in zip(y, agree):
        ax.text(v+1.5, yi, f"{v:.2f}%", va="center", fontsize=12.5,
                color="#B05E1C", fontweight="bold")
    ax.axvline(100, color=PRIMARY, lw=1.6, ls="--")
    ax.text(98.5, y[0]+0.45, "严格 PIP 基准", ha="right", fontsize=10, color=PRIMARY)
    ax.set_yticks(y); ax.set_yticklabels(items, fontsize=11.5)
    ax.set_xlim(0, 116)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.set_ylim(-0.55, len(items)-0.4)
    ax.set_xlabel("近似法与严格 Point-in-Polygon 的一致率", fontsize=11, color="#3A4552")
    ax.set_title("近似空间关联误差显著：融合层已切换为严格 PIP + 多级回退",
                 fontsize=13, color="#25313D", pad=30, loc="left")
    ax.text(0, 1.025, "最终 S2 POI 9,893 条与源省份字段 100% 吻合：PIP 直接命中 9,886 + 城市名回退 7 + 最近中心兜底 0",
            transform=ax.transAxes, fontsize=10, color="#3A4552", va="bottom")
    style_ax(ax, xgrid=True, ygrid=False)
    save(fig, "pip_validation.png")

# ---------------------------------------------------------------- 9. LISA 象限分布
def chart_moran_lisa():
    fig, ax = plt.subplots(figsize=(7.8, 4.0))
    quad = ["低-低 LL", "高-低 HL", "低-高 LH", "高-高 HH"]
    vals = [146, 57, 52, 41]
    cols = ["#7A93A8", TEAL, "#9AA7B2", RED]
    y = np.arange(len(quad))
    bars = ax.barh(y, vals, height=0.58, color=cols)
    for yi, v in zip(y, vals):
        ax.text(v+2.5, yi, f"{v} 城", va="center", fontsize=12, color="#3A4552")
    ax.set_yticks(y); ax.set_yticklabels(quad, fontsize=12)
    ax.set_xlim(0, 168)
    ax.set_xlabel("城市数（296 个有效城市，KNN-4 邻接，未校正象限）", fontsize=11, color="#3A4552")
    ax.set_title("LISA 象限仅为探索层：BH-FDR 校正后显著城市为 0",
                 fontsize=13, color="#25313D", pad=12, loc="left")
    style_ax(ax, xgrid=True, ygrid=False)
    save(fig, "moran_lisa.png")

# ---------------------------------------------------------------- 10. 数据流水线
def chart_pipeline():
    fig, ax = plt.subplots(figsize=(11.2, 5.6))
    ax.set_xlim(0, 112); ax.set_ylim(0, 56); ax.axis("off")

    def box(x, y, w, h, text, fc, tc="white", fs=10.5, bold=False, ec="none", ls="-"):
        p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6,rounding_size=1.6",
                           fc=fc, ec=ec, lw=1.4, ls=ls)
        ax.add_patch(p)
        ax.text(x+w/2, y+h/2, text, ha="center", va="center", fontsize=fs,
                color=tc, fontweight="bold" if bold else "normal", linespacing=1.4)

    def arrow(x0, y0, x1, y1):
        a = FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=15,
                            color="#8FA5B5", lw=1.8)
        ax.add_patch(a)

    # 第一层：8 源（4×2 网格）
    src = ["S1 OSM路网\n1.5GB", "S2 百度POI\n1.4MB", "S3 环境数据\n13MB", "S4 ERA5气象\n1.6GB",
           "S5 健康服务\n74MB", "S6 经济指标\n11MB", "S7 人口数据\n39KB", "S8 区划边界\n4.6MB"]
    w, h = 13.4, 6.8
    xs = [2.5 + c*(w+1.4) for c in range(4)]
    for i, s in enumerate(src):
        r, c = divmod(i, 4)
        box(xs[c], 44-r*8.5, w, h, s, "#F2F6F9", "#25313D", 9.6, ec="#C9D6DF")
    # 汇流箭头
    arrow(31.3, 35.3, 31.3, 31.7)
    # 第二层
    box(18.5, 22, 25.5, 9.5, "清洗层 cleaning\n15 个清洗数据集\n坐标转换 · osmium 提速", TEAL, fs=10)
    box(56.5, 22, 25.5, 9.5, "融合层 integrating\n7 个融合数据集\n严格 PIP + 三维关联", PRIMARY, fs=10)
    box(87, 22, 23, 9.5, "质量保障（贯穿全流程）\n4 类规则 · 36 项检查\n清单 + MD5 校验", ORANGE, fs=9.6)
    arrow(44, 26.8, 56.5, 26.8)
    # 第三层
    qy, qh, qw = 5, 10, 29
    qxs = [4.5, 41.5, 78.5]
    qtext = ["Q1 环境 × 健康\n31 省 × 2 年 面板", "Q2 资源 × 可达性\n279 省×年 · 363 城快照", "Q3 公平性\n10 年 × 24 指标"]
    for (x, t), fx in zip(zip(qxs, qtext), (61, 69, 77)):
        box(x, qy, qw, qh, t, PRIMARY, fs=11.5, bold=True)
        arrow(fx, 22, x+qw/2, qy+qh+0.6)
    ax.text(56, 53.2, "多源数据流水线：8 源采集 → 清洗 → 跨源融合 → 三大研究问题",
            ha="center", fontsize=14, color="#25313D", fontweight="bold")
    save(fig, "pipeline.png")

if __name__ == "__main__":
    chart_data_sources()
    chart_pm25()
    chart_beds_trend()
    chart_accessibility()
    chart_equity_slope()
    chart_zone_gini()
    chart_kmeans()
    chart_pip_validation()
    chart_moran_lisa()
    chart_pipeline()
    print("ALL CHARTS DONE")
