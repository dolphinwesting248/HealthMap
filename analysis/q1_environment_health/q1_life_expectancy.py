import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf
from pathlib import Path
from scipy.stats import pearsonr, spearmanr
import geopandas as gpd

plt.rcParams["font.sans-serif"] = [
    "Microsoft YaHei",
    "SimHei",
    "Arial Unicode MS"
]
plt.rcParams["axes.unicode_minus"] = False

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

OUTPUT_DIR = (
    PROJECT_ROOT
    / "analysis"
    / "q1_environment_health"
)
OUTPUT_DIR.mkdir(exist_ok=True)

df = pd.read_csv(DATA_PATH)

print("\n================ 原始数据 ================")
print("总行数：", len(df))
print("地区数：", df["province"].nunique())

life_2020 = (
    df[df["year"] == 2020][
        [
            "province",
            "outcome_life_expectancy",
            "econ_income_total"
        ]
    ]
    .drop_duplicates(subset=["province"])
    .copy()
)

print("\n================ 2020 年健康与收入数据 ================")
print("原始地区数：", life_2020["province"].nunique())
print("\n缺失情况：")
print(
    life_2020[
        [
            "outcome_life_expectancy",
            "econ_income_total"
        ]
    ].isna().sum()
)

pm25_2023_2025 = (
    df[
        df["year"].isin([2023, 2024, 2025])
    ][
        [
            "province",
            "year",
            "air_pm25_mean"
        ]
    ]
    .dropna(subset=["air_pm25_mean"])
    .groupby("province", as_index=False)
    .agg(
        pm25_mean_2023_2025=(
            "air_pm25_mean",
            "mean"
        ),
        pm25_year_count=(
            "year",
            "nunique"
        )
    )
)

print("\n================ 2023–2025 PM2.5 三年平均 ================")
print("地区数：", pm25_2023_2025["province"].nunique())
print("\n各省实际参与计算的年份数：")
print(
    pm25_2023_2025[
        "pm25_year_count"
    ].value_counts().sort_index()
)

cross = life_2020.merge(
    pm25_2023_2025,
    on="province",
    how="inner"
)

print("\n================ 1.3 横截面 ================")
print("合并后地区数：", cross["province"].nunique())
print("\n缺失情况：")
print(
    cross[
        [
            "outcome_life_expectancy",
            "pm25_mean_2023_2025",
            "econ_income_total"
        ]
    ].isna().sum()
)

analysis_df = cross.dropna(
    subset=[
        "outcome_life_expectancy",
        "pm25_mean_2023_2025",
        "econ_income_total"
    ]
).copy()

analysis_df["income_10k"] = (
    analysis_df["econ_income_total"] / 10000
)

print("\n================ 最终分析样本 ================")
print("样本数：", len(analysis_df))
print("地区数：", analysis_df["province"].nunique())

print(
    analysis_df[
        [
            "province",
            "outcome_life_expectancy",
            "pm25_mean_2023_2025",
            "econ_income_total",
            "income_10k"
        ]
    ]
    .sort_values("outcome_life_expectancy")
    .to_string(index=False)
)

print("\n================ 描述统计 ================")

print(
    analysis_df[
        [
            "outcome_life_expectancy",
            "pm25_mean_2023_2025",
            "income_10k"
        ]
    ].describe()
)

pearson_r, pearson_p = pearsonr(
    analysis_df["pm25_mean_2023_2025"],
    analysis_df["outcome_life_expectancy"]
)

spearman_rho, spearman_p = spearmanr(
    analysis_df["pm25_mean_2023_2025"],
    analysis_df["outcome_life_expectancy"]
)

print("\n================ 相关分析 ================")

print(
    f"Pearson r = {pearson_r:.3f}, "
    f"p = {pearson_p:.4f}"
)

print(
    f"Spearman rho = {spearman_rho:.3f}, "
    f"p = {spearman_p:.4f}"
)

l1 = smf.ols(
    """
    outcome_life_expectancy
    ~ pm25_mean_2023_2025
    """,
    data=analysis_df
).fit(
    cov_type="HC3"
)

print("\n")
print("=" * 80)
print("L1：预期寿命 ~ PM2.5")
print("=" * 80)
print(l1.summary())

l2 = smf.ols(
    """
    outcome_life_expectancy
    ~ pm25_mean_2023_2025
    + income_10k
    """,
    data=analysis_df
).fit(
    cov_type="HC3"
)

print("\n")
print("=" * 80)
print("L2：预期寿命 ~ PM2.5 + 收入")
print("=" * 80)
print(l2.summary())

regression_results = pd.DataFrame(
    [
        {
            "model": "L1：仅 PM2.5",
            "pm25_coef":
                l1.params["pm25_mean_2023_2025"],
            "pm25_se":
                l1.bse["pm25_mean_2023_2025"],
            "pm25_p":
                l1.pvalues["pm25_mean_2023_2025"],
            "n":
                int(l1.nobs),
            "r_squared":
                l1.rsquared
        },
        {
            "model": "L2：PM2.5 + 收入",
            "pm25_coef":
                l2.params["pm25_mean_2023_2025"],
            "pm25_se":
                l2.bse["pm25_mean_2023_2025"],
            "pm25_p":
                l2.pvalues["pm25_mean_2023_2025"],
            "income_coef":
                l2.params["income_10k"],
            "income_p":
                l2.pvalues["income_10k"],
            "n":
                int(l2.nobs),
            "r_squared":
                l2.rsquared
        }
    ]
)

print("\n================ 回归结果汇总 ================")
print(regression_results.to_string(index=False))

regression_results.to_csv(
    OUTPUT_DIR
    / "q1_life_expectancy_regression_results.csv",
    index=False,
    encoding="utf-8-sig"
)

fig, ax = plt.subplots(figsize=(10, 7))

ax.scatter(
    analysis_df["pm25_mean_2023_2025"],
    analysis_df["outcome_life_expectancy"],
    s=85,
    alpha=0.85
)

slope, intercept = np.polyfit(
    analysis_df["pm25_mean_2023_2025"],
    analysis_df["outcome_life_expectancy"],
    1
)

x_line = np.linspace(
    analysis_df["pm25_mean_2023_2025"].min(),
    analysis_df["pm25_mean_2023_2025"].max(),
    100
)

y_line = slope * x_line + intercept

ax.plot(
    x_line,
    y_line,
    linestyle="--",
    linewidth=2
)

label_offsets = {
    "北京": (6, 4),
    "天津": (6, 6),
    "上海": (6, 6),
    "重庆": (6, 6),
    "河北": (6, -2),
    "河南": (6, -2),
    "湖北": (6, 6),
    "湖南": (6, -2),
    "江苏": (6, 6),
    "浙江": (6, 6),
    "广东": (6, 6),
    "山东": (6, 6),
    "山西": (6, 4),
    "陕西": (6, 4),
    "辽宁": (6, 4),
    "吉林": (-18, 6),
    "黑龙江": (6, -10),
    "内蒙古": (6, -10),
    "安徽": (6, 4),
    "福建": (6, 4),
    "江西": (6, -10),
    "四川": (6, 4),
    "贵州": (6, 4),
    "云南": (6, 4),
    "海南": (6, 4),
    "甘肃": (6, 4),
    "青海": (6, -10),
    "宁夏": (6, 4),
    "新疆": (6, 4),
    "西藏": (6, 4),
    "广西": (6, 4),
}

for _, row in analysis_df.iterrows():

    province = row["province"]

    dx, dy = label_offsets.get(
        province,
        (5, 5)
    )

    ax.annotate(
        province,
        (
            row["pm25_mean_2023_2025"],
            row["outcome_life_expectancy"]
        ),
        xytext=(dx, dy),
        textcoords="offset points",
        fontsize=9
    )

stats_text = (
    f"Pearson r = {pearson_r:.2f}\n"
    f"Spearman ρ = {spearman_rho:.2f}\n"
    f"n = {len(analysis_df)}"
)

ax.text(
    0.03,
    0.08,
    stats_text,
    transform=ax.transAxes,
    ha="left",
    va="bottom",
    fontsize=12,
    bbox=dict(
        boxstyle="round,pad=0.3",
        facecolor="white",
        alpha=0.8,
        edgecolor="lightgray"
    )
)

ax.set_xlabel(
    "2023–2025年 PM2.5 平均浓度（μg/m³）",
    fontsize=13
)

ax.set_ylabel(
    "2020年预期寿命（岁）",
    fontsize=13
)

ax.set_title(
    "省级 PM2.5 水平与预期寿命的空间关联",
    fontsize=17,
    pad=14
)

fig.text(
    0.02,
    0.02,
    "注：预期寿命为2020年数据，PM2.5为2023–2025年平均值。由于两类数据存在时间错位，"
    "本图仅反映省际空间关联，不代表因果关系。",
    fontsize=10
)

plt.tight_layout(
    rect=[0, 0.05, 1, 1]
)

plt.savefig(
    IMG_DIR / "q1_life_expectancy_pm25_scatter.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()

geo = gpd.read_file(GEO_PATH)

print("\n================ 地理边界 ================")
print(geo.columns)
print("全部地区数：", len(geo))

if "level" in geo.columns:
    geo = geo[
        geo["level"] == "province"
    ].copy()

def clean_province_name(name):

    if pd.isna(name):
        return name

    name = str(name).strip()

    replacements = [
        "壮族自治区",
        "回族自治区",
        "维吾尔自治区",
        "自治区",
        "特别行政区",
        "省",
        "市"
    ]

    for suffix in replacements:
        name = name.replace(suffix, "")

    return name.strip()

analysis_df["province_clean"] = (
    analysis_df["province"]
    .apply(clean_province_name)
)

geo["province_clean"] = (
    geo["name"]
    .apply(clean_province_name)
)

map_df = geo.merge(
    analysis_df,
    on="province_clean",
    how="left"
)

print("\n================ 地图匹配情况 ================")

matched = map_df[
    "outcome_life_expectancy"
].notna().sum()

print("成功匹配：", matched)

print("\n未匹配地区：")

print(
    map_df.loc[
        map_df[
            "outcome_life_expectancy"
        ].isna(),
        [
            "name",
            "province_clean"
        ]
    ].to_string(index=False)
)

fig, ax = plt.subplots(figsize=(10, 7))

map_df.plot(
    column="outcome_life_expectancy",
    cmap="YlGn",
    linewidth=0.8,
    edgecolor="white",
    legend=True,
    missing_kwds={
        "color": "#d9d9d9",
        "label": "无数据"
    },
    legend_kwds={
        "label": "预期寿命（岁）",
        "shrink": 0.72,
        "pad": 0.015,
        "fraction": 0.035,
        "aspect": 28
    },
    ax=ax
)

ax.set_title(
    "2020年省级预期寿命空间分布",
    fontsize=16,
    pad=12
)

ax.axis("off")

label_df = map_df.dropna(
    subset=["outcome_life_expectancy"]
).copy()

label_df["label_point"] = (
    label_df.geometry.representative_point()
)

map_label_offsets = {
    "北京": (0.5, 0.4),
    "天津": (0.5, -0.2),
    "上海": (0.5, 0.0),
    "江苏": (0.4, -0.3),
    "浙江": (0.5, -0.2),
    "宁夏": (0.2, 0.2),
    "重庆": (0.4, 0.0),
    "海南": (0.0, -0.5),
}

for _, row in label_df.iterrows():

    x = row["label_point"].x
    y = row["label_point"].y

    province_name = row["province_clean"]

    dx, dy = map_label_offsets.get(
        province_name,
        (0, 0)
    )

    ax.text(
        x + dx,
        y + dy,
        province_name,
        fontsize=7.5,
        ha="center",
        va="center",
        color="black"
    )

minx, miny, maxx, maxy = map_df.total_bounds

x_pad = (maxx - minx) * 0.03
y_pad = (maxy - miny) * 0.03

ax.set_xlim(
    minx - x_pad,
    maxx + x_pad
)

ax.set_ylim(
    miny - y_pad,
    maxy + y_pad
)

fig.text(
    0.25,
    0.2,
    "注：颜色越深表示预期寿命越高；灰色表示无可用数据。",
    fontsize=9
)

plt.subplots_adjust(
    left=0.02,
    right=0.91,
    top=0.92,
    bottom=0.07
)

plt.savefig(
    IMG_DIR / "q1_life_expectancy_map_2020.png",
    dpi=300,
    bbox_inches="tight",
    pad_inches=0.08
)

plt.show()

try:

    from libpysal.weights import Queen, KNN
    from esda.moran import Moran

    spatial_df = map_df.dropna(
        subset=[
            "outcome_life_expectancy",
            "pm25_mean_2023_2025",
            "income_10k"
        ]
    ).copy()

    spatial_df = spatial_df.reset_index(drop=True)

    queen_w = Queen.from_dataframe(
        spatial_df,
        use_index=True
    )
    queen_w.transform = "r"

    knn_w = KNN.from_dataframe(
        spatial_df,
        k=4
    )
    knn_w.transform = "r"

    spatial_reg = smf.ols(
        """
        outcome_life_expectancy
        ~ pm25_mean_2023_2025
        + income_10k
        """,
        data=spatial_df
    ).fit()

    spatial_df["regression_residual"] = spatial_reg.resid

    variables = {
        "2020年预期寿命":
            spatial_df["outcome_life_expectancy"].values,

        "2023–2025年PM2.5":
            spatial_df["pm25_mean_2023_2025"].values,

        "L2回归残差":
            spatial_df["regression_residual"].values
    }

    moran_results = []

    print("\n")
    print("=" * 80)
    print("Queen 邻接权重 Moran's I")
    print("=" * 80)

    for variable_name, values in variables.items():

        moran = Moran(
            values,
            queen_w
        )

        print(
            f"\n{variable_name}"
        )

        print(
            f"Moran's I = {moran.I:.4f}"
        )

        print(
            f"置换检验 p = {moran.p_sim:.4f}"
        )

        moran_results.append(
            {
                "weight": "Queen",
                "variable": variable_name,
                "moran_I": moran.I,
                "p_sim": moran.p_sim
            }
        )

    print("\n")
    print("=" * 80)
    print("KNN（k=4）空间权重 Moran's I")
    print("=" * 80)

    for variable_name, values in variables.items():

        moran = Moran(
            values,
            knn_w
        )

        print(
            f"\n{variable_name}"
        )

        print(
            f"Moran's I = {moran.I:.4f}"
        )

        print(
            f"置换检验 p = {moran.p_sim:.4f}"
        )

        moran_results.append(
            {
                "weight": "KNN_k4",
                "variable": variable_name,
                "moran_I": moran.I,
                "p_sim": moran.p_sim
            }
        )

    moran_results_df = pd.DataFrame(
        moran_results
    )

    moran_results_df.to_csv(
        OUTPUT_DIR
        / "q1_life_expectancy_moran_results.csv",
        index=False,
        encoding="utf-8-sig"
    )

    print("\n================ Moran's I 汇总 ================")
    print(
        moran_results_df.to_string(index=False)
    )

    print("\n空间统计结果已保存：")

    print(
        OUTPUT_DIR
        / "q1_life_expectancy_moran_results.csv"
    )

except ImportError:

    print("\n")
    print("=" * 80)
    print("尚未安装 Moran's I 所需套件。")
    print("=" * 80)

print("\n================ 1.3 完成 ================")

print("横截面数据：")
print(
    OUTPUT_DIR
    / "q1_life_expectancy_cross_section.csv"
)

print("\n回归结果：")
print(
    OUTPUT_DIR
    / "q1_life_expectancy_regression_results.csv"
)

print("\n主要图片：")
print(
    IMG_DIR
    / "q1_life_expectancy_pm25_scatter.png"
)

print(
    IMG_DIR
    / "q1_life_expectancy_map_2020.png"
)