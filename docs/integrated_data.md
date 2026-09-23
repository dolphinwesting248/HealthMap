# Integrated data说明

> 项目：城市环境、医疗资源与居民健康 — 多源数据融合分析
> 清洗层文档见 [cleaned_data.md](cleaned_data.md)；融合代码见 `processing/integrating/`

---

## 一、数据总览

| 文件 | 所在文件夹 | 大小 | 规模 | 粒度 | 年份覆盖 | 研究问题 |
|------|-----------|------|------|------|---------|---------|
| q1_env_exposure_province.csv | q1_environment_health | 27KB | 99 行 × 35 列 | 省×年 | 空气 2023-25 / 水 2023 / ERA5 2023-2025 | Q1 |
| q1_health_outcome_province.csv | q1_environment_health | 30KB | 279 行 × 22 列 | 省×年 | 2016-2024 (寿命 2020) | Q1 |
| q1_env_health_panel.csv | q1_environment_health | 71KB | 316 行 × 58 列 | 省×年 | 全年（env 仅 23+） | Q1 分析面板 |
| q2_medical_resource_province.csv | q2_healthcare_access | 42KB | 279 行 × 28 列 | 省×年 | 2016-2024 | Q2 |
| q2_healthcare_accessibility_city.csv | q2_healthcare_access | 20KB | 363 行 × 13 列 | 城市(363城) | 单点 | Q2 |
| q3_equity_metrics.csv | q3_equity | 4KB | 10 行 × 25 列 | 全国年度横截面 | 2016-2025 | Q3 |
| q3_equity_panel.csv | q3_equity | 158KB | 316 行 × 100 列 | 省×年 | 全要素总面板 | Q1/Q2/Q3 |

---

## 二、数据集详情

### q1_env_exposure_province.csv（省级环境暴露）

**元数据**

| 属性 | 内容 |
|------|------|
| 生成脚本 | `q1_env_exposure_province.py` |
| 输入 | cleaned: env_air_quality, env_water_quality, env_weather_{y}, geo_boundary |
| 输出 | 99 省×年 × 35 列 |
| 粒度 | 省×年 |

**输出列摘要**

| 组 | 列 | 说明 |
|---|---|------|
| air（来自 31 省会逐日）×13 | air_pm25_mean/max, pm10, aqi_mean/max, o3, no2, days_aqi_gt100, precip_sum, precip_days, temp_mean | 省会城市日均值的省域聚合; 年份受 Kaggle 源限制 2023-2025 |
| water（10 省监测站）×17 | water_wqi_mean/min, do, cod, nh3n, pH, TN, TP, nitrate, nitrite, bod, Pb/Cd/Hg, coliform, polluted_frac, stations | 源数据自身仅 10 省; **2023 单年** |
| ERA5 气象 | weather_t2m_mean, d2m, wind_mean/max (hypot(u,v) 合成), n_grid | 格点→省 **严格 Point-in-Polygon**；境外(海/邻国)格点剔除, 2023-2025 |

**样本**

```csv
province,year,air_pm25_mean,...,water_wqi_mean,...,weather_t2m_mean,...
北京,2023,72.65,...,52.36,...,280.35
```

**生成策略**
1. air: 省会城市×日 → province 聚合 mean/max; 英文省名 normalize → 中文
2. water: 数据自带 province 列（10 省）直接用（旧版曾按经纬度最近省中心错配为 29 省, 已修正）
3. ERA5 147×141 格点×daily → 每 3 格点取 1 (0.75°); 格点→省用**严格 Point-in-Polygon**，国境外(海/邻国)格点剔除（境内占 44.7%）

---

### q1_health_outcome_province.csv（省级健康结局）

| 属性 | 内容 |
|------|------|
| 生成脚本 | `q1_health_outcome_province.py` |
| 输入 | cleaned: health_service (12 领域), econ_life_expectancy (2020), econ_pop_age (2016-2024, 人抽样调查) |
| 输出 | 279 省×年 × 22 列 |

**输出列摘要**

| 组 | 列 | 说明 |
|---|---|------|
| 服务质量（来自 health_service）×8 | outcome_er_mortality_rate, obs_mortality_rate, rescue_success/er_rescue, bed_utilization, avg_los | 急诊病死率、观察室病死率、危重抢救成功率等 |
| 健康服务量代理×7 | outsvc_visits_yi, outpatient_yi, discharges_wan, surgeries_wan, admission_per_100, bed_turnover, township_visits_yi | 健康负荷/医疗服务利用指标 |
| 预期寿命 ×3 | outcome_life_expectancy, male, female | **仅 2020 (七普年)**, 供空间横截面使用 |
| 年龄构成 ×6 | outcome_age_pop_0_14, 15_64, 65p, n, dependency_ratio(总/儿童/老年) | 抽样调查年 2016-2024 (无 2020/2025) |

**清洗策略**
1. health_service 中 quality 类 indicator 长表→宽表（group mean on value_num）
2. WHO 国家级（province=CHN）剥离, 避免混入省行
3. 三表按 province/year outer merge, 保留各源可得年
4. **时间取向**: 病死率类 (2018-2024 实际有值)、寿命 (2020)、年龄构成 (2016-2024) 各自年不同

---

### q1_env_health_panel.csv（Q1 分析面板）

| 属性 | 内容 |
|------|------|
| 生成脚本 | `q1_panel_build.py` |
| 输入 | Q1 暴露/结局两表 + cleaned econ_income (控制) |
| 输出 | 316 省×年 × 58 列 |
| 结构 | `province, year, [air_* x7, water_* x17, weather_* x4], [outcome_* x8, outsvc_* x7, life_expectancy* x3, age_pop* x6], econ_income_total/urban/rural` |

**样本**

```csv
province,year,air_pm25_mean,...,outcome_er_mortality_rate,...,econ_income_total
上海,2023,48.48,...,0.11,...,84775
```

**注意 / 使用提示**
- `air/water/weather_*` 仅 2023-2025 有值（是源数据时间边界），2016-2022 行保留供历史结局分析但 env 为 NA
- `outcome_life_expectancy*` 仅 2020 年有值
- 分析 Q1 "环境×结局" 推荐子集：years=[2023, 2024]（n=62）或 2020 寿命空间横截面 (n=31, 注明时间错位)

---

### q2_medical_resource_province.csv（省级医疗资源标准化）

| 属性 | 内容 |
|------|------|
| 生成脚本 | `q2_medical_resource_province.py`（空间归属用 `spatial_join.py` 的严格 PIP）|
| 输入 | cleaned: health_service（101 指标中挑 19 core）、health_resource_poi（9,893 POI）、geo_boundary（POI 落省 + 面积近似）、pop_census（七普分母）、econ_pop_age（65+人口） |
| 输出 | 279 省×年 × 28 列 |

**输出列摘要**

| 组 | 列 |
|---|---|
| 绝对量 (万单位 / 个) ×14 | med_institutions/hospitals/general/tcm/primary_care, beds_wan, beds_hospitals/hospwc, visits, admissions, personnel/health_tech/doctors/nurses |
| NBS 原生每万人 ×5 | per10k_beds_all, per10k_beds_hospwc, per10k_health_tech, per10k_doctors, per10k_nurses |
| POI (S2 落省) ×3 | poi_count_s2, poi_density_per_10kkm2, poi_per_10kpop |
| 备用分母 | pop_2020_wan (七普) |
| 本脚本计算每万人口 ×5 | per10k_beds/doctors/nurses_calc, poi_per_10kpop, beds_per_10k_elderly (每万名 65+ 老人对应床位) |

**样本**

```csv
province,year,med_hospitals,med_beds_wan,per10k_beds_all,...,pop_2020_wan,poi_per_10kpop,beds_per_10k_elderly
上海,2016,349.0,12.92,53.37,...,2487.0,262.0,
```

**说明**:
- POI 覆盖 31 省会市区 (非全省), `poi_density_per_10kkm2` 是省会城市 POI 数 / 全省面积 ×10⁴, 属下限估计
- `beds_per_10k_elderly` 分析老龄化压力, 只在 pop_age 有值的年份 (2016-2019, 2021-2024) 非空

---

### q2_healthcare_accessibility_city.csv（城市级就医可达性）

| 属性 | 内容 |
|------|------|
| 生成脚本 | `q2_healthcare_accessibility.py` |
| 输入 | cleaned: geo_road_poi (OSM 医院 2,569 个目的地), clean geo_boundary(城市级中心点), raw/osm pbf (路网) |
| 输出 | 363 城市 × 13 列 |
| 粒度 | 城市级 (全部地级市 boundary) |

**输出列**

city, hospitals_window, nearest_hospital_km/min, hospitals_15min/30min/60min (等时圈医院数), major_nearest_km/min, major_30min, mean_hospital_km_roundtrip, window_area_km2, method (network|euclidean)

**样本**

```csv
city,hospitals_window,nearest_hospital_km,nearest_hospital_min,...,method
七台河市,2,94.76,77.3,...,network
三门峡市,0,,,,network
```

**计算要点**
- 每城自省会中心 (cleaned boundary 城市 mean-center) 以 0.6° (~60km 半径) 剪出 OSM 窗口子图 → heapq Dijkstra → 到最近/大医院的路网距离与时长
- `method=euclidean` 表示窗口内无路网, 用欧氏折算 (362/363 为 network)
- **两年复制策略**: 数据是"当前快照" — 不构成时序面板

---

### q3_equity_metrics.csv（年度公平性指标）

| 属性 | 内容 |
|------|------|
| 生成脚本 | `q3_equity_metrics.py` |
| 输入 | Q2 资源表 + Q1 暴露/结局 + econ_income + econ_price (CPI 平减) |
| 输出 | 10 年 (2016-2025) × 25 指标 |
| 粒度 | 全国年度横截面（31 省聚合为指标） |

**输出列**

| 组 | 指标 |
|---|------|
| 资源 Gini/CV ×10 | gini/cv per10k_beds_all, per10k_doctors, per10k_nurses, per10k_health_tech, med_hospitals (5 项×2) |
| 收入 Gini/CV ×3 | gini/cv_real_income (名义÷CPI 累计), gini_nominal_income |
| 泰尔 & 分位比 ×5 | theil_real_income, theil_within/between_real_income (规范 Shorrocks 口径, T=Tb+Tw 恒等), theil_between_share, income_p90_p10, income_max_min |
| 环境/结局 Gini/CV ×5 | air_pm25, life_expectancy 等仅当对应年份有值 |
|地带内 Gini ×3 | gini_beds_东部/中部/西部（资源 by 地带）|

**样本**

```csv
year,gini_per10k_beds_all,gini_real_income,theil_real_income,theil_between_share,income_p90_p10,...
2016,0.072,0.191,0.068,0.559,2.04
2024,0.075,0.171,0.056,0.521,1.79
```

**方法与结论摘要**:
- 泰尔分解按东/中/西三大地带，恒等式 T=Tw+Tb 验证 (最大偏差 1e-16)
- 主要发现: 实际收入 Theil 2016→2025 从 0.068 → 0.055 递降; **地带间份额 ~52-55% → 区间间的结构差距是主要不平等源**
- gini_air_pm25 仅 2023-2024 有 (2016-2022 无 env 源)

---

### q3_equity_panel.csv（Q3 全要素分析面板）

| 属性 | 内容 |
|------|------|
| 生成脚本 | `q3_panel_build.py` |
| 输入 | Q1 panel + Q2 资源 + **Q2 城市可达性 (省均聚合, 含 P90)** + econ_labor (卫生社工就业) + pop_wb (World Bank 国家级背景) |
| 输出 | 316 省×年 × 100 列 |

**输出列摘要**

| 组 | 前缀 | 说明 |
|---|------|------|
| 环境暴露 (同 Q1) | air_/water_/weather_ | 2023-2025 |
| 健康结局 (同 Q1) | outcome_/outsvc_ | 年份因指标而有 |
| 医疗资源 (同 Q2) | med_/per10k_/poi_/beds_ | 2016-2024 |
| 可达性省均 ×8 | acc_nearest_km_mean/p90, acc_hospitals_30min_mean, acc_major_*, acc_mean_roundtrip | 363 城按省 mean+P90 聚合 (P90 为分布尾部, 公平性敏感) |
| 控制 ×1 | ctrl_healthcare_employment_wan (卫生社工就业) | econ_labor 拼接 |
| WB 国家背景 ×13 | wb_life_expectancy, wb_urbanization_rate, wb_gdp_per_capita, wb_health_exp_gdp, wb_physicians/beds_per_1000, wb_gini 等 | 按 year 挂接 (不能与省 join) |

**使用说明**: 该面板是 Q1/Q2/Q3 的统一分析底表；`acc_*` 列是城市级可达性向省均的投影；wb_* 列在国家层面所有省值一致，回归时只能作 national-level time-varying 控制。

---

## 三、缺失值与融合口径汇总

| 数据集 | 缺失说明 | 分析策略 |
|--------|---------|---------|
| q1_env_exposure | air 仅 2023-2025；water 仅 10 省（1 种年）| 时间错位需要 Q1 分析段内明示；水为区域性分析 |
| q1_health_outcome | 寿命仅 2020; 2025 未发布 | 寿命作空间横截面; 2025 保留 NA |
| q2_medical_resource | pop_age 65+ 仅抽样调查年 (无 2015/2020/2025) | beds_per_10k_elderly 对应年份为空 |
| q2_accessibility | 单点快照 | 可达性分析侧重截面 (各法不加权, 不做时序) |
| q3_equity_metrics | gini_air 只 2023-25 | 早期年公平性用其他维度 |
| q3_panel | wb_* 全省相同 / acc_* 2016-2022 为 NA | 明示即可 |

---

## 四、数据流一览 (cleaned → integrated)

```
env_air_quality     ┐
env_water_quality   ├─ q1_env_exposure_province ─┐
env_weather _{y}    ┘                            │
health_service ┬─ q1_health_outcome_province ────┤-- q1_env_health_panel ──┐
life_expectancy┤                                  │                         ├→ q3_equity_panel → 分析
pop_age       ┘                                   │                         │
econ_income ──────────────────────────────────────┤                         │
health_service ┬ q2_medical_resource_province ────┤── q3_equity_metrics ────┤
health_resource_poi + geo_boundary + pop_census ─┘                         │
geo_road_poi + geo_boundary + raw pbf → q2_healthcare_accessibility_city ──┘
econ_price (CPI) → (q3_equity_metrics 内平减)
econ_labor, pop_wb, pop_census → (q3_panel 内控制变量/背景/分母)
```

