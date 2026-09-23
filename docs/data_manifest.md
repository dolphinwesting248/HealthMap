# 数据清单与校验值 (data manifest)

> 由 `scripts/make_manifest.py` 生成；用于核对数据完整性与可复现性。
> MD5 校验值可用于验证重新采集/清洗后的数据与本文档记录的一致性。

## raw/ — 原始数据 (对应采集脚本 crawler/fetch_*.py 的输出)

- 文件数：**69**；合计：**3.1 GB**

| 文件 | 大小 | 行数/要素数 | MD5 |
|---|---|---|---|
| `raw/econ_gdp/nbs_econ_finance.csv` | 1.0 MB | 14880 | dc62f3a1a04e30ce9d2d7a12e4b84942 |
| `raw/econ_gdp/nbs_econ_gdp.csv` | 359.5 KB | 5580 | 9d3dc0e0d2311a160fd28231bc8265bd |
| `raw/econ_income/nbs_econ_income.csv` | 64.7 KB | 930 | 9f97579e838e1de4faa7958eecb783e3 |
| `raw/econ_labor/nbs_econ_labor.csv` | 971.2 KB | 11160 | ffdcfd6ee8078efd2105745ff60ac82e |
| `raw/econ_price/nbs_econ_price.csv` | 8.6 MB | 107880 | 1ad8feb4378dcb84af2be6d01838bb8a |
| `raw/env_air/LICENSE_NOTICE.md` | 640 B | — | 8ce54053360349c7dbe038e6ffb68806 |
| `raw/env_air/README.md` | 1.7 KB | — | 156846a1ba9df5505fe4692aa2b72169 |
| `raw/env_air/china_air_quality_daily.csv` | 5.2 MB | 40424 | c2dd235de28d4a66637ab7aa4b592eaa |
| `raw/env_air/china_provincial_capitals_daily_weather_air_quality_2023_2026.csv` | 6.9 MB | 40424 | ae75de784b7482df63dd3225e4a50975 |
| `raw/env_air/cities.csv` | 1.6 KB | 31 | 97b12e3e2d252d94c3fa0416daf836e8 |
| `raw/env_air/data_dictionary.csv` | 1.4 KB | 20 | 828cbdc26ace4b80817e47a7ea0378a3 |
| `raw/env_air/download_data.ps1` | 3.9 KB | — | 9a51349305fca3277b51373a7e540829 |
| `raw/env_water/china_water_pollution_data.csv` | 531.1 KB | 3000 | 03052a6745a628fbd9b62f1ca915660b |
| `raw/env_weather/era5_single_level_2023.nc` | 525.8 MB | — | (>200MB, 略) size=551341520 |
| `raw/env_weather/era5_single_level_2024.nc` | 526.6 MB | — | (>200MB, 略) size=552175588 |
| `raw/env_weather/era5_single_level_2025.nc` | 532.9 MB | — | (>200MB, 略) size=558777173 |
| `raw/geo_boundary/100000_china.json` | 619.1 KB | — | 498d3f6b1edac6b0f8b63cf28710d68d |
| `raw/geo_boundary/110000_beijing.json` | 107.5 KB | — | eb1d941fa9cf78be5c9d82ca5d612160 |
| `raw/geo_boundary/120000_tianjin.json` | 75.4 KB | — | 3f86d227bf54121edae3b7628173ae3d |
| `raw/geo_boundary/130000_hebei.json` | 78.1 KB | — | 423d1a941ffd88f8bb7b6738b9fb7c30 |
| `raw/geo_boundary/140000_shanxi.json` | 64.7 KB | — | 20f5b044701b3452b438b4090162d730 |
| `raw/geo_boundary/150000_neimenggu.json` | 84.3 KB | — | 873d4f2380578286a7f087ceef89bba4 |
| `raw/geo_boundary/210000_liaoning.json` | 171.6 KB | — | 80409c9754f6d804ba615cf92ffb44e2 |
| `raw/geo_boundary/220000_jilin.json` | 156.5 KB | — | 305d154a96f09321c5c4fcc72852e298 |
| `raw/geo_boundary/230000_heilongjiang.json` | 156.0 KB | — | 399bdb52fa2026847530901b5eed8166 |
| `raw/geo_boundary/310000_shanghai.json` | 88.5 KB | — | 24e202e12184e0f86a14454412ca47ec |
| `raw/geo_boundary/320000_jiangsu.json` | 103.7 KB | — | 24576103cf2662a190ac94443fcbef53 |
| `raw/geo_boundary/330000_zhejiang.json` | 127.9 KB | — | b852623b6c441ed980f465e21b448500 |
| `raw/geo_boundary/340000_anhui.json` | 135.3 KB | — | 3048bcfb84e2f18a1ed5cbe80e9f124e |
| `raw/geo_boundary/350000_fujian.json` | 121.4 KB | — | 399d159dda325d2fe38a63930847f156 |
| `raw/geo_boundary/360000_jiangxi.json` | 129.3 KB | — | 9faeb3f009a6cb5a692411c6330dc0bd |
| `raw/geo_boundary/370000_shandong.json` | 178.4 KB | — | 6ff947900989adb6543917817ed73094 |
| `raw/geo_boundary/410000_henan.json` | 163.4 KB | — | a3fc9fedf058b6f5dd356b4798f63755 |
| `raw/geo_boundary/420000_hubei.json` | 165.5 KB | — | bf36ec41bffe0dcabb2f371112f99446 |
| `raw/geo_boundary/430000_hunan.json` | 186.7 KB | — | a2bdc2c3536d9e6eb647695317b30c9f |
| `raw/geo_boundary/440000_guangdong.json` | 205.0 KB | — | be130c0cb59a48d892042324fe098f76 |
| `raw/geo_boundary/450000_guangxi.json` | 178.5 KB | — | fa10431cf0d604fee722d1721232f81f |
| `raw/geo_boundary/460000_hainan.json` | 36.3 KB | — | 6c03c239ce847de980735eadca36f9b0 |
| `raw/geo_boundary/500000_chongqing.json` | 172.3 KB | — | 6b4d6effa0b2b95cf9a1907573e386ed |
| `raw/geo_boundary/510000_sichuan.json` | 175.2 KB | — | b14195c9ee89ddc5bbf83723c9768f97 |
| `raw/geo_boundary/520000_guizhou.json` | 138.3 KB | — | c5e325de3039fb524207cde03076fe10 |
| `raw/geo_boundary/530000_yunnan.json` | 130.4 KB | — | f76348e1ae9949dad41332d5ba4f3481 |
| `raw/geo_boundary/540000_xizang.json` | 143.4 KB | — | b95ce159e22c9bccd6a563f980edf5d9 |
| `raw/geo_boundary/610000_shaanxi.json` | 76.2 KB | — | 593795f0a30950acdf9803aaa755f6b2 |
| `raw/geo_boundary/620000_gansu.json` | 112.3 KB | — | ccbee3b7d438d0df3d4bb4359f028174 |
| `raw/geo_boundary/630000_qinghai.json` | 104.3 KB | — | 3ac1dc55183bcaafdaf8b76fcc7cf333 |
| `raw/geo_boundary/640000_ningxia.json` | 52.6 KB | — | f5aef5541de36818fd07c70afd40d5a0 |
| `raw/geo_boundary/650000_xinjiang.json` | 127.1 KB | — | 33475a85ff77bef884b3c0b9ecc28c8f |
| `raw/geo_road/china-latest.osm.pbf` | 1.5 GB | — | (>200MB, 略) size=1597621653 |
| `raw/health_resource/medical_poi.csv` | 1.7 MB | 9894 | 6a07c239aba460e13256ee7e99beeab2 |
| `raw/health_resource/progress.json` | 1.7 KB | — | 06eb5d2d8127ece5e6685b9826297a31 |
| `raw/health_service/covid/covid-19-all.csv` | 71.1 MB | 1241952 | bf336b4bb820b124dbe4a51dd546a234 |
| `raw/health_service/nbs_health_乡镇卫生院医疗服务情况.csv` | 86.5 KB | 1240 | b0a505a622c80f178ed8c2fe3610d6fa |
| `raw/health_service/nbs_health_医疗卫生机构.csv` | 279.6 KB | 4960 | f6695338329d935fe3f01eb6827d2720 |
| `raw/health_service/nbs_health_医疗卫生机构住院服务情况.csv` | 147.3 KB | 1860 | ed30ff2e8c91111beacfe5b8b63c2839 |
| `raw/health_service/nbs_health_医疗卫生机构床位.csv` | 187.3 KB | 2790 | 00010c48e52c0f5d0d6a311f42dca357 |
| `raw/health_service/nbs_health_医疗卫生机构门诊服务情况.csv` | 162.5 KB | 2170 | 374318bae2a788986598b3f2260e2595 |
| `raw/health_service/nbs_health_医院床位利用情况.csv` | 145.7 KB | 2480 | cab3bf9bb0d84f157528f4272dafd7fe |
| `raw/health_service/nbs_health_卫生人员.csv` | 179.3 KB | 3100 | 8bdf6dfa851bd331d5c00ac04c3100c7 |
| `raw/health_service/nbs_health_按床位数分组的社区卫生服务中心_站.csv` | 250.9 KB | 3410 | c3b3c0a7175b6711414a542e3067fbc1 |
| `raw/health_service/nbs_health_新型农村合作医疗情况.csv` | 133.4 KB | 1860 | e79643474f18f1da145582a4317a7ab0 |
| `raw/health_service/nbs_health_村卫生室情况.csv` | 139.6 KB | 2170 | f0f48131b076a7d90af453b753f93ceb |
| `raw/health_service/nbs_health_每万人口医疗卫生机构床位数.csv` | 193.2 KB | 2790 | 8853509501cc1687c6b3c0599d752938 |
| `raw/health_service/nbs_health_每万人口卫生技术人员数.csv` | 202.6 KB | 2790 | 36be7826f5b98f3dd23cc887c98a03cf |
| `raw/health_service/who_gho_china_health.csv` | 5.2 KB | 94 | a2e1671ab38e1df3d16e44b0e029a312 |
| `raw/pop_age/nbs_pop_age_structure.csv` | 156.4 KB | 2170 | 624a95b1ab8d30d1382af77975715664 |
| `raw/pop_census/census_7_province_population.csv` | 1.9 KB | 31 | 4a1f11e0f43c1e9dd5c767854ea30cb6 |
| `raw/pop_life_exp/nbs_life_expectancy.csv` | 50.6 KB | 930 | e08511b8ab716daef86541e4aff31784 |
| `raw/pop_wb/worldbank_population_china.csv` | 36.0 KB | 774 | 19b26e66bef666ba3cf7f8eaa8293978 |

## cleaned/ — 清洗后数据 (processing/cleaning/clean_*.py)

- 文件数：**17**；合计：**546.5 MB**

| 文件 | 大小 | 行数/要素数 | MD5 |
|---|---|---|---|
| `cleaned/econ_gdp.csv` | 1.8 MB | 20460 | 454d315bfa53e1685b8acc31284ff16d |
| `cleaned/econ_income.csv` | 86.5 KB | 930 | 01c4209d99fb2aa35690eea310bd1d8d |
| `cleaned/econ_labor.csv` | 1.2 MB | 11160 | 6345a4cf2eceec73e840d5d11200b500 |
| `cleaned/econ_life_expectancy.csv` | 72.4 KB | 930 | 1c4df35d733869696d56e2bd207c5459 |
| `cleaned/econ_pop_age.csv` | 204.6 KB | 2170 | 0692cf0ed00c4476c9879a922034d732 |
| `cleaned/econ_price.csv` | 10.4 MB | 107880 | 491cdafd0d6164a1f4c314d3d7a50e11 |
| `cleaned/env_air_quality.csv` | 3.1 MB | 33976 | 4778c4be532cdab23223bbe9b32c4fd8 |
| `cleaned/env_water_quality.csv` | 531.1 KB | 3000 | 18a33f62560271613e8846f5c6737b97 |
| `cleaned/env_weather_2023.csv` | 120.0 MB | 1393570 | 05417e19a38a5832bc359a4c45f8c253 |
| `cleaned/env_weather_2024.csv` | 120.3 MB | 1397388 | da0a636cb0ce2dad43988b90f07469c4 |
| `cleaned/env_weather_2025.csv` | 120.0 MB | 1393570 | 0d808e45f82f835397d9d5c2e0aee604 |
| `cleaned/geo_boundary.geojson` | 4.4 MB | 484 | b69f8c20840ddd4d8746a4a1754eee5a |
| `cleaned/geo_road_poi.geojson` | 159.1 MB | 564702 | a65141dcd8e44b26242bca4dbdd90416 |
| `cleaned/health_resource_poi.csv` | 2.1 MB | 9893 | b5007790bec38a63e426b34d71342c93 |
| `cleaned/health_service.csv` | 3.3 MB | 31714 | 7108a2eccb2eb97e8b3722025e1670ae |
| `cleaned/pop_census.csv` | 1.9 KB | 31 | 4a1f11e0f43c1e9dd5c767854ea30cb6 |
| `cleaned/pop_wb.csv` | 36.0 KB | 774 | 19b26e66bef666ba3cf7f8eaa8293978 |

## integrated/ — 跨源融合数据 (processing/integrating/q*_*.py)

- 文件数：**7**；合计：**353.2 KB**

| 文件 | 大小 | 行数/要素数 | MD5 |
|---|---|---|---|
| `integrated/q1_environment_health/q1_env_exposure_province.csv` | 26.5 KB | 99 | f4ad0fb794e39e5a0b21dd6ebc3f8f07 |
| `integrated/q1_environment_health/q1_env_health_panel.csv` | 70.5 KB | 316 | d1b8af573164e21c2491f88debda5f18 |
| `integrated/q1_environment_health/q1_health_outcome_province.csv` | 29.8 KB | 279 | d33a0f384fd5e3f49667f731b73c0d10 |
| `integrated/q2_healthcare_access/q2_healthcare_accessibility_city.csv` | 20.8 KB | 363 | 02e47f943248a7ff934ed49b835a3fa2 |
| `integrated/q2_healthcare_access/q2_medical_resource_province.csv` | 41.5 KB | 279 | b5fb8fa945e0590ca09cae19c4ac4ccb |
| `integrated/q3_equity/q3_equity_metrics.csv` | 4.6 KB | 10 | 73de382cf45d587b0f5d3b24f287953c |
| `integrated/q3_equity/q3_equity_panel.csv` | 159.5 KB | 316 | a5b95b56c68115d7b2d382987e2f2254 |

## 汇总

- data/ 三层共 **93** 个文件，合计 **3.7 GB**
- 原始数据总量满足作业要求（≥2GB，单一数据源占比 <80%）
