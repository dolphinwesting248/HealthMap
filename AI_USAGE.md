# AI 使用说明

> 项目：城市环境、医疗资源与居民健康 — 多源数据融合分析

---

## 一、AI 工具使用概览

| AI 工具/模型 | 使用时间 | 参与阶段 |
|-------------|---------|---------|
| Claude (Anthropic) | 2026-09-20 至 2026-09-23 | 选题设计、数据采集、数据清洗、数据整合 |

---

## 二、AI 参与的具体任务

### 2.1 选题与研究设计

- 帮助拆解研究问题：围绕"城市环境质量、医疗资源分布与居民健康"设计 3 个核心问题
- 建议数据源候选：从 WHO GHO、Kaggle、国家统计局、Kaggle、OpenStreetMap、Copernicus ERA5 等平台筛选数据源
- 设计跨源关联方案：空间（经纬度→行政区划）、时间（年度对齐）、实体（省名映射）三种关联维度

### 2.2 数据采集

**API 探索与发现**：
- 发现国家统计局新版 API 的 `stream/esData` 端点，解决了旧接口返回 403 的问题
- 测试验证多个数据源 API：百度地图、WAQI、Kaggle、CDS、World Bank、DataV 等
- 从高德 API 切换到百度地图 API（额度更高），再到国家数据平台 API

**采集脚本编写**

| 脚本 | AI 完成内容 |
|------|-----------|
| `fetch_env_air.py` | Kaggle 数据集下载、解压处理 |
| `fetch_env_water.py` | Kaggle 水质量数据下载 |
| `fetch_env_weather.py` | CDS API 对接、ERA5 变量配置 |
| `fetch_health_resource.py` | 百度地图 API 对接、区县级搜索、断点续传 |
| `fetch_health_service.py` | NBS stream/esData API 对接 + WHO GHO API |
| `fetch_geo_road.py` | Geofabrik 下载、进度显示 |
| `fetch_geo_boundary.py` | DataV API 对接、省级边界下载 |
| `fetch_econ.py` | NBS API 对接、3 领域分目录采集 |
| `fetch_pop.py` | 人口普查编译 + World Bank API |

### 2.3 数据清洗

**清洗脚本编写**

| 脚本 | AI 完成内容 |
|------|-----------|
| `utils.py` | 省份名称统一映射（31 省标准名 + 城市→省份映射 + 英文名映射） |
| `clean_env_air.py` | 时间过滤、列名标准化、前向填充缺失值 |
| `clean_env_water.py` | 时间过滤、缺失值统计 |
| `clean_env_weather.py` | NetCDF→CSV、降采样 step=3、变量重命名 |
| `clean_health_resource.py` | BD-09→WGS-84 坐标转换、省份映射、去重 |
| `clean_health_service.py` | 省份统一、value 数值化、缺失值分析 |
| `clean_geo_road.py` | osmium 提取医疗/教育/交通 POI → GeoJSON |
| `clean_geo_boundary.py` | 32 个 GeoJSON 合并、属性标准化 |
| `clean_econ.py` | 多文件合并、省份统一、value 数值化 |
| `clean_pop.py` | 人口普查 + World Bank 合并、空值删除 |

---

## 三、代表性 Prompt / 指令片段

### Prompt 1：数据源探索
```
人口与健康统计+医疗机构POI+交通/路网+环境与气象+社会经济数据；
研究医疗资源分布与就医可达性、环境因素与健康指标的关系，
以及不同地区医疗服务的公平性。这些数据如何获取，给出可以收集的指南
```

### Prompt 2：API 发现
```
查看 https://blog.csdn.net/loo_Charles_ool/article/details/159548826#1
根据其中的内容尝试用 api 获取国家统计局的 s5 数据
```

### Prompt 3：省级数据采集
```
分省卫生数据存在多个领域，https://data.stats.gov.cn/dg/website/publicrelease/web/external/new/queryIndexTreeAsync?pid=aad2947cd56047a69a6b17504f227db5&code=6
这个 api 的响应中的 _name 就是不同领域的数据，
修改脚本，获取所有领域的 2023-2025 年的卫生数据
```

---

## 四、AI 输出采纳与修改情况

| AI 输出 | 采纳/修改/放弃 | 原因 |
|---------|--------------|------|
| 数据源清单 | 采纳 | 覆盖 Q1/Q2/Q3 三个研究问题 |
| 国家数据平台 API 方案 | 采纳并扩展 | 从 1 个领域扩展到 12+5 个领域 |
| S3 Kaggle 数据集方案 | 采纳 | 替代 WAQI API，数据更完整 |
| S6 IMF 方案 | 改为 NBS API | IMF 仅国家级，NBS 有省级数据 |
| S5 GBD 省级方案 | 放弃 | GBD 2023 无省级数据，改用 NBS 卫生指标 |
| 百度地图 POI 方案 | 采纳 | 替代高德 API，额度更高 |
| 缺失值处理方案 | 采纳 | 为每个数据源设计针对性策略 |

---

## 五、AI 使用过程中出现的问题与纠正

| 问题 | 原因 | 纠正方式 |
|------|------|---------|
| 高德 API 返回 10044 | 日额度耗尽 | 改用百度地图 API（30 万次/天） |
| OpenAQ v2 返回 410 Gone | API 已废弃 | 改用 Kaggle 数据集 |
| 国家数据平台返回 403 | 反爬机制 | 发现新版 stream/esData API 端点 |
| GBD Results Tool 注册被拒 | 邮箱/IP 限制 | 放弃省级 GBD，改用 NBS 卫生指标 |
| ERA5 2023 年下载失败 | CDS 服务器处理超时 | 保留 2024–2025 数据 |
| 误删 S2 已采集数据 | 操作失误 | 教训：删除数据前必须确认 |
| S2 省份数异常（492→53→25） | 城市名带"市"后缀未处理 | 修复 normalize_province 支持去后缀匹配 |
| utils.py 中 CITY_PROVINCE 未定义就引用 | 代码结构问题 | 移到模块级别 |
| raw 数据被整体删除 | 重构目录时操作失误 | 教训：重构前备份数据 |

---

## 六、AI 对项目效率的影响

| 方面 | 影响 |
|------|------|
| 数据源发现 | 快速筛选出合适的数据源，避免逐一尝试 |
| API 探索 | 发现国家数据平台新版 API，节省数小时调试 |
| 采集脚本 | 9 个 fetch 脚本均由 AI 生成，人工微调 |
| 清洗脚本 | 9 个 clean 脚本均由 AI 编写，含缺失值策略 |
| 问题排查 | 网络超时、API 格式错误、坐标转换等由 AI 快速定位修复 |
