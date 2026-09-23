"""
多源数据关联图 (数据血缘图) — 作业必交材料
绘制 S1-S8 数据源 → cleaned → integrated(q1/q2/q3) → 研究问题的完整血缘，
并标注每条边的跨源关联维度 (实体/时间/空间)。

输出: imgs/data_lineage.png (300 dpi) 与 imgs/data_lineage.svg
运行: python visualization/data_lineage.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = PROJECT_ROOT / "imgs"
OUT_DIR.mkdir(exist_ok=True)

# 中文字体 (系统已装 Noto Serif CJK)
plt.rcParams["font.sans-serif"] = ["Noto Serif CJK SC", "Noto Sans CJK SC", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# 颜色: 按层次区分
C_RAW = "#e8f0fe"      # 源数据
C_CLEAN = "#fff4e5"    # 清洗
C_INTG = "#e8f5e9"     # 融合
C_QUESTION = "#f3e5f5"  # 研究问题
C_EDGE = "#5f6368"
C_EDGE_INTEG = "#1a73e8"   # 融合层边高亮


def box(ax, x, y, w, h, title, lines, facecolor, edgecolor="#5f6368", title_size=10, body_size=8):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                linewidth=1.2, edgecolor=edgecolor, facecolor=facecolor, zorder=2))
    ax.text(x + w / 2, y + h - 0.16, title, ha="center", va="top",
            fontsize=title_size, fontweight="bold", zorder=3)
    for i, ln in enumerate(lines):
        ax.text(x + w / 2, y + h - 0.40 - i * 0.20, ln, ha="center", va="top",
                fontsize=body_size, color="#3c4043", zorder=3)


def arrow(ax, p1, p2, label=None, color=C_EDGE, style="-|>", lw=1.0, rad=0.0,
          label_dx=0.0, label_dy=0.0, ls="-"):
    a = FancyArrowPatch(p1, p2, arrowstyle=style, mutation_scale=11, linewidth=lw,
                        color=color, connectionstyle=f"arc3,rad={rad}", zorder=1,
                        linestyle=ls, shrinkA=1, shrinkB=1)
    ax.add_patch(a)
    if label:
        mx, my = (p1[0] + p2[0]) / 2 + label_dx, (p1[1] + p2[1]) / 2 + label_dy
        ax.text(mx, my, label, fontsize=7, color=color, ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.9), zorder=4)


def main():
    fig, ax = plt.subplots(figsize=(19, 11.5))
    ax.set_xlim(0, 19)
    ax.set_ylim(0, 11.5)
    ax.axis("off")

    # ---------- 第 1 层: 原始数据源 S1-S8 ----------
    ax.text(0.25, 11.15, "① 原始数据源 (raw)", fontsize=12, fontweight="bold", color="#202124")
    raw_boxes = [
        (0.25, 9.75, "S1 OSM 中国路网", ["1.5GB · ODbL", "2.6 亿节点"], C_RAW),
        (2.55, 9.75, "S2 百度医疗 POI", ["9,894 条", "BD-09 坐标"], C_RAW),
        (4.85, 9.75, "S3 环境 (Kaggle)", ["空气质量 40,424 行", "水质量 3,000 行"], C_RAW),
        (7.15, 9.75, "S4 ERA5 气象", ["1.6GB NetCDF", "147×141 格点×日"], C_RAW),
        (9.45, 9.75, "S5 卫生服务 (NBS+WHO)", ["12 领域 + 94 条", "省×年 2016-25"], C_RAW),
        (11.75, 9.75, "S6 社会经济 (NBS)", ["GDP/财政/价格", "就业/收入/年龄"], C_RAW),
        (14.05, 9.75, "S7 人口 (七普+WB)", ["31 省 + 774 行", "2020 / 1960-2025"], C_RAW),
        (16.35, 9.75, "S8 行政边界 (DataV)", ["32 GeoJSON", "省/市/区县"], C_RAW),
    ]
    for x, y, t, lines, c in raw_boxes:
        box(ax, x, y, 2.1, 1.05, t, lines, c, title_size=8.5, body_size=7.2)

    # ---------- 第 2 层: cleaned ----------
    ax.text(0.25, 8.85, "② 清洗后数据 (cleaned)   — 处理链: Raw → Cleaned", fontsize=12,
            fontweight="bold", color="#202124")
    clean_boxes = [
        (0.25, 7.55, "geo_road_poi.geojson", ["564,702 POI", "osmium 提取 15 类"], 2.25),
        (2.60, 7.55, "health_resource_poi.csv", ["9,893 行", "BD-09→WGS-84 修正"], 2.25),
        (4.95, 7.55, "env_air / env_water", ["33,976 / 3,000 行", "列标准化 + ffill"], 2.25),
        (7.30, 7.55, "env_weather_{y}.csv", ["~140 万行/年", "NetCDF→CSV 降采样"], 2.25),
        (9.65, 7.55, "health_service.csv", ["31,714 行", "12 领域 + WHO 合并"], 2.25),
        (12.00, 7.55, "econ_*.csv (6 个)", ["gdp/price/labor/income", "年龄/寿命"], 2.25),
        (14.35, 7.55, "pop_census / pop_wb", ["31 行 / 774 行", "省名标准化"], 2.25),
        (16.70, 7.55, "geo_boundary.geojson", ["484 features", "省34/市363/区86"], 2.05),
    ]
    for x, y, t, lines, w in clean_boxes:
        box(ax, x, y, w, 0.95, t, lines, C_CLEAN, title_size=8, body_size=7)

    # raw → cleaned 箭头
    for (rx, ry, _, _, _), (cx, cy, _, _, cw) in zip(raw_boxes, clean_boxes):
        arrow(ax, (rx + 1.05, ry), (cx + cw / 2, cy + 0.95), color="#bdc1c6", lw=0.9)

    # ---------- 第 3 层: integrated ----------
    ax.text(0.25, 6.85, "③ 跨源融合数据 (integrated)   — processing/integrating/", fontsize=12,
            fontweight="bold", color="#202124")
    intg_boxes = {
        # (x, y, w, h, title, lines)
        "q1_exp": (0.6, 5.15, 3.3, 1.15, "q1_env_exposure_province.csv",
                   ["102 省×年 × 35 列", "air×13 · water×17 · ERA5×4"]),
        "q1_out": (4.2, 5.15, 3.3, 1.15, "q1_health_outcome_province.csv",
                   ["279 省×年 × 22 列", "病死率/服务量/寿命/抚养比"]),
        "q1_panel": (2.4, 3.75, 3.3, 1.05, "q1_env_health_panel.csv",
                     ["319 × 58  环境×健康分析面板"]),
        "q2_res": (8.0, 5.15, 3.3, 1.15, "q2_medical_resource_province.csv",
                   ["279 省×年 × 28 列", "资源 + 每万人 + POI 密度"]),
        "q2_acc": (11.6, 5.15, 3.4, 1.15, "q2_healthcare_accessibility_city.csv",
                   ["363 城 × 13 列", "0.6° 路网窗口 Dijkstra"]),
        "q3_met": (8.0, 3.75, 3.3, 1.05, "q3_equity_metrics.csv",
                   ["10 年 × 25 列  基尼/泰尔分解"]),
        "q3_panel": (11.6, 3.75, 3.4, 1.05, "q3_equity_panel.csv",
                     ["319 × 100  全要素分析面板"]),
    }
    for key, (x, y, w, h, t, lines) in intg_boxes.items():
        box(ax, x, y, w, h, t, lines, C_INTG, edgecolor="#34a853", title_size=8.5, body_size=7.2)

    # ---------- 第 4 层: 研究问题 ----------
    ax.text(8.0, 3.05, "④ 分析 / 研究问题", fontsize=12, fontweight="bold", color="#202124")
    q_boxes = [
        (0.6, 1.35, 5.9, 1.5, "Q1 环境质量 ↔ 居民健康结局",
         ["跨源: S3 空气/水 + S4 气象 + S5 卫生 + S6 收入 (5 源)",
          "关联: 空间(省) × 时间(年) × 实体(省名)",
          "样本: 2023-24 空气×病死率 n=62; 2020 寿命横截面 n=31"]),
        (6.7, 1.35, 5.9, 1.5, "Q2 医疗资源 ↔ 可达性 ↔ 区域经济",
         ["跨源: S1 路网 + S2 POI + S5 卫生 + S6 经济 + S8 边界 (5 源)",
          "关联: 空间(0.6°窗口/省) + 实体 + 时间(2016-24)",
          "样本: 279 省×年; 363 城可达性"]),
        (12.8, 1.35, 5.9, 1.5, "Q3 医疗服务公平性 ↔ 环境·经济",
         ["跨源: S2/S5 资源 + S6 经济 + S3/S4 环境 + S7 人口 (5 源)",
          "关联: 实体(省→三大地带) + 时间(10 年) + 空间",
          "样本: 10 年公平性指标; 319 省×年全要素面板"]),
    ]
    for x, y, w, h, t, lines in q_boxes:
        box(ax, x, y, w, h, t, lines, C_QUESTION, edgecolor="#9334e6",
            title_size=9.5, body_size=7.5)

    # ---------- 融合层内部连线 ----------
    # q1 暴露 + q1 结局 → q1 panel
    arrow(ax, (2.25, 5.15), (3.6, 4.80), color=C_EDGE_INTEG, lw=1.4, rad=-0.15)
    arrow(ax, (5.85, 5.15), (4.5, 4.80), color=C_EDGE_INTEG, lw=1.4, rad=0.15)
    # q2 资源 → q3 metrics / panel
    arrow(ax, (9.65, 5.15), (9.65, 4.80), color=C_EDGE_INTEG, lw=1.4)
    arrow(ax, (11.3, 5.15), (13.0, 4.80), color=C_EDGE_INTEG, lw=1.4, rad=-0.12)
    # q1 panel → q3 panel
    arrow(ax, (5.7, 4.15), (11.6, 4.28), color=C_EDGE_INTEG, lw=1.4, rad=0.10,
          label="环境+结局+收入", label_dy=0.16)
    # q2 可达性 → q3 panel (省均聚合)
    arrow(ax, (13.3, 5.15), (13.3, 4.80), color=C_EDGE_INTEG, lw=1.4,
          label="省均+P90", label_dx=0.62)
    # q3 metrics/panel → Q3；q1 panel → Q1；q2 → Q2
    arrow(ax, (4.05, 3.75), (3.55, 2.85), color="#9334e6", lw=1.3)
    arrow(ax, (9.65, 3.75), (9.65, 2.85), color="#9334e6", lw=1.3)
    arrow(ax, (13.3, 3.75), (15.75, 2.85), color="#9334e6", lw=1.3)

    # ---------- 跨源关联维度标注 (图例) ----------
    ax.add_patch(FancyBboxPatch((0.6, 0.30), 18.1, 0.85,
                                boxstyle="round,pad=0.02,rounding_size=0.06",
                                linewidth=1.0, edgecolor="#dadce0", facecolor="#fafafa", zorder=2))
    ax.text(0.85, 0.90, "跨源关联维度:", fontsize=9.5, fontweight="bold", va="center")
    legend = [
        ("空间关联", "经纬度 → 省/市归属 (最近省中心 / 0.6° 路网窗口)；栅格格点→省；POI→省", "#1a73e8"),
        ("时间关联", "日→年聚合；省级 2016-2025 与 环境 2023-2025 对齐；CPI 序列累乘平减", "#ea8600"),
        ("实体关联", "省/市名称规范化 (英文 Anhui→安徽, 北京市→北京)；城市→省 (parent.adcode)", "#34a853"),
    ]
    for i, (name, desc, color) in enumerate(legend):
        y = 0.78 - i * 0.20
        ax.plot([1.35], [y], marker="s", markersize=7, color=color)
        ax.text(1.55, y, f"{name}：{desc}", fontsize=8, va="center", color="#3c4043")

    ax.text(9.5, 11.42, "多源数据关联图 — 城市环境、医疗资源与居民健康",
            ha="center", fontsize=15, fontweight="bold", color="#202124")

    fig.tight_layout()
    fig.savefig(OUT_DIR / "data_lineage.png", dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(OUT_DIR / "data_lineage.svg", bbox_inches="tight", facecolor="white")
    print(f"输出: {OUT_DIR/'data_lineage.png'} 与 .svg")


if __name__ == "__main__":
    main()
