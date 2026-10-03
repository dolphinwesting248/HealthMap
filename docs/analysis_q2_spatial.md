# Q2 城市医疗可达性的空间自相关分析

## 1. 分析问题

本分析对应 `analysis.md` 第 6.2 节中 Q2 的城市可达性问题：城市最近医院就医时间是否在空间上呈现邻近城市相似的聚集结构？使用全局 Moran's I 和局部 Moran's I (LISA) 分析 296 个有有效 `nearest_hospital_min` 的城市。该分析不生成地图或其他图表。

## 2. 数据与样本

- 城市可达性：`data/integrated/integrated/q2_healthcare_access/q2_healthcare_accessibility_city.csv`
- 城市边界：`data/cleaned/cleaned/geo_boundary.geojson`
- 原始城市记录：363；`nearest_hospital_min` 非缺失观测：296；城市边界与可达性表城市名全部匹配。
- 因变量：`nearest_hospital_min`，最近医院所需时间，单位为分钟。

城市坐标沿用 `processing/integrating/spatial_join.py` 的既有口径：递归展开城市 GeoJSON 多边形顶点，取经度和纬度的算术均值作为城市点位。城市邻接由 `libpysal.weights.KNN` 构造，输入经纬度单位为度、地球半径为 6371.0088 km，球面距离定义与 Haversine KNN 一致。

## 3. 方法

1. 对 296 个有有效就医时间的城市按城市名排序，保证计算顺序稳定；
2. 基于城市点位建立 KNN-4 邻接关系，每城连接最近的 4 个其他城市；权重矩阵按行标准化，每个邻居权重为 1/4；
3. 使用 `esda.Moran` 计算全局 Moran's I，随机置换 9,999 次；全局正态和随机化近似 p 值设置为双侧；
4. 使用 `esda.Moran_Local` 计算局部 Moran's I 与 LISA 象限，随机置换 9,999 次；分别报告未校正 p<0.05 的城市数，以及对 296 项局部检验实施 Benjamini–Hochberg (FDR) 校正后的显著数；
5. 全局与局部检验固定随机种子 42。全局 Esda `p_sim` 是置换分布较小尾伪 p 值，不应误读为双侧 p 值；报告同时列出双侧 `p_rand` 和单尾 `p_sim`。

全局 Moran's I 定义为：

   `I = (n / S0) * [z' W z / (z' z)]`

   其中 `z` 为就医时间减去样本均值后的偏差，`W` 为行标准化空间权重矩阵，`S0` 为权重总和；随机化零假设下的期望值为 `-1/(n-1)`；
当前使用的版本为 `libpysal 4.14.1`、`esda 2.8.1`、`shapely 2.1.2`、`geopandas 1.1.3`。脚本直接使用 PySAL 的 KNN 权重与 Esda 的 Moran/LISA 实现。

## 4. 结果

| 指标 | 结果 |
|---|---:|
| 有效城市数 | 296 |
| 邻居数 k | 4 |
| Moran's I | 0.00233 |
| 随机化零假设期望 I | -0.00339 |
| 正态近似双侧 p 值 (`p_norm`) | 0.8820 |
| 随机化近似双侧 p 值 (`p_rand`) | 0.7210 |
| Esda 置换较小尾伪 p 值 (`p_sim`) | 0.3306 |
| 置换 z 分数 / 正态上尾 p 值 | 0.3563 / 0.3608 |
| 置换次数 | 9,999 |
| 随机种子 | 42 |

Moran's I 接近 0，双侧 `p_rand` = 0.7210，不能拒绝“最近医院就医时间不存在全局空间自相关”的零假设。全局置换 `p_sim` 是较小尾伪 p 值，数值为 0.3306，同样不显著。

`analysis.md` 中原有探索值约为 Moran's I=0.001、p=0.36。I 的差异来自展示精度；p≈0.36 对应本次 Esda 的正态化置换 z 单尾 `p_z_sim`=0.3608，而非双侧 `p_rand`。因此，原探索结论与本次标准包复算在“未发现全局空间自相关”这一判断上相符；完整口径和单双侧定义以本报告为准。

局部 LISA 象限分布为 HH 41 城、LH 52 城、LL 146 城、HL 57 城。未校正的局部伪 p<0.05 有 35 城；对 296 次局部检验做 FDR 校正后显著城市为 0。故本数据没有通过多重检验控制的局部高-高、低-低或空间离群聚集证据；未校正的 35 个候选不作为稳健空间热点解释。

## 5. 输出文件

- 分析脚本：`analysis/q2_healthcare_access/q2_spatial_autocorrelation.py`
- 总体统计结果：`analysis/q2_healthcare_access/q2_accessibility_moran_results.csv`
- 城市级审计结果：`analysis/q2_healthcare_access/q2_accessibility_moran_city_results.csv`，包括城市坐标、就医时间、KNN-4 邻居名单与空间滞后、LISA 值与象限、未校正伪 p 值和 FDR q 值。

运行方式：

```bash
python analysis/q2_healthcare_access/q2_spatial_autocorrelation.py
```

## 6. 解释边界与后续可视化需求

- 可达性数据是单点快照，空间统计反映该快照，不是随时间变化的面板结果；
- Moran's I 与 LISA 依赖 KNN-4 及城市中心点定义；改用其他邻居数或权重矩阵可能得到不同结果；
- 局部检验经过 FDR 校正后没有显著城市，不应把未校正候选点解释为确认热点；
- 空间自相关不是因果识别，城市级分析也不代表省内所有居民的真实出行体验；
- 后续若要可视化，可按城市点位展示 `nearest_hospital_min` 和 LISA 象限；本次只输出制图数据，不生成图表。
