"""
S4-Fetch: ERA5 气象数据采集
输出: data/raw/env_weather/
"""
from pathlib import Path

from config import get_output_dir


def fetch(output_dir):
    try:
        import cdsapi
    except ImportError:
        print("请先安装: pip install cdsapi")
        print("并配置 ~/.cdsapirc")
        return

    client = cdsapi.Client()
    variables = ["2m_temperature", "2m_dewpoint_temperature",
                 "10m_u_component_of_wind", "10m_v_component_of_wind", "surface_pressure"]

    for year in range(2023, 2026):
        out = output_dir / f"era5_single_level_{year}.nc"
        if out.exists():
            print(f"[S4] {year} 已存在，跳过")
            continue
        print(f"[S4] 下载 {year}...")
        try:
            client.retrieve(
                "reanalysis-era5-single-levels",
                {
                    "product_type": "reanalysis",
                    "variable": variables,
                    "year": str(year),
                    "month": [f"{m:02d}" for m in range(1, 13)],
                    "day": [f"{d:02d}" for d in range(1, 32)],
                    "time": ["00:00", "06:00", "12:00", "18:00"],
                    "area": [55, 70, 20, 140],
                    "format": "netcdf",
                },
                str(out),
            )
            print(f"[S4] {year} 完成: {out.stat().st_size // 1024 // 1024} MB")
        except Exception as e:
            print(f"[S4] {year} 失败: {e}")


if __name__ == "__main__":
    OUTPUT_DIR = get_output_dir("s4_env_weather")
    fetch(OUTPUT_DIR)
