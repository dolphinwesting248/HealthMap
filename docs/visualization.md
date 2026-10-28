# 可视化说明文档（visualization.md）

> 本文件对应协作指南第 9 节「可视化」要求：说明**每张图回答什么问题、数据来源与口径、图在哪（文件路径）、怎么重新生成**。
> 所有图表均为本项目已有分析结论的可视化呈现，数字口径与 `docs/analysis.md`、`docs/analysis_q2_focused.md`、`docs/analysis_q2_spatial.md` 及 `integrated_data.md` 保持一致。
> 文字使用简体中文。

## 0. 文件位置总览

| 类别 | 仓库路径 | 说明 |
|---|---|---|
| 图表（10 张） | `imgs/` | 数据可视化产出，对应协作指南「图片产出放 imgs/」 |
| 图表生成脚本 | `visualization/make_charts.py` | 10 张图的一键生成脚本 |
| 汇报 PPT | `docs/presentation/HealthMap项目汇报.pptx` | 16 页汇报演示文稿（含演讲者备注） |
| 逐页讲稿 | `docs/presentation/HealthMap汇报讲稿.docx` | 配套讲稿 + 时间建议 + Q&A |
| PPT 生成脚本 | `docs/presentation/build_ppt.py`、`make_speech.py` | PPT 与讲稿生成脚本 |

---

## 1. 数据体系与流水线（2 张）

### 1.1 `imgs/data_sources.png` — 八大外部数据源体积对比
- **回答的问题**：项目整合了哪些外部数据、各自体量有多大？
- **数据来源与口径**：`data_sources.md` 列出的 8 个数据源。体积为各源原始下载量：S1 OSM 路网 1.5GB、S2 百度 POI 1.4MB、S3 环境数据 13MB、S4 ERA5 气象 1.6GB、S5 健康服务 74MB、S6 经济指标 11MB、S7 人口数据 39KB、S8 区划边界 4.6MB（纵轴对数刻度）。数据本身不在 git 仓库（已加入 `.gitignore`，发布于 GitHub Release `data-v1`）。
- **图在哪**：`imgs/data_sources.png`
- **重新生成**：`python visualization/make_charts.py`

### 1.2 `imgs/pipeline.png` — 多源数据流水线
- **回答的问题**：原始数据如何变成可分析的数据集？
- **数据来源与口径**：`README.md` 与 `analysis.md` 第五节。流程为「8 源采集 → 清洗层（15 个清洗数据集，BD-09→WGS-84 坐标转换、osmium 提速）→ 融合层（7 个融合数据集，严格 PIP + 实体/时间/空间三维关联）→ Q1/Q2/Q3」。质量保障贯穿全流程（4 类规则、36 项检查、文件清单 + MD5 校验）。
- **图在哪**：`imgs/pipeline.png`
- **重新生成**：`python visualization/make_charts.py`

---

## 2. Q1：城市环境质量与居民健康（1 张）

### 2.1 `imgs/pm25.png` — PM2.5 年均值（31 省）与国标/WHO 对照
- **回答的问题**：Q1 空气质量的基线水平，是否显著超过标准？
- **数据来源与口径**：`data/integrated/q1_environment_health/q1_env_health_panel.csv` 的 `air_pm25_mean`。31 省年均值为 2023=40.3、2024=39.3、2025=44.7 µg/m³；对照线为国家环境空气质量标准二级 35、WHO 指导值 5。env 类字段仅覆盖 2023–2025；空间格局为西部明显偏低、京津冀/晋豫明显偏高。
- **口径局限**：本图为描述性基线，不构成因果结论；寿命等结局字段存在年份错位，仅作空间关联证据。
- **图在哪**：`imgs/pm25.png`
- **重新生成**：`python visualization/make_charts.py`

---

## 3. Q2：医疗资源、可达性与区域经济（4 张）

### 3.1 `imgs/beds_trend.png` — 每万人床位数 2016–2024 趋势
- **回答的问题**：Q2 医疗资源供给是否在持续扩张？
- **数据来源与口径**：`data/integrated/q2_healthcare_access/q2_medical_resource_province.csv` 的 `per10k_beds_calc`。279 省×年面板均值：2016=53.15 → 2024=72.70，整体稳步上升。2025 年指标多未发布（NA）。
- **图在哪**：`imgs/beds_trend.png`
- **重新生成**：`python visualization/make_charts.py`

### 3.2 `imgs/accessibility.png` — 363 城就医可达性分布
- **回答的问题**：城市就医可达性是否存在明显不平等？
- **数据来源与口径**：`data/integrated/q2_healthcare_access/q2_healthcare_accessibility_city.csv` 的 `nearest_hospital_min`、`major_nearest_min`。`nearest_hospital_min` 中位数 35.30 分钟，P25=20.65、P75=54.52、P90=77.20、最大值 1461.70 分钟，分布明显右偏。环形图显示 329/363=90.63% 的城市大医院 30 分钟不可达。
- **操作性口径（重要）**：`major_hospital_30min_unreachable` 的 90.63% 为**操作性口径**——`major_nearest_min` 缺失值被临时填为 999 后也计为不可达，故 329/363 不等同于「329 个已观测到的超时城市」，不应据此夸大「实时超时城市数」。可达性为单一快照，不能做时序面板。
- **图在哪**：`imgs/accessibility.png`
- **重新生成**：`python visualization/make_charts.py`

### 3.3 `imgs/moran_lisa.png` — 可达性空间自相关（Moran's I + LISA）
- **回答的问题**：城市就医时间在空间上是否呈现邻近聚集？
- **数据来源与口径**：`data/integrated/q2_healthcare_access/q2_healthcare_accessibility_city.csv` + `data/cleaned/geo_boundary.geojson`。对 296 个有有效 `nearest_hospital_min` 的城市构造 KNN-4 空间权重（libpysal，随机种子 42，置换 9,999 次）。全局 Moran's I=0.00233，双侧随机化 `p_rand`=0.7210（正态 `p_norm`=0.8820、`p_sim`=0.3306），不能拒绝「无全局空间自相关」零假设。局部 LISA 象限：HH 41 / LH 52 / LL 146 / HL 57；未校正 p<0.05 有 35 城，但 Benjamini–Hochberg (FDR) 校正后显著城市为 0。
- **口径局限**：单点快照；依赖 KNN-4 与城市中心点定义；未校正候选点**不**作为稳健热点解释。完整口径见 `docs/analysis_q2_spatial.md`。
- **图在哪**：`imgs/moran_lisa.png`
- **重新生成**：`python visualization/make_charts.py`

### 3.4 `imgs/zone_gini.png` — 城市级医疗资源分布基尼（分地带）
- **回答的问题**：Q2/Q3 区域间医疗资源分布是否不均衡？
- **数据来源与口径**：363 城 `hospital_count_window` 的分布基尼。整体 0.679；东部 0.574 / 中部 0.664 / 西部 **0.727**，西部最不均衡，地带梯度成立。
- **图在哪**：`imgs/zone_gini.png`
- **重新生成**：`python visualization/make_charts.py`

---

## 4. Q3：公平性（3 张）

### 4.1 `imgs/equity_slope.png` — 卫生公平性年度趋势
- **回答的问题**：Q3 卫生公平性是否在改善？
- **数据来源与口径**：`data/integrated/q3_equity/q3_equity_metrics.csv`（10 年 × 25 列，省等权）。`gini_real_income` 0.191→0.168（2016→2025，缓慢改善）；`income_p90_p10` 2.04→1.79（尾部收敛）；`theil_between_share` 55.9%→51.9%（东/中/西部间结构差距是主要不平等源）；`gini_per10k_beds_all` 稳定约 0.075（床位分布稳态公平）。Mann-Kendall：`gini_income` τ=−1.0（p<0.01）、`income_p90_p10` τ=−0.96、`theil_between_share` τ=−1.0，严格单调下降；`gini_per10k_beds_all` τ=NaN（2025 全空，绘图须 skipna）。
- **图在哪**：`imgs/equity_slope.png`
- **重新生成**：`python visualization/make_charts.py`

### 4.2 `imgs/kmeans.png` — KMeans 省份健康压力分层（k=3, 2024）
- **回答的问题**：Q2/Q3 省际健康压力可分成哪些典型型态？
- **数据来源与口径**：31 省 ×（资源密度、老龄化压力、可达性、收入）四维 2024 横截面，sklearn KMeans（k=3）。cluster 2（粤/苏/浙/闽）收入均值 55k、可达 31km，「高收入高可达」；cluster 1（新疆/藏/蒙/黔/青/琼）收入 31k、可达 78km，「边远低可达」；cluster 0 为中间型。
- **口径局限**：2024 单年横截面，非时序。
- **图在哪**：`imgs/kmeans.png`
- **重新生成**：`python visualization/make_charts.py`

### 4.3 `imgs/pip_validation.png` — 空间关联校验：近似法 vs 严格 PIP
- **回答的问题**：点→省归属用「最近省中心」近似法是否可靠？应以哪种口径为准？
- **数据来源与口径**：`docs/spatial_association_validation.md`（由 `processing/integrating/spatial_join.py` 生成）。图为**近似法与严格 Point-in-Polygon 的两法一致率**，按点集对比：S2 医疗 POI（9,893 点）84.75%、363 城中心点（363 点）79.06%、ERA5 气象格点（3,818 点，境外剔除）33.08%。两法差异显著 → 近似法不可接受，融合层已全面改用严格 PIP + 多级回退（PIP → 城市名回退 → 最近中心兜底）；最终 S2 POI 9,893 条与源省份字段 100% 吻合（PIP 直接命中 9,886 + 城市名回退 7 + 最近中心兜底 0）。
- **口径注意**：84.75%/33.08% 是「两法一致率」而非「与真值吻合率」；S2 POI 自身 province 字段来自百度城市名，并非绝对真值，吻合率是两种独立来源的相互印证。海岛 POI、深港边界等回退案例见原报告。
- **图在哪**：`imgs/pip_validation.png`
- **重新生成**：`python visualization/make_charts.py`

---

## 5. 如何重新生成

### 5.1 依赖
```bash
pip install matplotlib pandas numpy
```
（PPT 与讲稿另需 `python-pptx`、`python-docx`，见 `docs/presentation/` 下脚本。）

### 5.2 一键生成 10 张图表
```bash
# 在仓库根目录执行，图表输出到 imgs/
python visualization/make_charts.py
```

### 5.3 重新生成 PPT 与讲稿
```bash
python docs/presentation/build_ppt.py    # 生成 HealthMap项目汇报.pptx
python docs/presentation/make_speech.py   # 生成 HealthMap汇报讲稿.docx
```

## 6. 图表通用规范（遵循协作指南）
- 所有图为「问题式标题」，图注标注数据范围、单位与来源；
- 关联均标注「关联非因果」，可达性标注「单一快照」，90.63% 标注「操作性口径」；
- 空间统计标注随机种子、置换次数与 FDR 校正口径；
- 图片产出统一放 `imgs/`，生成脚本放 `visualization/`，与 `analysis/` 代码同一 PR 提交。
