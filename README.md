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

## 数据分析与可视化协作说明

> 面向负责**分析与可视化**的成员：你不需要重新采集或清洗数据，
> 直接下载已融合好的数据（`data/integrated/`）开始分析即可。

### 1. 获取代码

```bash
git clone https://github.com/dolphinwesting248/HealthMap.git
cd HealthMap
```

已有仓库时先同步最新：

```bash
git pull
```

### 2. 下载数据

数据**不在 git 仓库里**（体积原因，已加入 `.gitignore`），全部放在 GitHub Release：

**发布页**：https://github.com/dolphinwesting248/HealthMap/releases/tag/data-v1

| 附件 | 内容 | 大小 | 你需要吗 |
|---|---|---|---|
| `data_integrated.zip` | **跨源融合数据**（Q1/Q2/Q3 共 7 个数据集）| 142 KB | ✅ **做分析主要用这个** |
| `data_cleaned.zip` | 清洗后数据（15 个数据集）| 117 MB | ✅ 需要更细粒度或原始字段时用 |
| `data_raw01.zip` + `data_raw02.zip` | 原始数据（8 个数据源）| 1.53 GiB ×2 | ❌ 一般不需要（除非要核对数据来源）|

#### 下载方式

**方式 A：浏览器** — 打开发布页，点击附件直接下载。

**方式 B：命令行**（推荐，可只下载需要的）：

```bash
# 只下融合数据 + 清洗数据
gh release download data-v1 -R dolphinwesting248/HealthMap -p "data_integrated.zip" -p "data_cleaned.zip"

# 或全部下载
gh release download data-v1 -R dolphinwesting248/HealthMap
```

### 3. 放到正确位置

数据必须解压到项目根的 `data/` 下，目录名需与下表一致（脚本按固定路径读取）：

```
HealthMap/
└── data/
    ├── raw/          # ← data_raw.*.zip 解出
    ├── cleaned/      # ← data_cleaned.zip 解出
    └── integrated/   # ← data_integrated.zip 解出
```

解压命令：

```bash
cd HealthMap/data

# ① 融合数据（常用）
unzip ~/Downloads/data_integrated.zip       # 解出 integrated/

# ② 清洗数据
unzip ~/Downloads/data_cleaned.zip          # 解出 cleaned/

# ③ 原始数据：注意是分卷，必须先合并再解压
cat ~/Downloads/data_raw01.zip ~/Downloads/data_raw02.zip > data_raw.zip
unzip data_raw.zip                          # 解出 raw/
rm data_raw.zip                             # 合并用的临时文件，可删
```

解压后自检（应能看到文件）：

```bash
ls data/integrated/q1_environment_health/ data/integrated/q2_healthcare_access/ data/integrated/q3_equity/
```

### 4. 从哪开始分析

| 你想做的事 | 看这个 |
|---|---|
| **分析路线、方法、样本量、注意事项** | [`docs/analysis.md`](docs/analysis.md) ← **先读这个** |
| 融合数据有哪些表、每列什么意思、有什么坑 | [`docs/integrated_data.md`](docs/integrated_data.md) |
| 清洗数据的字段与缺失值策略 | [`docs/cleaned_data.md`](docs/cleaned_data.md) |
| 数据从哪来、怎么采的、许可 | [`data_sources.md`](data_sources.md) |
| 数据间怎么关联的（画图用） | [`imgs/data_lineage.png`](imgs/data_lineage.png) |
| 数据质量、已知问题 | [`docs/data_quality_report.md`](docs/data_quality_report.md) |

**最常用的三张表**：

```
data/integrated/q3_equity/q3_equity_panel.csv        # 全要素面板（316 省×年 × 100 列）—— 三问的通用底表
data/integrated/q2_healthcare_access/q2_healthcare_accessibility_city.csv   # 363 城就医可达性
data/integrated/q3_equity/q3_equity_metrics.csv      # 年度公平性指标（10 年 × 25 列）
```

### 5. 代码放哪里

```
analysis/        # 分析脚本放这里（目前为空，等你来写）
visualization/   # 出图脚本放这里（现有 data_lineage.py 是关联图）
```

`analysis.md` 第五节列了 7 张建议的核心可视化及其数据来源，可直接照做。

### 6. 环境准备

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

分析常用：`pandas numpy matplotlib` + `statsmodels scipy scikit-learn`（回归/聚类）+ `geopandas libpysal esda`（空间分析与地图）。

### 7. 提交工作（每次工作都开新分支）

**不要在 `main` 上直接改**——每次工作开一个新分支，做完推上去提 PR，复核后合并。

```bash
# ① 同步 main
git checkout main && git pull

# ② 开新分支（命名: 工作类型/简短主题）
git checkout -b analysis/q3-equity-trend
#             ├─ analysis  分析
#             ├─ viz       可视化
#             ├─ docs      文档
#             └─ fix       修 bug

# ③ 干活，随时查看改动
git status
git diff

# ④ 提交（只加你写的代码/文档, 别加 data/）
git add analysis/ docs/analysis_q3.md
git commit -m "analysis: 完成 Q3 基尼系数趋势分析"

# ⑤ 推送分支
git push -u origin analysis/q3-equity-trend

# ⑥ 在 GitHub 上开 Pull Request（终端也可）
gh pr create --fill --base main

# ⑦ PR 合并后回到 main, 删掉本地分支
git checkout main && git pull
git branch -d analysis/q3-equity-trend
```

**注意事项**：

- ❌ **不要 `git add data/`** —— 数据体积大且已在 `.gitignore` 中，提交会失败或撑爆仓库
- ❌ 不要提交 `.venv/`、`__pycache__/`、大图片中间产物（`.gitignore` 已覆盖大部分）
- ✅ 图片产出放 `imgs/`（如需要）或 `visualization/output/`
- ✅ 一次工作一个分支、一个 PR；分支别开太久，做完就合并，减少与他人改动的冲突
- ⚠️ 若 `git push` 报 TLS/连接错误，重试一次通常即可（网络抖动）

### 8. 遇到数据问题怎么办

1. 先查 [`docs/data_quality_report.md`](docs/data_quality_report.md) —— 已记录的已知局限（如 US AQI 越界值）不必重复排查
2. 再查 [`docs/integrated_data.md`](docs/integrated_data.md) 的「缺失值」小节 —— 空值可能是"源数据本就无此年"，不是错误
3. 确认是数据生成的问题，请联系数据侧（改 `processing/` 下的脚本重跑），**不要手改 CSV**

### 9. 文档随工作同步更新

**代码提交时，文档要一起跟上**——文档过时比没有文档更误导人。每完成一块工作，先问自己"这改变了哪份文档的记录"。

#### 需要随之更新的已有文档

| 文档 | 什么时候要改 |
|---|---|
| `README.md` | 新增数据/脚本/输出目录、快速开始命令变化、协作流程调整、新成员上手方式变化 |
| `AI_USAGE.md` | 每次用 AI 完成了一段实际工作 —— 补上"任务 / 采纳情况 / 人工核验方式 / 修改与反思"，包括 AI 出错被纠正的记录 |

#### 应当新增的说明文档

自己负责的那块工作，需要留下**别人能看懂、能复核**的说明，建议统一放在 `docs/`：

| 你的工作 | 建议文档 | 至少包含 |
|---|---|---|
| 分析 | `docs/analysis_<主题>.md` | 研究问题、用了哪些表与字段、方法与选择理由、样本量与筛选条件、结果、**结论的局限** |
| 可视化 | `docs/visualization.md` | 每张图回答什么问题、数据来源与口径、图在哪（文件路径）、怎么重新生成 |

分析方法与结论尤其要写清**验证过程**：做了什么检验、排除了哪些替代解释、哪里还不确定。图表要有问题式标题（如"降雨增加后道路速度是否下降？"），并在图注中标注数据范围、单位与来源。

#### 几条习惯建议

- **文档与代码同一个 PR/commit**：不要留"下次再补文档"
- **发现文档与数据不符时**：先确认哪个是对的，再改错的那个；不要只改文档掩盖数据问题
- **不确定写在哪**：`docs/analysis.md` 是分析路线的总纲，具体工作细节放各自的专题文档，不要都堆进总纲

---

## 环境依赖

- Python 3.12+；基础: requests, pandas, numpy, beautifulsoup4, lxml, python-dotenv
- 融合/分析: networkx, shapely, osmium, geopandas, matplotlib, statsmodels, scipy, scikit-learn, esda, libpysal
- 路网处理: [`osmium-tool`](https://osmcode.org/osmium-tool/) (apt install osmium-tool) — 100× 提速
- API Key配置: 复制 `.env.example` 为 `.env` 并填入 `BAIDU_AK` 等
