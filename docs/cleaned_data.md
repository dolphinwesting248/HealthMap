# cleaned data说明

> 项目：城市环境、医疗资源与居民健康 — 多源数据融合分析
> 对应采集源 S1–S8 见 [data_sources.md](../data_sources.md)；清洗代码见 `processing/cleaning/clean_*.py`

---

## 一、数据总览

| 文件 | 清洗源 | 类型 | 大小 | 规模 | 关联粒度 |
|------|--------|------|------|------|---------|
| geo_road_poi.geojson | S1 OSM pbf | GeoJSON | 160MB | 564,702 features | 经纬度 |
| env_weather_{2023,2024,2025}.csv | S4 ERA5 NetCDF | CSV | 120MB ×3 | ~140 万行/年, 10 列 | 经纬度×日 |
| health_service.csv | S5a 国家数据平台 12 领域 + WHO | CSV | 3.3MB | 31,714 行, 11 列 | 省×年 |
| env_air_quality.csv | S3a Kaggle 空气质量 | CSV | 3.2MB | 33,976 行 × 15 列 | 城市×日 |
| health_resource_poi.csv | S2 百度医疗 POI | CSV | 2.1MB | 9,893 行 × 15 列 | POI 点 |
| econ_gdp.csv | S6 GDP + 地方财政 | CSV | 1.8MB | 20,460 行 × 8 列 | 省×年 |
| env_water_quality.csv | S3b Kaggle 水污染 | CSV | 532KB | 3,000 行 × 25 列 | 监测站点×日 |
| econ_labor.csv | S6 就业与工资 | CSV | 1.2MB | 11,160 行 × 8 列 | 省×年 |
| econ_price.csv | S6 价格指数 | CSV | 11MB | 107,880 行 × 8 列 | 省×年 |
| geo_boundary.geojson | S8 DataV 边界 | GeoJSON | 4.4MB | 484 features | 行政区划 |
| econ_pop_age.csv | S6 年龄构成与抚养比 | CSV | 208KB | 2,170 行 × 8 列 | 省×年 |
| econ_income.csv | S6 居民人均可支配收入 | CSV | 88KB | 930 行 × 8 列 | 省×年 |
| econ_life_expectancy.csv | S6 平均预期寿命 | CSV | 76KB | 930 行 × 8 列 | 省×年 |
| pop_wb.csv | World Bank | CSV | 40KB | 774 行 × 4 列 | 国家×年 |
| pop_census.csv | S10 七普公报 | CSV | 4KB | 31 行 × 6 列 | 省(2020) |

---

## 二、数据集详情

### S1 → geo_road_poi.geojson (OSM POI)

**元数据**

| 属性 | 内容 |
|------|------|
| 清洗脚本 | `processing/cleaning/clean_geo_road.py` |
| 输入 | `data/raw/geo_road/china-latest.osm.pbf` (1.5GB 二进制路网) |
| 输出 | `data/cleaned/geo_road_poi.geojson` (160MB, 564,702 features) |
| 提取范围 | 15 类节点: 医院(2,569)/诊所/药店/学校/大学/公交站/社交设施等 |
| 关键字段 | osm_id, category, type, name, healthcare, lat, lon |
| 用途 | Q2 就医可达性的目的地集 |

**清洗策略**

1. **osmium CLI tags-filter 预过滤**优先，兼容 pyosmium 全量 Python 扫描
2. 提取全部目标 POI 节点坐标与标签 → 单一 GeoJSON
3. 二进制 PBF 无文本行, 规模变化以 features 数衡量: 全国 2.6 亿节点 → 56.5 万 POI (0.2%)

### S2 → health_resource_poi.csv (医疗 POI)

**元数据**

| 属性 | 内容 |
|------|------|
| 清洗脚本 | `clean_health_resource.py` |
| 输入 | `data/raw/health_resource/medical_poi.csv` (1.4MB, 8,005 条) |
| 输出 | `data/cleaned/health_resource_poi.csv` (2.1MB, 9,893 行 × 15 列) |
| 新增列 | longitude_wgs84, latitude_wgs84, province |

**样本**

```csv
id,name,address,city,district,telephone,longitude,latitude,...,longitude_wgs84,latitude_wgs84,province
4642844a...,首都医科大学附属北京朝阳医院,北京市朝阳区工人体育场南路8号,北京市,朝阳区,...,116.447313,39.924507,北京
```

**清洗策略**

1. **BD-09 → GCJ-02 → WGS-84 坐标转换**: BD-09 平面偏移用极坐标公式逆变换回 GCJ-02, 再用迭代法（12 轮, 收敛 <1e-6°）求 WGS-84
2. 省份映射: 城市 → 省份 (`utils.normalize_province`, 支持"市"后缀剥离)
3. 按 `id` 去重

### S3a → env_air_quality.csv (空气质量)

**元数据**

| 属性 | 内容 |
|------|------|
| 清洗脚本 | `clean_env_air.py` |
| 输入 | `data/raw/env_air/china_air_quality_daily.csv` (12.7MB, 40,424 行 × 20 列) |
| 输出 | `data/cleaned/env_air_quality.csv` (3.2MB, 33,976 行 × 15 列) |
| 覆盖 | 31 省会逐日 2023–2025 |

**样本**

```csv
date,city,province,latitude,longitude,pm25,pm10,no2,o3,aqi,temp_c,precipitation,wind_speed,year,month
2023-01-01,Beijing,Beijing,39.9042,116.4074,79.871,119.171,88.346,6.667,166,-2.4,0.0,14.1,2023,1
```

**清洗策略**

1. 列名标准化: `pm2_5_mean_ug_m3` → `pm25` 等 9 个重命名
2. **日期过滤 2023–2025**: raw 覆盖 2023–2026, 剔除 2026 数据 (40,424 → 33,976 行, 这是**缩水 16% 的原因**)
3. `province` 列自动补建 (raw 无此列, 从 `province_level_region` 派生)
4. **前向填充**: pm25/pm10/o3/temp 等 8 个数值列按城市分组 ffill(limit=3) —— 最多补 3 天缺口
5. 派生 year / month 列用于跨源按时间融合

### S3b → env_water_quality.csv (水质量)

**元数据**

| 属性 | 内容 |
|------|------|
| 清洗脚本 | `clean_env_water.py` |
| 输入 | `data/raw/env_water/china_water_pollution_data.csv` (3,000 行 × 25 列) |
| 输出 | `data/cleaned/env_water_quality.csv` (532KB, 3,000 行 × 25 列) |

**清洗策略**: 列名小写化 (`Province`→`province` 等 4 个), 日期解析 + 过滤 2023–2025, 缺失值仅统计不处置 (保留 NA 供分析阶段决策), 规模不变。

### S4 → env_weather_{2023,2024,2025}.csv (ERA5 气象)

**元数据**

| 属性 | 内容 |
|------|------|
| 清洗脚本 | `clean_env_weather.py` |
| 输入 | `data/raw/env_weather/era5_single_level_{y}.nc` ×3 (共 1.6GB NetCDF) |
| 输出 | `data/cleaned/env_weather_{y}.csv` (120MB ×3, 共 ~420 万行) |
| 时间范围 | 2023–2025 (2023 年数据不完整, CDS 下载失败; 2024-2025 完整) |

**样本**

```csv
time_0,latitude,longitude,t2m,d2m,u10,v10,sp
2024-06-01 00:00,39.75,116.25,295.6,289.9,2.85,0.71,99500.0
```

**清洗策略**

1. NetCDF → CSV 展平 (**栅格→表格): 147 × 141 格点 × 365 天 × 4 时次**
2. **降采样 3 倍**: 经纬度步长 step=3 (每 3 个格点取 1 个), 控制单年文件在 120MB
3. 变量重命名: `t2m`(温度, K), `d2m`(露点), `u10/v10`(风分量), `sp`(气压)
4. **规模说明**: 行数巨大但整年完整; 融合阶段按坐标点就近而非省级聚合

### S5 → health_service.csv (省级卫生指标 + WHO)

**元数据**

| 属性 | 内容 |
|------|------|
| 清洗脚本 | `clean_health_service.py` |
| 输入 | `data/raw/health_service/nbs_health_*.csv` (12 领域文件, 共 31,620 行) + `who_gho_china_health.csv` |
| 输出 | `data/cleaned/health_service.csv` (3.3MB, 31,714 行 × 11 列) |
| 字段 | province, adcode, year, indicator, value, domain, source 等 11 列 |

**样本**

```csv
province,adcode,year,indicator,value,domain,source
北京,110000,2016,每万人卫生技术人员数 (...),112.4,每万人口卫生技术人员数,NBS
```

**清洗策略**

1. 12 个 NBS 领域文件纵向合并, 加 `domain` 来源标记
2. 省份标准化 (去"省/市/自治区"后缀)
3. value 数值化: 空字符串/非数 → NA; **行级特征: 2025 年数据多为空 (指标未发布), 深度清洗阶段只统计不删除**
4. WHO GHO 94 条按同 schema 融合, 标记 `source=WHO`

### S6 → econ_{gdp,price,labor,income,pop_age,life_expectancy}.csv (省级社会经济)

**元数据**

| 属性 | 内容 |
|------|------|
| 清洗脚本 | `clean_econ.py` |
| 输入 | `data/raw/econ_gdp/`(GDP+财政), `econ_price/`, `econ_labor/`, `econ_income/`, `pop_age/`, `pop_life_exp/` 共 7 个 raw CSV (~132,500 行) |
| 输出 | `data/cleaned/econ_gdp.csv` 等 6 个 CSV (合计 ~19MB) |

**样本**

```csv
province,adcode,year,indicator,value,value_clean,value_num,domain
北京,110000000000,2025,地区生产总值 (亿元),52073.4,52073.4,52073.4,econ_gdp
```

**清洗策略**: 与 S5 相同 schema + `domain` 标记 (econ_gdp/price/labor/income/pop_age/life_expectancy), 数值化 `value → value_num`。**仍保留为空的行 (value_num NA, 3,714/20,460) 是"指标未出数"如 2025 部分就业细分, 不做删除**。

### S7a → pop_census.csv; S7b → pop_wb.csv (人口)

| 属性 | pop_census (七普) | pop_wb (World Bank) |
|------|------------------|--------------------|
| 输入 | 七普公报 (31 行) | worldbank 3 个 CSV (2,325 行) |
| 输出 | 31 行 × 6 列 (2KB) | **774 行 × 4 列 (40KB)** |
| 覆盖 | 2020 年单点 | 1960–2025, 有值年份仅 (~774) |

**清洗策略**: pop_census 仅去空值/标准化 (规模不变)。pop_wb 为 `worldbank_population_china.csv` (15 个世界银行指标 × 有值年份, 774 行) 的直接数值化; `data_sources.md` 中提到的另两个补充文件 (world_bank_health_social / supplement) 当前不在 raw 目录中, 未纳入清洗。

### S8 → geo_boundary.geojson (行政区划边界)

| 属性 | 内容 |
|------|------|
| 输入 | `data/raw/geo_boundary/{adcode}_{name}.json` × 32 |
| 输出 | `data/cleaned/geo_boundary.geojson` (4.4MB, 484 features) |
| 层级 | province 34 + city 363 + district 86 (+1 全国) |
| 注意 | **清洗时 properties 中丢弃了 center/centroid 字段** (省空间); 如需中心点, 用 geometry 计算平均中心 (integrating 层即这样做) |

---

## 三、缺失值总结

| 数据集 | 缺失原因 | 处理 |
|--------|---------|------|
| env_air | 气象/污染少量缺测 | 按城市 ffill ≤3 天 |
| health_service | 2025 年指标未发布 | 保留 NA |
| econ_p* | 未出数 (就业细分/寿命年际) | 保留 NA, 另存 value_num 数值列 |
| health_resource_poi | 百度 API 部分字段 (telephone/tag) 空 | 保留 NA |
| econ_gdp/finance | 年末未出数 (2025 部分空) | 保留 NA |

---

## 四、规模变化摘要

| 数据集 | raw | cleaned | 变化原因 |
|--------|-----|---------|---------|
| env_air | 40,424 行 (2023–2026) | 33,976 行**↓16%** | 时间过滤剔除 2026 |
| env_weather | 1.6GB NetCDF 光栅 | ~420 万行 CSV (120MB ×3) | 栅格降采样 + 展平, 行多而体量更小 |
| health_resource POI | 9,894 行 (含补采) | 9,893 行 (持平) | 去重 -1; 新增 WGS-84 列使文件 1.7MB→2.1MB |
| pop_wb | 774 行 (单文件) | 774 行 (不变) | 直通式保留, 另两个 raw 补充文件未采集到 |
| health_service | 12 文件 31,620 行 | 31,714 行**基本持平** (+94 WHO) | 合并增列 |
| econ_gdp | 5,580 (GDP 单文件) | 20,460 行**↑3.7 倍** | + 财政 14,880 行合并 |
| econ_price | 107,880 | 107,880 (持平) | 未过滤 |
| econ_income / pop_age / life_exp | 930/2170/930 | 同 | 未过滤 |
| pop_census | 31 | 31 | 不变 |
| geo_boundary | 32 文件多级嵌套 | 484 features | 合并 + 简化属性 |
| geo_road | 1.5GB 全网 2.6 亿节点 | 56.5 万 POI GeoJSON | 仅需节点要素 |
