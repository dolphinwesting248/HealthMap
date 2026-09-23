# 数据质量检查报告

> 由 `processing/cleaning/quality_check.py` 生成；规则覆盖完整性 / 唯一性 / 有效性（业务规则）/ 一致性（跨源关联）四类。
> 结果：**36 项通过，1 项警告，0 项未通过**（共 37 项）。
> WARN = 源数据固有局限（已定位原因并在分析时规避），FAIL = 处理链缺陷（须修复）。

| 表 | 层次 | 检查项 | 结果 | 说明 |
|---|---|---|---|---|
| health_resource_poi | cleaned | 主键 id 唯一 | ✅ | 重复 0 行 |
| health_resource_poi | cleaned | WGS-84 坐标落在中国境内 | ✅ | 越界 0 行 |
| health_resource_poi | cleaned | BD-09→WGS-84 偏移量在合理范围 (0.0005°~0.05°) | ✅ | 命中率 100.0%, 中位偏移 0.01266° |
| health_resource_poi | cleaned | province 在 31 省标准名单 | ✅ | 异常 0 行: [] |
| health_resource_poi | cleaned | 关键字段缺失率记录 | ✅ | name 0.0%; city 0.0%; telephone 42.1%; tag 100.0% |
| geo_road_poi | cleaned | GeoJSON 结构完整 (FeatureCollection) | ✅ | 564702 features |
| geo_road_poi | cleaned | 抽样 20 万点坐标在中国境内 | ✅ | lon∈[75.2,135.1], lat∈[15.8,53.0] |
| geo_road_poi | cleaned | 医院 POI 数量与文档一致 (2,569) | ✅ | 实际 2569 |
| env_air_quality.csv | cleaned | 日期在声明范围 2023-2025 | ✅ | 实际 2023-2025 |
| env_air_quality.csv | cleaned | pm25 落在物理区间 [0, 1500] µg/m³ | ✅ | 缺失 0.0%, 范围 [0.62, 310.57], 越界 0 |
| env_air_quality.csv | cleaned | pm10 落在物理区间 [0, 2000] µg/m³ | ✅ | 缺失 0.0%, 范围 [0.95, 1803.04], 越界 0 |
| env_air_quality.csv | cleaned | aqi 落在物理区间 [0, 500] 指数 | ⚠️ | 缺失 0.0%, 范围 [24.00, 1958.00], 越界 209 ⚠ 源数据局限: 该 Kaggle 数据集的 US AQI 超出量表上限 500, 且与同日 PM2.5 不自洽; 建议分析时剔除该列越界行或改用 european_aqi_daily_max |
| env_air_quality.csv | cleaned | temp_c 落在物理区间 [-50, 50] °C | ✅ | 缺失 0.0%, 范围 [-27.50, 37.30], 越界 0 |
| env_water_quality.csv | cleaned | 日期在声明范围 2023-2025 | ✅ | 实际 2023-2023 |
| env_water_quality.csv | cleaned | Water_Quality_Index 落在物理区间 [0, 500] 指数 | ✅ | 缺失 0.0%, 范围 [0.00, 99.95], 越界 0 |
| env_water_quality.csv | cleaned | pH 落在物理区间 [0, 14] 无量纲 | ✅ | 缺失 0.0%, 范围 [5.34, 8.76], 越界 0 |
| env_water_quality.csv | cleaned | Dissolved_Oxygen_mg_L 落在物理区间 [0, 20] mg/L | ✅ | 缺失 0.0%, 范围 [1.47, 14.49], 越界 0 |
| env_water_quality.csv | cleaned | pH 在 [0,14] 物理范围 | ✅ | 范围 [5.34, 8.76] |
| health_service | cleaned | 省级行 province 在标准名单 | ✅ | 异常 0 行; WHO 国家级行 94 条 (不适用) |
| health_service | cleaned | year 在 2016-2025 | ✅ | 实际 2016-2025 |
| health_service | cleaned | 非数值 value 均已标记为 NA (缺失语义显式化) | ✅ | 0 行 (0.0%) 为未发布/非数值 |
| econ_gdp | cleaned | value_num 缺失率记录 | ✅ | 18.2% (未出数年份) |
| pop_census | cleaned | 31 省齐备且人口为正 | ✅ | 31 行 |
| q1_env_exposure_province | integrated | 省名与 cleaned 标准一致 (跨源实体关联有效) | ✅ | 异常 0 行; 含台港澳 6 行 (边界 34 省级单元, 属预期) |
| q1_env_exposure_province | integrated | 三源省名归一后可同表连接 (air∩weather) | ✅ | 90 省×年同时有 air 与 ERA5 值 |
| q2_medical_resource | integrated | 每万人床位数在合理区间 (10~200 张) | ✅ | 范围 [42.1, 90.1] |
| q2_medical_resource | integrated | 医院数 ≤ 医疗卫生机构数 (业务逻辑) | ✅ | 违反 0 行 |
| q2_medical_resource | integrated | 派生指标 per10k_beds_calc 与源列自洽 | ✅ | 最大相对偏差 0.0012 |
| q2_accessibility | integrated | 城市主键唯一 | ✅ | 363 城 |
| q2_accessibility | integrated | 路网计算占比记录 (>95%) | ✅ | 99.7% 为 network |
| q2_accessibility | integrated | 最近医院时间均为正值 | ✅ | 范围 [2.6, 1461.7] 分钟 |
| q2_accessibility | integrated | 隐含车速在合理区间 (10~150 km/h) | ✅ | 中位车速 65 km/h, 越界 0 城 |
| q3_equity_metrics | integrated | 所有 Gini 系数落在 [0,1] | ✅ | 11 个基尼指标 |
| q3_equity_metrics | integrated | Theil 分解恒等式 T = Tb + Tw 成立 | ✅ | 最大偏差 1.04e-16 |
| q3_equity_metrics | integrated | 年份覆盖 2016-2025 连续 | ✅ | [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025] |
| q3_equity_panel | integrated | 省×年主键唯一 | ✅ | 316 行, 33 省 |
| q3_equity_panel | integrated | 城市→省均聚合值在城市级值域内 (聚合正确性) | ✅ | 省均范围 [23.3, 111.1] ⊂ 城市级 [1.8, 974.5] |

## 检查规则说明

| 规则类型 | 覆盖内容 |
|---|---|
| 完整性 | 行数、关键字段缺失率（缺失语义已在 cleaned_data.md 显式化：未发布≠测量缺失）|
| 唯一性 | 主键重复（POI id / 城市名 / 省×年）|
| 有效性 | 坐标须落在中国 bbox；pH/床位密度等物理与业务区间；医院数≤机构数；Gini∈[0,1]；隐含车速合理性 |
| 一致性 | 省份名跨源统一；三源省名归一后可同表连接；派生指标与源列自洽；Theil 分解恒等式；城市→省聚合值域 |
