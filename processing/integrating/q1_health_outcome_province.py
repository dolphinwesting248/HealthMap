"""
Q1-Integration: 省级健康结局汇总
输入 (cleaned):
     data/cleaned/health_service.csv    (S5a: 卫生服务过程指标 + 病死率)
     data/cleaned/econ_life_expectancy.csv (预期寿命, 仅 2020)
     data/cleaned/econ_pop_age.csv      (年龄构成/抚养比, 抽样调查年 2016-2024)
     data/cleaned/health_service.csv 内的 WHO 健康结局 (national, domain=WHO)
输出: data/integrated/q1_environment_health/q1_health_outcome_province.csv (省×年宽表)

指标选择说明: 卫生指标无省级粗死亡率/婴儿死亡率 (NBS 分省年度不提供),
用"服务质量代理": 急诊/观察室病死率, 重症抢救成功率 + 寿命/抚养比。WHO 94 条为国家级行 (province=CHN)。
"""
from pathlib import Path

import pandas as pd

PROCESSING_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = PROCESSING_DIR.parent
CLEANED = PROJECT_ROOT / "data" / "cleaned"
OUT_DIR = PROJECT_ROOT / "data" / "integrated" / "q1_environment_health"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "q1_health_outcome_province.csv"


def log(msg):
    print(f"  {msg}", flush=True)


# health_service 中可作健康服务质量的"结局类"指标 → 输出列名
QUALITY_INDS = {
    "医疗卫生机构急诊病死率 (%)": "outcome_er_mortality_rate",
    "医疗卫生机构观察室病死率 (%)": "outcome_obs_mortality_rate",
    "医疗卫生机构危重病人抢救成功率 (%)": "outcome_rescue_success_rate",
    "医疗卫生机构急诊抢救成功率 (%)": "outcome_er_rescue_rate",
    "医院病床使用率 (%)": "outsvc_bed_utilization",
    "医院平均住院日 (日)": "outsvc_avg_los",
    # 服务量/健康负荷代理
    "医疗卫生机构诊疗人次数 (亿人次)": "outsvc_visits_yi",
    "医疗卫生机构门急诊诊疗人次数 (亿人次)": "outsvc_outpatient_yi",
    "医疗卫生机构出院人次数 (万人次)": "outsvc_discharges_wan",
    "医疗卫生机构住院病人手术人次 (万人次)": "outsvc_surgeries_wan",
    "医疗卫生机构每百门急诊入院人次数 (人次)": "outsvc_admission_per_100",
    "医院病床周转次数 (次)": "outsvc_bed_turnover",
    "乡镇卫生院诊疗人次数 (亿人次)": "outsvc_township_visits_yi",
}


def _pivot(df, value_col, agg="mean"):
    """indicator 长表 → 宽表, province×year 上做 mean (大小写: 多年重复指标无)"""
    p = df.pivot_table(index=["province", "year"], columns="indicator",
                       values=value_col, aggfunc=agg)
    p.columns = [c.strip() for c in p.columns]
    return p.reset_index()


def clean():
    print("\n[Q1-Integration] 省级健康结局汇总...")

    hs = pd.read_csv(CLEANED / "health_service.csv", low_memory=False)
    hs = hs[hs["province"] != "CHN"]  # WHO 国家级行剥离, 避免混入省级

    # 服务质量/病死类 → (indicator 移到行, value_num 聚合后 pivot)
    q = hs[hs["indicator"].isin(QUALITY_INDS) & hs["value_num"].notna()]
    q = q.groupby(["province", "year", "indicator"], as_index=False)["value_num"].mean()
    q_pivot = _pivot(q, "value_num")
    q_pivot = q_pivot.rename(columns=QUALITY_INDS)

    # 预期寿命 (2020) 与抚养比 (2016-2024)
    le = pd.read_csv(CLEANED / "econ_life_expectancy.csv")
    le = le[le["value_num"].notna()]
    le_pivot = _pivot(le, "value_num")
    le_pivot = le_pivot.rename(columns={
        "平均预期寿命 (岁)": "outcome_life_expectancy",
        "男性平均预期寿命 (岁)": "outcome_life_expectancy_male",
        "女性平均预期寿命 (岁)": "outcome_life_expectancy_female",
    })

    pa = pd.read_csv(CLEANED / "econ_pop_age.csv")
    pa = pa[pa["value_num"].notna()]
    pa_pivot = _pivot(pa, "value_num")
    pa_pivot = pa_pivot.rename(columns={
        "人口数 (人口抽样调查) (人)": "outcome_age_pop_n",
        "0-14岁人口数 (人口抽样调查) (人)": "outcome_age_pop_0_14",
        "15-64岁人口数 (人口抽样调查) (人)": "outcome_age_pop_15_64",
        "65岁及以上人口数 (人口抽样调查) (人)": "outcome_age_pop_65p",
        "总抚养比 (人口抽样调查) (%)": "outcome_dependency_ratio",
        "少年儿童抚养比 (人口抽样调查) (%)": "outcome_child_dependency_ratio",
        "老年人口抚养比 (人口抽样调查) (%)": "outcome_old_dependency_ratio",
    })

    # 三表合并 (省×年 outer 以保留各表的实际可得年)
    df = (q_pivot.merge(le_pivot, on=["province", "year"], how="outer")
                 .merge(pa_pivot, on=["province", "year"], how="outer"))
    df.to_csv(OUT_FILE, index=False, encoding="utf-8-sig")
    log(f"输出: {len(df)} 省×年 × {len(df.columns)-2} 结局指标 → {OUT_FILE}")


if __name__ == "__main__":
    clean()
