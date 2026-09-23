"""
Q1-Integration: 环境×健康 分析面板 (Q3 面板底层也复用)
输入 (integrated + cleaned):
     data/integrated/q1_environment_health/q1_env_exposure_province.csv   (exposure)
     data/integrated/q1_environment_health/q1_health_outcome_province.csv (outcome)
     data/cleaned/econ_income.csv  (居民人均可支配收入, 控制)
输出: data/integrated/q1_environment_health/q1_env_health_panel.csv (省×年 面板)

环境暴露仅 2023-2025 有 (Kaggle 空气/ERA5), 结局在更宽年份 → 保留所有行,
env 列 2016-2022 为 NA 属预期, 分析时按需子集。
"""
from pathlib import Path

import pandas as pd

PROCESSING_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = PROCESSING_DIR.parent
CLEANED = PROJECT_ROOT / "data" / "cleaned"
Q1_DIR = PROJECT_ROOT / "data" / "integrated" / "q1_environment_health"
OUT_FILE = Q1_DIR / "q1_env_health_panel.csv"


def log(msg):
    print(f"  {msg}", flush=True)


def clean():
    print("\n[Q1-Integration] 环境×健康面板构建...")
    exp = pd.read_csv(Q1_DIR / "q1_env_exposure_province.csv")
    out = pd.read_csv(Q1_DIR / "q1_health_outcome_province.csv")
    df = exp.merge(out, on=["province", "year"], how="outer")

    # 收入 (控制变量): 数字化后宽表 pivot
    inc = pd.read_csv(CLEANED / "econ_income.csv")
    inc = inc[inc["value_num"].notna()]
    inc_p = inc.pivot_table(index=["province", "year"], columns="indicator",
                            values="value_num", aggfunc="mean").reset_index()
    inc_p.columns = [c.strip() for c in inc_p.columns]
    ren = {}
    for c in inc_p.columns:
        if "城镇居民人均可支配收入" in c and "货币" not in c:
            ren[c] = "econ_income_urban"
        elif "农村居民人均可支配收入" in c:
            ren[c] = "econ_income_rural"
        elif "全体居民人均可支配收入" in c or "居民人均可支配收入" == c:
            ren[c] = "econ_income_total"
    inc_p = inc_p.rename(columns=ren)
    keep = [c for c in inc_p.columns if c in ("province", "year") or c.startswith("econ_income")]
    df = df.merge(inc_p[keep], on=["province", "year"], how="outer")

    df.to_csv(OUT_FILE, index=False, encoding="utf-8-sig")
    n_prov = df["province"].nunique()
    log(f"输出: {len(df)} 省×年 × {len(df.columns)-2} 列 (省 {n_prov}) → {OUT_FILE}")
    log("提示: env 列仅 2023-2025 有值 (暴露期), 2016-2022 行供历史结局分析")


if __name__ == "__main__":
    clean()
