# 数据源清单

> 项目：城市环境、医疗资源与居民健康 — 多源数据融合分析
> 采集时间：2026-09-20 至 2026-09-22

---

## 数据源总览

| # | 数据源名称 | 获取方式 | 数据类型 | 原始规模 | 时间范围 | 许可 | 跨源关联字段 |
|---|-----------|---------|---------|---------|---------|------|------------|
| S1 | OpenStreetMap 中国路网 | 公开下载 (Geofabrik) | 地理空间矢量 | 1.5 GB | 路网快照 | ODbL | 经纬度, 行政区划 |
| S2 | 百度地图医疗机构 POI | 公开 API (百度地图) | 结构化数据 | 1.5 MB | 快照 | 学术使用 | adcode, 经纬度, 城市名 |
| S3 | 中国城市空气质量 | Kaggle 公开数据集 | 结构化数据 | 10 MB | 2023–2025 | CC BY 4.0 | 城市名, 经纬度, 年月 |
| S4 | ERA5 再分析气象数据 | CDS API (Copernicus) | 科研栅格→CSV | 1.7 GB | 2023–2025 | Copernicus 免费 | 经纬度, 时间 |
| S5 | 国家统计局省级卫生 | 国家数据平台 API | 结构化数据 | 2 MB | 2023–2025 | 政府公开 | 省份名, adcode, 年份 |
| S6 | 国家统计局省级经济 | 国家数据平台 API | 结构化数据 | 15 MB | 2023–2025 | 政府公开 | 省份名, adcode, 年份 |
| S7 | 人口普查 + World Bank | 政府公报 + API | 统计数据 | 20 KB | 2020 + 2023–2024 | 公开数据 | 省份名, adcode |
| S8 | 行政区划边界 | DataV API | 地理空间 GeoJSON | 4.4 MB | 静态 | 公开数据 | adcode, 行政区划名 |

**原始数据总量：3.21 GB**

---

## 各数据源详情

### S1. OpenStreetMap 中国路网数据

- **来源**: https://download.geofabrik.de/asia/china.html
- **获取方式**: wget 下载 .osm.pbf 文件
- **采集脚本**: `crawler/s1_fetch_osm.py`
- **清洗脚本**: `processing/cleaning/clean_s1.py`（提取医疗设施 features）
- **原始规模**: 1,522 MB (1 个文件)
- **数据格式**: OSM PBF → GeoJSON（清洗后）
- **时间范围**: 路网快照
- **许可**: Open Database License (ODbL)
- **关键字段**: 节点(nodes)、边(ways)、关系(relations)、标签(tags)
- **跨源关联字段**: 经纬度 (lat/lon)、行政区划标签

---

### S2. 百度地图医疗机构 POI

- **来源**: https://lbsyun.baidu.com/
- **获取方式**: REST API 爬取
- **采集脚本**: `crawler/s2_fetch_gaode_poi.py`
- **清洗脚本**: `processing/cleaning/clean_s2.py`
- **原始规模**: 7,129 条 POI → 去重后 6,809 条
- **数据格式**: CSV
- **时间范围**: 采集时快照
- **许可**: 学术使用
- **关键字段**: id, name, type, address, city, telephone, longitude, latitude, longitude_wgs84, latitude_wgs84, province
- **跨源关联字段**: adcode, 经纬度(WGS-84), 城市名
- **缺失值**: telephone 缺失 34.3%（正常）

---

### S3. 中国城市空气质量数据

- **来源**: Kaggle - houjihao/china-capitals-weather-and-air-quality-2023-2026
- **获取方式**: Kaggle API 直接下载
- **采集脚本**: `crawler/s3_fetch_openaq.py`
- **清洗脚本**: `processing/cleaning/clean_s3.py`
- **原始规模**: 40,424 行 → 过滤 2023-2025 后 33,976 行
- **数据格式**: CSV
- **时间范围**: 2023-01-01 ~ 2025-12-31
- **许可**: CC BY 4.0
- **关键字段**: date, city, province, latitude, longitude, pm25_ugm3, pm10_ugm3, no2_ugm3, o3_ugm3, aqi, temp_c, precip_mm, wind_kmh, year, month
- **跨源关联字段**: 城市名, 经纬度, 年月
- **缺失值**: 0（完整数据集）

---

### S4. ERA5 再分析气象数据

- **来源**: https://cds.climate.copernicus.eu
- **获取方式**: CDS API 下载
- **采集脚本**: `crawler/s4_fetch_era5.py`
- **清洗脚本**: `processing/cleaning/clean_s4.py`（NetCDF → CSV）
- **原始规模**: 1,526 MB (3 个 NetCDF 文件)
- **数据格式**: NetCDF (.nc) → CSV
- **时间范围**: 2023-2025
- **许可**: Copernicus 免费，需接受使用条款
- **关键变量**: temperature_2m_K, dewpoint_2m_K, wind_u_10m, wind_v_10m, surface_pressure_Pa
- **跨源关联字段**: 经纬度, 时间
- **缺失值**: 0（完整数据集）

---

### S5. 国家统计局省级卫生指标

- **来源**: https://data.stats.gov.cn/ (stream/esData API)
- **获取方式**: API 调用
- **采集脚本**: `crawler/s5_fetch_gbd.py`
- **清洗脚本**: `processing/cleaning/clean_s5.py`
- **原始规模**: 12 个 CSV 文件, 31,632 行 → 过滤 2023-2025 后 9,486 行
- **数据格式**: CSV
- **时间范围**: 2023-2025
- **许可**: 政府公开数据
- **覆盖领域** (12 个): 医疗卫生机构、卫生人员、每万人口卫生技术人员数、村卫生室、床位、社区卫生服务中心、门诊服务、住院服务、床位利用、乡镇卫生院、新农合
- **关键字段**: province, adcode, year, indicator, value, value_num, domain
- **缺失值**: 2023 缺失 31.7%，2024 缺失 59.6%，2025 缺失 100%（数据未发布，正常）

---

### S6. 国家统计局省级社会经济指标

- **来源**: https://data.stats.gov.cn/ (stream/esData API)
- **获取方式**: API 调用
- **采集脚本**: `crawler/s6_fetch_stats.py`
- **清洗脚本**: `processing/cleaning/clean_s6.py`
- **原始规模**: 35 个 CSV 文件, 195,580 行 → 过滤 2023-2025 后 51,234 行
- **数据格式**: CSV
- **时间范围**: 2023-2025
- **许可**: 政府公开数据
- **覆盖领域** (5 个): GDP与经济增长、就业与工资、地方财政、价格指数、居民生活
- **关键字段**: province, adcode, year, indicator, value, value_num, domain
- **缺失值**: 2023 缺失 47.7%，2024 缺失 52.4%，2025 缺失 95.7%（数据未发布，正常）

---

### S7. 中国人口普查 + World Bank 人口指标

- **来源**: 国家统计局第七次人口普查 + World Bank API
- **获取方式**: 编译 + API
- **采集脚本**: `crawler/s7_fetch_census.py`
- **清洗脚本**: `processing/cleaning/clean_s7.py`
- **原始规模**: 20 KB (2 个 CSV 文件, 297 行) → 清洗后 42 行
- **数据格式**: CSV
- **时间范围**: 2020 (普查) + 2023-2024 (World Bank)
- **许可**: 公开数据
- **内容**: 31 省常住人口(2020)、全国总人口/女性比例/城镇化率/预期寿命
- **关键字段**: province, year, indicator, value, source
- **跨源关联字段**: 省份名
- **缺失值**: 0

---

### S8. 行政区划边界矢量数据

- **来源**: https://geo.datav.aliyun.com/areas_v3/bound/ (阿里云 DataV)
- **获取方式**: REST API 下载
- **采集脚本**: `crawler/s8_fetch_admin_boundary.py`
- **清洗脚本**: `processing/cleaning/clean_s8.py`
- **原始规模**: 32 个 GeoJSON 文件, 4.4 MB → 合并后 4,498 KB, 484 features
- **数据格式**: GeoJSON
- **时间范围**: 静态
- **许可**: 公开数据
- **内容**: 全国边界 + 31 省市级子区域边界
- **关键字段**: adcode, name, level, parent
- **跨源关联字段**: adcode, 行政区划名称
- **缺失值**: name 缺失 0 个（adcode 填充）

---

## 跨源关联设计

| 关联维度 | 涉及数据源 | 关联键 | 说明 |
|---------|-----------|--------|------|
| 空间关联 | S1+S2+S3+S4+S8 | 经纬度 → 行政区划 | Point-in-Polygon 空间 Join |
| 时间关联 | S3+S4+S5+S6 | 年份/月份 | 年度数据对齐 |
| 实体关联 | 所有源 | 省份/城市名称 | 中英文映射表统一命名 |
| 行政区划关联 | S2+S5+S6+S7+S8 | adcode | 12 位行政区划代码 |

---

## 数据质量总结

| 数据源 | Raw 缺失值 | Cleaned 缺失值 | 处理方式 |
|--------|-----------|---------------|---------|
| S2 | telephone 34.3% | 保留 NA | 正常（部分 POI 无电话） |
| S3 | 0 | 0 | 完整数据集 |
| S4 | 0 | 0 | 完整数据集 |
| S5 | 63.7% | 2023: 31.7%, 2024: 59.6%, 2025: 100% | 保留 NA（数据未发布） |
| S6 | 65.3% | 2023: 47.7%, 2024: 52.4%, 2025: 95.7% | 保留 NA（数据未发布） |
| S7 | 0 | 0 | 完整数据集 |
| S8 | name 缺失 0 | 0 | adcode 填充 |

---

## 采集日志

### S2 采集日志

```
[S2] 百度地图 POI 采集 (区县级)
[S2] 检查 API 额度...
  API Key 有效, 额度正常
[S2] 获取区县列表...
  共 2994 个区县

  类型: 医院 (090100)
    [1/2994] 北京 / 医院: +78
    [2/2994] 北京 / 医院: +60
    ...

采集结果: 7,129 条原始 → 去重后 6,809 条
覆盖省份: 25/31 (缺少: 内蒙古、安徽、江西、海南、福建、西藏)
```

### S3 采集日志

```
[S3] 从 Kaggle 下载数据集
  数据集: houjihao/china-capitals-weather-and-air-quality-2023-2026
  下载完成: 1440 KB
  ZIP 内容:
    china_provincial_capitals_daily_weather_air_quality_2023_2026.csv (7043 KB)
    cities.csv (1 KB)
    data_dictionary.csv (1 KB)

[S3] 处理数据: china_provincial_capitals_daily_weather_air_quality_2023_2026.csv
  原始: 40424 行 × 20 列
  城市: 31 个
  时间: 2023-01-01 ~ 2026-07-27
  过滤 2023-2025 后: 33976 行
  缺失值: 0
```

### S4 采集日志

```
[S4] ERA5 气象数据采集
  变量: 2m_temperature, 2m_dewpoint_temperature, 10m_u/v_component_of_wind, surface_pressure
  区域: 中国 [55, 70, 20, 140]
  年份: 2023-2025

  下载 ERA5 单层变量 2023... 完成 (526 MB)
  下载 ERA5 单层变量 2024... 完成 (527 MB)
  下载 ERA5 单层变量 2025... 完成 (533 MB)
  合计: 1,526 MB (3 个 NetCDF 文件)
```

### S5 采集日志

```
[S5] 获取卫生领域列表...
  医疗卫生机构: 16 个指标
  卫生人员: 10 个指标
  每万人口卫生技术人员数: 9 个指标
  村卫生室情况: 7 个指标
  医疗卫生机构床位: 9 个指标
  每万人口医疗机构床位数: 9 个指标
  按床位数分组的社区卫生服务中心: 11 个指标
  医疗卫生机构门诊服务情况: 7 个指标
  医疗卫生机构住院服务情况: 6 个指标
  医院床位利用情况: 8 个指标
  乡镇卫生院医疗服务情况: 4 个指标
  新型农村合作医疗情况: 6 个指标

  共 12 个领域, 96 个指标

[1/12] 医疗卫生机构... → 4960 条
[2/12] 卫生人员... → 3100 条
...
[12/12] 新型农村合作医疗情况... → 1860 条

采集汇总:
  医疗卫生机构                    |   4960 条 | 16 指标
  卫生人员                        |   3100 条 | 10 指标
  每万人口卫生技术人员数           |   2790 条 |  9 指标
  村卫生室情况                    |   2170 条 |  7 指标
  医疗卫生机构床位                |   2790 条 |  9 指标
  每万人口医疗机构床位数           |   2790 条 |  9 指标
  按床位数分组的社区卫生服务中心    |   3410 条 | 11 指标
  医疗卫生机构门诊服务情况         |   2170 条 |  7 指标
  医疗卫生机构住院服务情况         |   1860 条 |  6 指标
  医院床位利用情况                |   2480 条 |  8 指标
  乡镇卫生院医疗服务情况          |   1240 条 |  4 指标
  新型农村合作医疗情况            |   1860 条 |  6 指标
  总计                           |  31630 条 | 96 指标
```

### S6 采集日志

```
[S6] 获取经济领域列表...
  GDP与经济增长: 2 个子领域 (地区生产总值、GDP指数)
  就业与工资: 12 个子领域
  地方财政: 2 个子领域 (财政收入、支出)
  价格指数: 11 个子领域
  居民生活: 8 个子领域

  共 35 个子领域

采集结果:
  GDP与经济增长: 5,580 条
  就业与工资: 58,800 条
  地方财政: 14,880 条
  价格指数: 106,910 条
  居民生活: 26,410 条
  总计: 195,580 条
```

### S7 采集日志

```
[S7] 采集第七次全国人口普查数据...
  七普公报第一号: 2094 字符
  七普公报第二号: 1106 字符
  ...
  分省人口: 31 省份 → census_7_province_population.csv

[S7] 从世界银行获取人口数据...
  total_population: 65 条
  female_pct: 65 条
  urbanization_rate: 65 条
  life_expectancy: 65 条
  总计 264 条 → worldbank_population_china.csv
```

### S8 采集日志

```
[S8] 下载行政区划边界数据...
  china (100000): 35 个子区域
  beijing (110000): 16 个子区域
  tianjin (120000): 16 个子区域
  ...
  xinjiang (650000): 24 个子区域
  共下载 32 个文件, 合计 4.4 MB
```
