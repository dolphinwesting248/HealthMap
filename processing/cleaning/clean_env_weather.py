"""
S4-Clean: ERA5 气象数据清洗
输入: data/raw/env_weather/era5_single_level_*.nc
输出: data/cleaned/env_weather_*.csv
"""
import xarray as xr
from pathlib import Path

from utils import log

VAR_MAP = {"u10": "wind_u_10m", "v10": "wind_v_10m",
           "d2m": "dewpoint_2m_K", "t2m": "temperature_2m_K", "sp": "surface_pressure_Pa"}


def clean():
    print("\n[S4] 清洗 ERA5 气象数据...")
    raw_dir = Path(__file__).resolve().parent.parent.parent / "data" / "raw" / "env_weather"
    nc_files = sorted(raw_dir.glob("era5_single_level_*.nc"))
    if not nc_files:
        print("  未找到 NetCDF 文件")
        return

    for nc_file in nc_files:
        year = nc_file.stem.split("_")[-1]
        print(f"\n  处理 {nc_file.name}...")
        ds = xr.open_dataset(nc_file)

        # 过滤中国 + 降采样 step=3
        ds = ds.sel(latitude=slice(54, 18), longitude=slice(73, 135))
        ds = ds.isel(latitude=slice(0, None, 3), longitude=slice(0, None, 3))
        ds = ds.drop_vars(["sp", "number", "expver"], errors="ignore")
        ds = ds.rename({k: v for k, v in VAR_MAP.items() if k in ds})
        ds = ds.sel(valid_time=ds.valid_time.dt.hour == 12)

        df = ds.to_dataframe().reset_index()
        df = df.rename(columns={"valid_time": "datetime"})
        df["date"] = df["datetime"].dt.date
        df["year"] = df["datetime"].dt.year
        df["month"] = df["datetime"].dt.month

        out = Path(__file__).resolve().parent.parent.parent / "data" / "cleaned" / f"env_weather_{year}.csv"
        df.to_csv(out, index=False, encoding="utf-8-sig")
        log(f"  {year}: {df.shape[0]:,} 行 → {out.name} ({out.stat().st_size // 1024 // 1024} MB)")
        ds.close()


if __name__ == "__main__":
    clean()
