import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
from pathlib import Path
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

# =========================
# 0. 中文显示
# =========================
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

# =========================
# 1. 项目路径
# =========================
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "integrated"
    / "q1_environment_health"
    / "q1_env_health_panel.csv"
)

GEO_PATH = (
    PROJECT_ROOT
    / "data"
    / "cleaned"
    / "geo_boundary.geojson"
)

IMG_DIR = PROJECT_ROOT / "imgs"
IMG_DIR.mkdir(exist_ok=True)

# =========================
# 2. 读取数据
# =========================
df = pd.read_csv(DATA_PATH)
geo = gpd.read_file(GEO_PATH)

# 只保留省级边界
geo = geo[geo["level"] == "province"].copy()

# =========================
# 3. 统一省名
# =========================
def clean_province_name(name):
    if pd.isna(name):
        return name

    name = str(name)

    suffixes = [
        "维吾尔自治区",
        "壮族自治区",
        "回族自治区",
        "特别行政区",
        "自治区",
        "省",
        "市"
    ]

    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
            break

    return name


df["province_clean"] = df["province"].apply(clean_province_name)
geo["province_clean"] = geo["name"].apply(clean_province_name)

# =========================
# 4. PM2.5 全国年度均值
# =========================
pm25 = df.dropna(subset=["air_pm25_mean"]).copy()

yearly_pm25 = (
    pm25.groupby("year", as_index=False)["air_pm25_mean"]
    .mean()
    .sort_values("year")
)

print("2023–2025 全国省均 PM2.5：")
print(yearly_pm25)

# 做成字典，后面标题直接调用
pm25_mean_dict = dict(zip(yearly_pm25["year"], yearly_pm25["air_pm25_mean"]))

# =========================
# 5. PM2.5 分级设置（统一三年）
# =========================
bins = [0, 25, 35, 45, 55, 100]
labels_asc = ["<25", "25–35", "35–45", "45–55", ">55"]
labels_desc = [">55", "45–55", "35–45", "25–35", "<25"]

# 红色系：高值深、低值浅
pm25_colors_desc = [
    "#7f0000",  # >55
    "#cb181d",  # 45–55
    "#fb6a4a",  # 35–45
    "#fcae91",  # 25–35
    "#fee5d9"   # <25
]

pm25_cmap = ListedColormap(pm25_colors_desc)
no_data_color = "#d9d9d9"

# =========================
# 6. 图1：三年 PM2.5 地图（不画折线）
# =========================
years = [2023, 2024, 2025]

fig, axes = plt.subplots(1, 3, figsize=(18, 7))

for i, year in enumerate(years):
    ax = axes[i]

    year_df = df[
        (df["year"] == year)
        & (df["air_pm25_mean"].notna())
    ][["province_clean", "air_pm25_mean"]].copy()

    year_df["pm25_group"] = pd.cut(
        year_df["air_pm25_mean"],
        bins=bins,
        labels=labels_asc,
        include_lowest=True
    )

    year_df["pm25_group"] = year_df["pm25_group"].cat.reorder_categories(
        labels_desc,
        ordered=True
    )

    map_data = geo.merge(
        year_df,
        on="province_clean",
        how="left"
    )

    map_data.plot(
        column="pm25_group",
        ax=ax,
        categorical=True,
        legend=False,
        cmap=pm25_cmap,
        edgecolor="black",
        linewidth=0.7,
        missing_kwds={
            "color": no_data_color,
            "edgecolor": "black",
            "label": "No data"
        }
    )

    mean_value = pm25_mean_dict.get(year, None)
    if mean_value is not None:
        ax.set_title(
            f"{year}\n均值 = {mean_value:.1f} µg/m³",
            fontsize=16,
            pad=12
        )
    else:
        ax.set_title(
            f"{year}",
            fontsize=16,
            pad=12
        )

    ax.axis("off")

fig.suptitle("31省 PM2.5 时空分布（2023–2025）", fontsize=22, y=0.96)

legend_handles = [
    Patch(facecolor=color, edgecolor="black", label=label)
    for color, label in zip(pm25_colors_desc, labels_desc)
]
legend_handles.append(
    Patch(facecolor=no_data_color, edgecolor="black", label="No data")
)

fig.legend(
    handles=legend_handles,
    title="PM2.5 (µg/m³)",
    loc="lower center",
    bbox_to_anchor=(0.5, 0.02),
    ncol=6,
    frameon=True,
    fontsize=12,
    title_fontsize=13
)

plt.tight_layout(rect=[0, 0.08, 1, 0.92])

plt.savefig(
    IMG_DIR / "q1_pm25_overview.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()   # 先关掉第一张图，避免挡住水图

# =========================
# 7. 图2：水质 tile 图
# =========================
water_cols = ["water_wqi_mean", "water_polluted_frac"]

# 只保留至少有一个水指标不为空的记录
water_df = df[
    df[water_cols].notna().any(axis=1)
][["province_clean", "water_wqi_mean", "water_polluted_frac"]].copy()

# 如果为空，直接提示
if water_df.empty:
    print("\n没有可用的水质数据，water_df 为空。")
else:
    # 不做面板：按省聚合（取平均）
    water_summary = (
        water_df.groupby("province_clean", as_index=False)[water_cols]
        .mean()
        .sort_values("province_clean")
    )

    print("\n水质可用省份：")
    print(water_summary)

    provinces = water_summary["province_clean"].tolist()
    n = len(provinces)

    fig2, axes2 = plt.subplots(
        2, 1,
        figsize=(max(12, n * 1.2), 6.2),
        gridspec_kw={"height_ratios": [1, 1]}
    )

    # ---------- 上：water_wqi_mean ----------
    arr1 = water_summary["water_wqi_mean"].values.reshape(1, -1)

    im1 = axes2[0].imshow(
        arr1,
        aspect="auto",
        cmap="Blues"
    )

    axes2[0].set_title("各省平均水质指数", fontsize=14, pad=10)
    axes2[0].set_yticks([0])
    axes2[0].set_yticklabels(["WQI"])
    axes2[0].set_xticks(range(n))
    axes2[0].set_xticklabels(provinces, rotation=45, ha="right")

    for j, val in enumerate(arr1[0]):
        axes2[0].text(
            j, 0,
            f"{val:.2f}",
            ha="center",
            va="center",
            fontsize=9,
            color="black"
        )

    cbar1 = fig2.colorbar(im1, ax=axes2[0], fraction=0.03, pad=0.02)
    cbar1.set_label("WQI")

    # ---------- 下：water_polluted_frac ----------
    arr2 = water_summary["water_polluted_frac"].values.reshape(1, -1)

    im2 = axes2[1].imshow(
        arr2,
        aspect="auto",
        cmap="OrRd"
    )

    axes2[1].set_title("各省污染水体比例", fontsize=14, pad=10)
    axes2[1].set_yticks([0])
    axes2[1].set_yticklabels(["Polluted frac"])
    axes2[1].set_xticks(range(n))
    axes2[1].set_xticklabels(provinces, rotation=45, ha="right")

    for j, val in enumerate(arr2[0]):
        axes2[1].text(
            j, 0,
            f"{val:.2f}",
            ha="center",
            va="center",
            fontsize=9,
            color="black"
        )

    cbar2 = fig2.colorbar(im2, ax=axes2[1], fraction=0.03, pad=0.02)
    cbar2.set_label("Polluted fraction")

    fig2.suptitle("水环境质量省际比较", fontsize=18, y=0.98)

    plt.tight_layout(rect=[0, 0, 1, 0.95])

    plt.savefig(
        IMG_DIR / "q1_water_tiles.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.show()