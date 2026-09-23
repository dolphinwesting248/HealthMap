# 数据分析工作指南 (analysis.md)

> 项目：城市环境、医疗资源与居民健康 — 多源数据融合分析
> 输入：`data/integrated/`（三问面板与指标，详见 [integrated_data.md](integrated_data.md)）
> 输出目录约定：分析代码放 `analysis/`，图表放 `visualization/`，两者配套。

---

## 0. 数据可用性速查（先看这个再选题）

| 分析需求 | 可用样本 | 状态 |
|---------|---------|------|
| PM2.5 × 病死率/年龄结构（2023–24） | 31 省 × 2 年 = **62** | ✅ 面板回归就绪 |
| 2020 寿命 × 环境空间横截面 | **31 省** | ✅ 可做，需注明时间错位（env 2023–25）|
| 医疗资源 × 经济（省×年）| 31 × 9 年 = **279** | ✅ 数据最充裕 |
| 城市 × 就医可达性 | **363 城**（295 城有医院）| ✅ 横截面可做时序不能 |
| 卫生公平性年度趋势 | **10 年** × 24 指标 | ✅ 直接出趋势图/结论 |
| 水质量 | 仅 **10 省**（2023 单年）| ⚠️ 只做区域性分析，别做面板 |
| 预期寿命 | 仅 **2020 单年** | ⚠️ 只能空间横截面 |

**硬限制**（来自数据源，分析时诚实标注即可）：
- env 类列只覆盖 2023–2025；`gini_air` 无 2016–2022
- `outcome_life_expectancy` 只有 2020；2025 年指标多未发布（NA）
- 可达性是单点快照

---

## 一、Q1：城市环境质量与居民健康结局的空间关联

### 1.1 描述性（先做，看清分布再回归）

- `air_pm25_mean` 年均值起点（2023=40.3, 2024=39.3, 2025=44.7 µg/m³）画 31 省地图——西部明显低，京津冀/晋豫明显高，地理叙事自然成立
- 水只覆盖 10 省：用 `water_wqi_mean`/`water_polluted_frac` 做省份 tile，不做面板

### 1.2 主回归（Q2 分析框架已定）

面板子集（`years ∈ {2023, 2024}`，n=62，31 省 × 2 年）：

```
outcome_er_mortality_rate  ~ air_pm25_mean + outcome_old_dependency_ratio
                             + weather_t2m_mean + econ_income_total + 省 FE + 年 FE
```

- 变量在 `q1_env_health_panel.csv` 全部就位
- 参考：粗相关 r(PM2.5, 病死率) ≈ **+0.21**（n=62），方向合理但弱——预期加控制后变化
- 交互项：`air_pm25_mean × outcome_old_dependency_ratio`（老年暴露放大效应）是故事亮点
- 各结局列的名字及样本数见 integrated_data.md 中 outcome/outsvc 两组列

### 1.3 寿命（2020）空间横截面

`outcome_life_expectancy` 只在 2020 有（n=31）：

```
outcome_life_expectancy(2020) ~ air_pm25_mean(2023-25 均值) + econ_income_total(2020)
```
- 明示局限：env 与寿命有 3 年时差，只能作"空间关联"证据（不是因果时序）
- 建议同时报 Pearson/Spearman、Moran's I 空间自相关检验

### 1.3 备选/扩展

- 用 `weather_t2m_mean`、`weather_d2m_mean` 作温度/湿度对照（ERA5 是 2023-2025）
- 水暴露：只搭配 Q1 的 10 省做小样本横截面

---

## 二、Q2：医疗资源、可达性与区域经济

### 2.1 资源 vs 经济的省面板（数据最厚，主力面板）

n=279 省×年 (2016–2024)：

```
per10k_beds_calc ~ log(econ_income_total) + econ_income_urban/rural 差 (城乡差距)
                   + 年 FE + 省 FE
```

或反向：`log(econ_income) ~ per10k_beds_all`（资源对发展的边际贡献）
`acc_nearest_km_mean` 等可达性省均值与 `per10k_beds_*` 的相关矩阵——资源密度高≠可达性高是常常被说道的点

### 2.2 城市级可达性分析（363 城，单点横截面）

- 描述统计：`nearest_hospital_min` median=35.3 分钟, IQR 21–55 分钟，极端值 1461 分钟（西部自治州）
- **313/363 城 “大医院 30 分钟不可达”** —— 基层医疗可及性叙事的核心数字
- 可达性与经纬度地图可视化（可用 q3_equity_panel 中 `acc_*` 列）
- `major_nearest_km` vs `econ_income`（省均）回归 → 富裕省份大医院可达性更高的量化证据

### 2.3 老龄化压力（Q2/Q3 交叠）

- `beds_per_10k_elderly`列：2016–2019, 2021–2024（pop_age 中空 2020/2025）
- 看省 × 年推移 → 东北三省老龄化配给是否更紧张

---

## 三、Q3：公平性（已有指标数据的直接结论与深挖方向）

### 3.1 年度公平性趋势（q3_equity_metrics，已可直接引用）

现成结论可用：
- `gini_real_income` 0.191 → 0.168（2016→2025），**缓慢改善**
- `income_p90_p10` 2.04 → 1.79，**尾部收敛**
- `theil_between_share` 55.9% → 51.9%，**东区/中部/西部之间的结构差距是主要不平等源**
- `gini_per10k_beds_all` 稳定 ~0.075（床位分布稳态公平）

预期可视化：4 个子图的年度趋势线 + 泰尔分解的高分位（within/between 堆叠柱）

### 3.2 医疗资源公平性横截面

- `gini_per10k_beds/doctors/nurses` 年际变化小 → 加资源明细（省三级 gini 已在 metrics 表）
- 深入：分解到城市级——363 城的 hospital_count_window 用 Moran's I / 洛伦兹曲线
- 环境（`gini_air_pm25`）在 2023-24 有值 → 比较收入公平性 vs 环境公平性谁收敛快

### 3.3 面板回归（公平性驱动因素）

用 `q3_equity_panel.csv`（319 × 100 列全要素底表）:

```
outcome_er_mortality  ~ econ_income_total + acc_nearest_km_p90 + air_pm25_mean
                        + per10k_beds_all + ctrl_healthcare_employment_wan + 省/年 FE
```

- Key: 用 `acc_nearest_km_p90`（尾部不平等）不能只 mean——P90 体现分布尾
- 检验“环境×经济×可达性”三者对结局的边际影响（分解 Q3 的"环境与经济因素"命题）
- `wb_*` 列 national 级别（同省同值），只能做时序控制或生成趋势图（勿与省变量直接回归）

---

## 四、通用注意事项

1. **省名键**：panel 的 `province` 是 31 省标准短名（“北京”非“北京市”，来自 normalize_province）；外部表若用全名/英文名，先用 `processing/cleaning/utils.normalize_province`
2. **NA 语义**：cleaned/integrated 的 NA 保留策略见 cleaned_data.md / integrated_data.md 的两个缺失值表——2025 空是“未发布”不是测量缺失
3. **不加权/加权的口径**：`q3_equity_metrics` 里的 gini/theil 是省等权；需要人口加权时 `q3_equity_panel` 有 `pop_2020_wan`/`outcome_age_pop_n` 作 wp
4. **可达性字段是 single-snapshot**：363 城的 method=network 占 362；对其做时序面板是大忌
5. **路径**：analysis 脚本读 `data/integrated/**`，输出图到 `visualization/`，数据生成有问题回 `processing/integrating/` 改

---

## 五、建议的产出物清单（可视化/报告直接可用）

| 主题 | 数据 | 建议图型 |
|---|---|---|
| PM2.5 空间分布 (2023-25) | q1_panel | 省界 choropleth（geo_boundary + matplotlib/plotly）|
| 空气 × 病死率 散点+分期 | q1_env_health_panel | 散点 + 回归线, 按年分色 |
| 31 省可达性 | q2_accessibility | 省界/城点 marker 地图 + 30 分钟等时圈城市列表 |
| 资源-经济 散点 图 | q2_medical_resource | 散点（x=econ_income_total, y=per10k_beds_all）且回归线 |
| 泰尔/基尼趋势 | q3_metrics | 折线（three-axis: theil between/within, gini, p90p10）|
| 地地带堆叠贡献 | q3_metrics | 堆叠柱 (between vs within share by year) |
| 老龄化压力图 | q2_medical_resource | bar: beds_per_10k_elderly by year (二三线省份对比) |

---

## 六、进阶方法清单（可选，样本要求在速查内）

以下方法在本仓库环境 (statsmodels/scipy/sklearn/esda/libpysal) **已装齐并试探性跑通**，每项都给出"适用场景 + 参考输出"：

### 6.1 面板回归升级类

**TWFE (双向固定效应) + 聚类标准误** — Q1/Q2/Q3 主回归的规范版
- 代码骨架（已试跑）:
```python
import statsmodels.api as sm
X = pd.concat([d[["air_pm25_mean","ln_inc"]],
               pd.get_dummies(d["province"], prefix="prov", drop_first=True).astype(float),
               pd.get_dummies(d["year"], prefix="yr", drop_first=True).astype(float)], axis=1)
m = sm.OLS(y, sm.add_constant(X)).fit(cov_type="cluster", cov_kwds={"groups": d["province"]})
```
- 探索结果: PM2.5→急诊病死率 TWFE coef = −0.0008 (p=0.27, n=62)。初值显示加省年度 FE 后粗相关消失——这正是高级方法的价值：粗相关（r=+0.21）会被内生变化解释，需解释异质性和控制
- 变体: `practice = linearmodels.PanelOLS` 可再装（若做严格 panel FE，explainable 加 entity/time id）

**分位数回归 statsmodels quantreg** — Q1 的不均等效应
- 探索结果: 病死率 P25/P50/P75 处 PM2.5 效应均 +0.0006~+0.0007, q=P25 边缘显著 (p=0.084)，中位以上发散——佐证"环境对健康分布上部的影响不确定"，比 OLS 单系数有消息量

### 6.2 空间分析类

**Moran's I (全局) + LISA (局部) @ esda/libpysal** — Q1/Q2 空间组织
- 探索结果: 城市 296 个可达性 (KNN-4): nearest_hospital_min Moran I=0.001, p=0.36 (无显著空间自相关——市域可达性近独立)
- 但 **PM2.5 的 31 省 strongly clustered (2024)**: LISA 显著聚集: 天津/河北/北京 HH（京津冀高-高），内蒙古/山西 LH (低-高边界)； 新疆 HL。空间插值或 cluster mapping 都是可视化高价值项
- 建议: `esda.Moran_Local` 生成 LISA cluster map，与省界 choropleth 叠作双面板图

**省际空间 Durbin / Spatial Lag (SDM/SAR)** — Q3 更深指标
- 需要 libpysal权和 queen contiguity (由 geo_boundary polygon 直接导出), spreg 库 (额外安装)
- 如果你想要空间外溢回归 (PM25 邻省流动)，可在 Q1 故事里补一节

### 6.3 事件 / 因果推断类

**Interrupted / DiD (2020 COVID 冲击)** — 在 health_service 病死率 2018–2022 范围
- 探索: `~ post + ln_inc + C(province) + C(year)` → post coef = **+0.056 (p=0.006)**: 2020 之后急诊病死率系统性抬升（可解释为 COVID 影响），带统计证据
- 扩展: quarterly 数据不可得, 但可做 `outcome_obs_mortality` 类比、C-country difference-in-differences

### 6.4 降维/分类聚类

**KMeans / 层次聚类** (sklearn) — 对 31 省 × (资源密度, 老龄化压力, 可达性, 收入) 四维 2024 横截面分层
- 探索结果 (k=3, 2024):
  - cluster 2 (粤/苏/浙/闽): 收入均值 55k, 可达 31km, 资源偏稳 — "高收入高可达"
  - cluster 1 (新疆/藏/蒙/黔/青/琼): 收入 31k, 可达 78km — **"边远低可达"** 群
  - cluster 0 (其余大部分): 中间形
- 这是报告里一幅很重要的 vec 图（Province stratification map）

### 6.5 时间序列趋势检验

**Kendall τ / Mann-Kendall** — q3 指标的单调性检验 (Scipy kendalltau)
- 探索: gini_income τ=−1.0 (p<0.01, 严格单调下降), income_p90_p10 τ=−0.96, theil_between_share τ=−1.0
- **gini_per10k_beds_all τ=NaN** 致病: 该指标 2025 全空 (口径断裂)。绘制时须 skipna
- 洞见: 所有公平性指标 2016→2025 年间严格单调改善（不含床位分）— Mann-Kendall 叙事非常干净

### 6.6 不平等的可分解性 (泰尔前后)

规范 Theil 分解已在 q3_equity_metrics 里: `T_between + T_within = T` 恒等式 machine-precision 成立。
进一步可做: 按 **收入十等分组的 within 分解**（借 q3_panel econ_income_urban/rural 城乡差异作 subgroup），或者做 Lorenz 曲线 + 地带集中指数 (Concentration Index)

### 6.7 城市级可达性的不平等度量（每人公平性）

- 城市级医类分布 gini = *0.679*；东部 0.574 / 中部 0.664 / 西部 **0.727**（医院数分布的地带梯度成立, 西部最不均衡）
- 报告可绘 Lorenz curve + tri-zone gini 表格——Q2/Q3 有真新发现

---

## 七、执行建议（优先级 + 工作量）

| 优先 | 内容 | 原因 |
|---|---|---|
| 1 | Panel TWFE 回归框架 (Q1/Q2/Q3 主线) |方法和结果直接可写报告 |
| 2 | LISA 空间聚集地图（2024 PM2.5 + 可达性双面板）| 有 HH/LL cluster 可叙事 |
| 3 | 公平性趋势 Mann-Kendall + 泰尔 decomposition 图 | 严谨且有现成结果可展示 |
| 4 | COVID 冲击 Interrupted 事件回归 (2020) | 故事性极强，有统计显著 |
| 5 | 城市级 Lorenz curve & zone-gini | 报告 vivid 谈资 |
| 6 | KMeans 省分层聚类 (health-stress typology) | 补充叙事 |

**依赖已装齐**: statsmodels 0.15, scipy 1.18, sklearn 1.9, esda 2.10, libpysal 4.15, shapely 2.1 (q2 access), geopandas 1.1.4。

