# 城市环境、医疗资源与居民健康 — 多源数据融合分析

## 项目概述

围绕"城市环境质量、医疗资源分布与居民健康"这一核心问题，从 8 个独立数据源采集多维度数据，通过空间、时间和实体关联进行跨源融合分析。

### 核心研究问题

1. **Q1**: 城市环境质量（空气质量、水质量、气象）是否与居民健康结局存在空间关联？
2. **Q2**: 医疗资源（机构 POI、床位、人员）的空间分布是否与就医可达性、区域社会经济发展水平相关？
3. **Q3**: 不同地区之间医疗服务供给的公平性如何，环境与经济因素如何共同影响健康不平等？

## 数据源

### 原始数据总览

| 数据源 | 类型 | 大小 |
|--------|------|------|
| S1 OpenStreetMap 中国路网 | 地理空间矢量 (PBF) | 1.5GB |
| S2 百度地图医疗机构 POI | 结构化数据 (CSV) | 1.4MB |
| S3 环境数据 | 结构化数据 (CSV) | 13MB |
| S4 ERA5 再分析气象数据 | 科研栅格 (NetCDF) | 1.6GB |
| S5 健康与医疗服务数据 | 统计数据 (CSV) | 74MB |
| S6 国家数据平台省级经济指标 | 统计数据 (CSV) | 11MB |
| S7 人口数据 | 政府公报/统计数据 (CSV) | 39KB |
| S8 行政区划边界 | 地理空间矢量 (GeoJSON) | 4.6MB |

> 各数据源的详细说明见 [data_sources.md](data_sources.md)；清洗后的数据说明见 [cleaned_data.md](docs/cleaned_data.md)；整合后的数据说明见 [integrated_data.md](docs/integrated_data.md)；完整数据见 [releases](https://github.com/dolphinwesting248/HealthMap/releases)。

### 数据关联与质量验证

| 材料 | 位置 |
|------|------|
| 多源数据关联图 | [imgs/data_lineage.png](imgs/data_lineage.png)（源码 `visualization/data_lineage.py`）|
| 数据质量检查报告（完整性/唯一性/有效性/一致性 四类规则） | [docs/data_quality_report.md](docs/data_quality_report.md) |
| 跨源空间关联验证 | [docs/spatial_association_validation.md](docs/spatial_association_validation.md) |
| 数据清单与 MD5 校验值 | [docs/data_manifest.md](docs/data_manifest.md) |

---

## 协作指南

面向负责**分析与可视化**的成员（数据获取、放置、分支工作流、文档规范等）：[collaboration.md](docs/collaboration.md)

要点速览：

- 数据不在 git 仓库中，从 [Release](https://github.com/dolphinwesting248/HealthMap/releases) 下载后解压到 `data/`（做分析主要用 `data_integrated.zip`）
- 分析路线与方法见 [docs/analysis.md](docs/analysis.md)，先读这个
- **每次工作开新分支**，不在 `main` 上直接改，完成后提 PR
- 代码与文档同步提交，不要留"下次再补文档"
- AI 使用记录按协作要求维护在 [AI_USAGE.md](AI_USAGE.md)

## Q2 分析与复现

| 分析 | 说明文档 | 脚本 | 结果 |
|------|----------|------|------|
| 医疗资源、经济与城市可达性 | [Q2 主分析](docs/analysis_q2_focused.md) | [`q2_analysis.py`](analysis/q2_healthcare_access/q2_analysis.py) | `analysis/q2_healthcare_access/q2_analysis_results.csv` |
| 城市可达性 Moran's I / LISA | [Q2 空间分析](docs/analysis_q2_spatial.md) | [`q2_spatial_autocorrelation.py`](analysis/q2_healthcare_access/q2_spatial_autocorrelation.py) | [总体结果](analysis/q2_healthcare_access/q2_accessibility_moran_results.csv)、[城市结果](analysis/q2_healthcare_access/q2_accessibility_moran_city_results.csv) |

在项目根目录安装 `requirements.txt` 后运行：

```bash
python analysis/q2_healthcare_access/q2_analysis.py
python analysis/q2_healthcare_access/q2_spatial_autocorrelation.py
```

当前脚本读取 `data/integrated/integrated/` 下的 Q1/Q2 融合表；空间分析还读取 `data/cleaned/cleaned/geo_boundary.geojson`。城市可达性是单点快照，空间分析仅使用有有效 `nearest_hospital_min` 且可匹配城市边界的城市；完整筛选口径与局限见对应报告。本项目这两项 Q2 分析只输出表格，不生成图表。

### 面向可视化协作成员

以下是可供后续协作的可视化需求建议，目前不包含已生成图表：

1. **城市最近医院可达性地图**：使用 [逐城空间结果](analysis/q2_healthcare_access/q2_accessibility_moran_city_results.csv) 中的 `longitude`、`latitude`、`nearest_hospital_min` 着色；363 城中仅 296 城有有效分钟数，其余缺失应显示为缺测，不得按 0 分钟或不可达值插补。
2. **KNN-4/LISA 探索图层**：可选展示 `lisa_quadrant` 或 `knn4_spatial_lag_min`，用于探索邻接结构；同时保留 `lisa_significant_fdr_05` 标记。当前 FDR 校正后显著城市数为 0，因此不能把未校正象限或候选点标成已确认热点。

图例与标题应注明可达性是单点快照、时间单位为分钟、空间邻接为 KNN-4；统计定义和局限见 [Q2 空间分析报告](docs/analysis_q2_spatial.md)。

---

## 环境依赖

- Python 3.12+；基础: requests, pandas, numpy, beautifulsoup4, lxml, python-dotenv
- 融合/分析: networkx, shapely, osmium, geopandas, matplotlib, statsmodels, scipy, scikit-learn, esda, libpysal
- 路网处理: [`osmium-tool`](https://osmcode.org/osmium-tool/) (apt install osmium-tool) — 100× 提速
- API Key配置: 复制 `.env.example` 为 `.env` 并填入 `BAIDU_AK` 等
