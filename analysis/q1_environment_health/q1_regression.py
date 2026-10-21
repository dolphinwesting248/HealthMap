import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf
from pathlib import Path

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
print("年份：", sorted(df["year"].dropna().unique()))


main_cols = [
    "province",
    "year",
    "air_pm25_mean",
    "weather_t2m_mean",
    "outcome_er_mortality_rate",
    "outcome_old_dependency_ratio",
    "econ_income_total"
]

panel_raw = (
    df[df["year"].isin([2023, 2024])][main_cols]
    .copy()
)

print("\n================ 2023–2024 原始面板 ================")
print("行数：", len(panel_raw))
print("地区数：", panel_raw["province"].nunique())

print("\n缺失情况：")
print(panel_raw.isna().sum())

panel = panel_raw.dropna(
    subset=[
        "air_pm25_mean",
        "weather_t2m_mean",
        "outcome_er_mortality_rate",
        "outcome_old_dependency_ratio",
        "econ_income_total"
    ]
).copy()

print("\n================ 主回归完整样本 ================")
print("样本数：", len(panel))
print("地区数：", panel["province"].nunique())
print("年份：", sorted(panel["year"].unique()))

print(
    panel[
        [
            "air_pm25_mean",
            "weather_t2m_mean",
            "outcome_er_mortality_rate",
            "outcome_old_dependency_ratio",
            "econ_income_total"
        ]
    ].describe()
)

panel["temp_c"] = panel["weather_t2m_mean"] - 273.15
panel_raw["temp_c"] = panel_raw["weather_t2m_mean"] - 273.15

corr_pm25_df = panel_raw.dropna(
    subset=["air_pm25_mean", "outcome_er_mortality_rate"]
).copy()

corr_temp_df = panel_raw.dropna(
    subset=["weather_t2m_mean", "outcome_er_mortality_rate"]
).copy()

corr_pm25 = (
    corr_pm25_df[
        [
            "air_pm25_mean",
            "outcome_er_mortality_rate"
        ]
    ]
    .corr(method="pearson")
    .iloc[0, 1]
)

corr_temp = (
    corr_temp_df[
        [
            "weather_t2m_mean",
            "outcome_er_mortality_rate"
        ]
    ]
    .corr(method="pearson")
    .iloc[0, 1]
)

print("\n================ Pearson 相关 ================")
print(f"PM2.5 与急诊病死率：r = {corr_pm25:.3f}, n = {len(corr_pm25_df)}")
print(f"气温与急诊病死率：r = {corr_temp:.3f}, n = {len(corr_temp_df)}")

plot1 = panel_raw.dropna(
    subset=[
        "air_pm25_mean",
        "outcome_er_mortality_rate"
    ]
).copy()

fig, ax = plt.subplots(figsize=(9, 6))

year_styles = {
    2023: {"marker": "o"},
    2024: {"marker": "o"}
}

for year in [2023, 2024]:

    d = plot1[plot1["year"] == year]

    ax.scatter(
        d["air_pm25_mean"],
        d["outcome_er_mortality_rate"],
        s=55,
        alpha=0.75,
        marker=year_styles[year]["marker"],
        label=str(year)
    )

    if len(d) >= 2:
        slope, intercept = np.polyfit(
            d["air_pm25_mean"],
            d["outcome_er_mortality_rate"],
            1
        )

        x_line = np.linspace(
            d["air_pm25_mean"].min(),
            d["air_pm25_mean"].max(),
            100
        )

        y_line = slope * x_line + intercept

        ax.plot(
            x_line,
            y_line,
            linestyle="--",
            alpha=0.8
        )

ax.axhline(
    y=plot1["outcome_er_mortality_rate"].mean(),
    linestyle=":",
    linewidth=1,
    alpha=0.5
)

ax.set_xlabel("PM2.5 年平均浓度（μg/m³）")
ax.set_ylabel("急诊病死率")
ax.set_title("2023–2024年 PM2.5 与急诊病死率的省际关系")
ax.legend(title="年份")

fig.text(
    0.02,
    0.02,
    "注：散点表示省级观测；虚线为各年份线性拟合，仅用于描述同期省际关联，不代表因果关系。",
    fontsize=9
)

plt.tight_layout(rect=[0, 0.06, 1, 1])

plt.savefig(
    IMG_DIR / "q1_pm25_er_mortality_by_year.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()

plot2 = panel_raw.dropna(
    subset=[
        "temp_c",
        "outcome_er_mortality_rate"
    ]
).copy()

fig, ax = plt.subplots(figsize=(8, 6))

ax.scatter(
    plot2["temp_c"],
    plot2["outcome_er_mortality_rate"],
    s=55,
    alpha=0.75
)

if len(plot2) >= 2:
    slope, intercept = np.polyfit(
        plot2["temp_c"],
        plot2["outcome_er_mortality_rate"],
        1
    )

    x_line = np.linspace(
        plot2["temp_c"].min(),
        plot2["temp_c"].max(),
        100
    )

    y_line = slope * x_line + intercept

    ax.plot(
        x_line,
        y_line,
        linestyle="--"
    )

temp_corr_plot = (
    plot2[
        [
            "temp_c",
            "outcome_er_mortality_rate"
        ]
    ]
    .corr()
    .iloc[0, 1]
)

ax.text(
    0.03,
    0.95,
    f"Pearson r = {temp_corr_plot:.2f}",
    transform=ax.transAxes,
    ha="left",
    va="top",
    fontsize=10
)

ax.set_xlabel("年平均气温（℃）")
ax.set_ylabel("急诊病死率")
ax.set_title("省级气温与急诊病死率的同期关系")

fig.text(
    0.02,
    0.02,
    "注：本图用于观察气象条件与急诊病死率的同期统计关系，不代表因果效应。",
    fontsize=9
)

plt.tight_layout(rect=[0, 0.06, 1, 1])

plt.savefig(
    IMG_DIR / "q1_temperature_er_mortality.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()

joint_df = df[df["year"] == 2023][
    [
        "province",
        "air_pm25_mean",
        "weather_t2m_mean",
        "outcome_er_mortality_rate"
    ]
].dropna().copy()

joint_df["temp_c"] = (
    joint_df["weather_t2m_mean"] - 273.15
)

print("\n================ 2023 联合分布样本 ================")
print("样本数：", len(joint_df))
print("地区数：", joint_df["province"].nunique())


fig, ax = plt.subplots(figsize=(9, 6.5))

sc = ax.scatter(
    joint_df["air_pm25_mean"],
    joint_df["temp_c"],
    c=joint_df["outcome_er_mortality_rate"],
    cmap="Reds",
    s=85,
    alpha=0.9,
    vmin=joint_df["outcome_er_mortality_rate"].min(),
    vmax=joint_df["outcome_er_mortality_rate"].max()
)

label_offsets = {
    "内蒙古": (-18, 6),
    "吉林": (6, -10)
}

for _, row in joint_df.iterrows():

    dx, dy = label_offsets.get(
        row["province"],
        (3, 3)
    )

    ax.annotate(
        row["province"],
        (
            row["air_pm25_mean"],
            row["temp_c"]
        ),
        xytext=(dx, dy),
        textcoords="offset points",
        fontsize=8
    )

cbar = plt.colorbar(sc, ax=ax)
cbar.set_label("急诊病死率")

ax.set_xlabel("PM2.5 年平均浓度（μg/m³）")
ax.set_ylabel("年平均气温（℃）")
ax.set_title("2023年省级 PM2.5、气温与急诊病死率的联合分布")

fig.text(
    0.02,
    0.02,
    "注：横轴为空气污染水平，纵轴为气温，颜色越深表示急诊病死率越高。",
    fontsize=9
)

plt.tight_layout(rect=[0, 0.06, 1, 1])

plt.savefig(
    IMG_DIR / "q1_pm25_temp_er_joint_2023.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()

m1 = smf.ols(
    """
    outcome_er_mortality_rate
    ~ air_pm25_mean
    """,
    data=panel
).fit(cov_type="HC3")

m2 = smf.ols(
    """
    outcome_er_mortality_rate
    ~ air_pm25_mean
    + weather_t2m_mean
    """,
    data=panel
).fit(cov_type="HC3")

m3 = smf.ols(
    """
    outcome_er_mortality_rate
    ~ air_pm25_mean
    + weather_t2m_mean
    + outcome_old_dependency_ratio
    """,
    data=panel
).fit(cov_type="HC3")


m4 = smf.ols(
    """
    outcome_er_mortality_rate
    ~ air_pm25_mean
    + weather_t2m_mean
    + outcome_old_dependency_ratio
    + econ_income_total
    """,
    data=panel
).fit(cov_type="HC3")


m5 = smf.ols(
    """
    outcome_er_mortality_rate
    ~ air_pm25_mean
    + weather_t2m_mean
    + outcome_old_dependency_ratio
    + econ_income_total
    + C(province)
    + C(year)
    """,
    data=panel
).fit(
    cov_type="cluster",
    cov_kwds={
        "groups": panel["province"]
    }
)

models = {
    "M1 仅PM2.5": m1,
    "M2 +气温": m2,
    "M3 +老年抚养比": m3,
    "M4 +收入": m4,
    "M5 +省/年份固定效应": m5
}

for name, model in models.items():

    print("\n")
    print("=" * 80)
    print(name)
    print("=" * 80)
    print(model.summary())


coef_rows = []

for name, model in models.items():

    coef = model.params["air_pm25_mean"]
    se = model.bse["air_pm25_mean"]
    p = model.pvalues["air_pm25_mean"]

    ci_low = coef - 1.96 * se
    ci_high = coef + 1.96 * se

    coef_rows.append(
        {
            "model": name,
            "coef": coef,
            "se": se,
            "ci_low": ci_low,
            "ci_high": ci_high,
            "p_value": p,
            "n": int(model.nobs),
            "r_squared": model.rsquared
        }
    )

coef_df = pd.DataFrame(coef_rows)

print("\n================ PM2.5 系数汇总 ================")
print(coef_df.to_string(index=False))


coef_df.to_csv(
    OUTPUT_DIR / "q1_pm25_model_coefficients.csv",
    index=False,
    encoding="utf-8-sig"
)

plot_coef = coef_df.copy()

plot_coef["label"] = [
    "M1：仅 PM2.5",
    "M2：PM2.5 + 气温",
    "M3：+ 老年抚养比",
    "M4：+ 收入",
    "M5：+ 省固定效应、年份固定效应"
]

plot_coef = plot_coef.iloc[::-1].reset_index(drop=True)

fig, ax = plt.subplots(figsize=(9, 6))

y_pos = np.arange(len(plot_coef))

xerr = np.vstack([
    plot_coef["coef"] - plot_coef["ci_low"],
    plot_coef["ci_high"] - plot_coef["coef"]
])

ax.errorbar(
    plot_coef["coef"],
    y_pos,
    xerr=xerr,
    fmt="o",
    capsize=4
)

ax.axvline(
    x=0,
    linestyle="--",
    linewidth=1
)

ax.set_yticks(y_pos)
ax.set_yticklabels(plot_coef["label"])

ax.set_xlabel("PM2.5 回归系数")
ax.set_title(
    "不同模型设定下 PM2.5 与急诊病死率的回归系数"
)

fig.text(
    0.02,
    0.02,
    "注：点表示回归系数估计值，横线表示95%置信区间；"
    "M5采用省固定效应、年份固定效应及省级聚类标准误。",
    fontsize=9
)

plt.tight_layout(rect=[0, 0.07, 1, 1])

plt.savefig(
    IMG_DIR / "q1_pm25_coefficient_plot.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()

interaction_panel = panel.copy()

# 中心化，减少主效应解释困难
interaction_panel["pm25_centered"] = (
    interaction_panel["air_pm25_mean"]
    - interaction_panel["air_pm25_mean"].mean()
)

interaction_panel["olddep_centered"] = (
    interaction_panel["outcome_old_dependency_ratio"]
    - interaction_panel["outcome_old_dependency_ratio"].mean()
)

interaction_model = smf.ols(
    """
    outcome_er_mortality_rate
    ~ pm25_centered
    * olddep_centered
    + weather_t2m_mean
    + econ_income_total
    + C(province)
    + C(year)
    """,
    data=interaction_panel
).fit(
    cov_type="cluster",
    cov_kwds={
        "groups": interaction_panel["province"]
    }
)

print("\n")
print("=" * 80)
print("探索性交互模型：PM2.5 × 老年抚养比")
print("=" * 80)
print(interaction_model.summary())

interaction_term = (
    "pm25_centered:olddep_centered"
)

print("\n交互项结果：")
print(
    "coef =",
    interaction_model.params.get(
        interaction_term,
        np.nan
    )
)

print(
    "p =",
    interaction_model.pvalues.get(
        interaction_term,
        np.nan
    )
)
panel.to_csv(
    OUTPUT_DIR / "q1_main_panel_2023_2024.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\n================ 完成 ================")

print("已保存：")
print(
    OUTPUT_DIR
    / "q1_main_panel_2023_2024.csv"
)

print(
    OUTPUT_DIR
    / "q1_pm25_model_coefficients.csv"
)

print("\n图片已保存至：")
print(IMG_DIR)