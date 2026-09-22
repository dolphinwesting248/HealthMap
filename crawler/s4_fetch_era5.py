"""
S4: ERA5 再分析气象数据采集
数据源: https://cds.climate.copernicus.eu

变量说明:
  t2m  = 2m temperature (气温)
  d2m  = 2m dewpoint temperature (露点温度)
  u10  = 10m u-component of wind (风速U分量)
  v10  = 10m v-component of wind (风速V分量)
  sp   = surface pressure (地面气压)

需要 CDS 账号 + ~/.cdsapirc 配置
"""
from pathlib import Path

from config import get_output_dir

# 中国区域边界 [N, W, S, E]
CHINA_AREA = [55, 70, 20, 140]

# ERA5 单层变量（与实际下载对齐）
SURFACE_VARIABLES = [
    "2m_temperature",              # → t2m
    "2m_dewpoint_temperature",     # → d2m
    "10m_u_component_of_wind",     # → u10
    "10m_v_component_of_wind",     # → v10
    "surface_pressure",            # → sp
]


def download_era5_single_level():
    """下载 ERA5 单层地面变量（逐年）"""
    try:
        import cdsapi
    except ImportError:
        print("请先安装: pip install cdsapi")
        print("并配置 ~/.cdsapirc:")
        print("  url: https://cds.climate.copernicus.eu/api")
        print("  key: YOUR_UID:YOUR_API_KEY")
        return

    client = cdsapi.Client()
    for year in range(2023, 2026):
        out = OUTPUT_DIR / f"era5_single_level_{year}.nc"
        if out.exists():
            print(f"  已存在，跳过: {out.name}")
            continue
        print(f"  下载 ERA5 单层变量 {year}...")
        try:
            client.retrieve(
                "reanalysis-era5-single-levels",
                {
                    "product_type": "reanalysis",
                    "variable": SURFACE_VARIABLES,
                    "year": str(year),
                    "month": [f"{m:02d}" for m in range(1, 13)],
                    "day": [f"{d:02d}" for d in range(1, 32)],
                    "time": ["00:00", "06:00", "12:00", "18:00"],
                    "area": CHINA_AREA,
                    "format": "netcdf",
                },
                str(out),
            )
        except Exception as e:
            print(f"    失败 {year}: {e}")


if __name__ == "__main__":
    OUTPUT_DIR = get_output_dir("era5")
    print("[S4] ERA5 气象数据采集")
    print(f"  变量: {', '.join(SURFACE_VARIABLES)}")
    print(f"  区域: 中国 [{', '.join(map(str, CHINA_AREA))}]")
    print(f"  年份: 2023-2025")
    download_era5_single_level()
    print("[S4] 完成！")
