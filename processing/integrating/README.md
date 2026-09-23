# processing/integrating — 跨源融合层

## 命名规范

### 脚本
`q{N}_{主题}_{空间粒度 / 计算逻辑}.py`，与输出数据集同名（如 `q2_healthcare_accessibility.py`）。

### 输入
**只读** `data/cleaned/`（例外：原始路网 pbf 无 cleaned 形态，可读 `data/raw/`）。

### 输出
落入 `data/integrated/q{1,2,3}_*` 三个研究问题文件夹之一：

| 文件夹 | 研究问题 |
|--------|---------|
| `q1_environment_health/` | 城市环境质量与居民健康结局的空间关联 |
| `q2_healthcare_access/` | 医疗资源分布与就医可达性、区域经济发展 |
| `q3_equity/` | 地区间医疗服务公平性、环境与经济对健康不平等的影响 |

### 数据集命名
`q{N}_{主题}_{空间粒度}.csv`，如现有 `q2_healthcare_accessibility_city.csv`（Q2 × 可达性 × 城市级）。

空间粒度取 `city`（363 城市级）/ `province`（31 省）/ `national`。
