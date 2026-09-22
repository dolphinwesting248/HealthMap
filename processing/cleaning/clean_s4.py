"""
S4 清洗: ERA5 再分析气象数据
"""
import pandas as pd
import xarray as xr
from pathlib import Path

from utils import CLEANED_DIR, log

RAW_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "raw" / "s4_era5"

VAR_MAP = {
    "t2m": "temperature_2m_K",
    "d2m": "dewpoint_2m_K",
    "u10": "wind_u_10m",
    "v10": "wind_v_10m",
    "sp": "surface_pressure_Pa",
}


def clean_s4():
    print("\n[S4] 清洗 ERA5 气象数据...")

    nc_files = sorted(RAW_DIR.glob("era5_single_level_*.nc"))
    if not nc_files:
        log("未找到 NetCDF 文件")
        return

    log(f"找到 {len(nc_files)} 个 NetCDF 文件")

    for nc_file in nc_files:
        year = nc_file.stem.split("_")[-1]
        print(f"\n  处理 {nc_file.name}...")

        ds = xr.open_dataset(nc_file)
        log(f"  维度: {dict(ds.sizes)}")
        log(f"  变量: {list(ds.data_vars)}")

        # 重命名变量
        rename_map = {k: v for k, v in VAR_MAP.items() if k in ds.data_vars}
        ds = ds.rename(rename_map)

        # 取每天 12:00 的数据
        try:
            ds_daily = ds.sel(valid_time=ds.valid_time.dt.hour == 12)
        except Exception:
            ds_daily = ds

        # 转为 DataFrame
        df = ds_daily.to_dataframe().reset_index()
        df = df.rename(columns={"valid_time": "datetime"})

        if "datetime" in df.columns:
            df["date"] = pd.to_datetime(df["datetime"]).dt.date
            df["year"] = pd.to_datetime(df["datetime"]).dt.year
            df["month"] = pd.to_datetime(df["datetime"]).dt.month

        # 缺失值检查
        numeric_cols = [c for c in df.columns if c in VAR_MAP.values()]
        log(f"  行数: {df.shape[0]}, 变量: {numeric_cols}")
        missing = df[numeric_cols].isnull().sum()
        total_missing = missing.sum()
        if total_missing > 0:
            log(f"  缺失值: {total_missing} 个")
            for col in numeric_cols:
                n = missing[col]
                if n > 0:
                    log(f"    {col}: {n} 缺失 ({n/len(df)*100:.1f}%)")
        else:
            log(f"  缺失值: 0 (完整数据)")

        # 保存
        out = CLEANED_DIR / f"s4_era5_{year}.csv"
        df.to_csv(out, index=False, encoding="utf-8-sig")
        log(f"  输出: {df.shape[0]} 行 → {out} ({out.stat().st_size // 1024 // 1024} MB)")
        ds.close()


if __name__ == "__main__":
    clean_s4()
