"""数据采集公共配置"""
import os
from pathlib import Path

from dotenv import load_dotenv

# 加载项目根目录的 .env 文件
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# 应用代理设置
HTTP_PROXY = os.getenv("HTTP_PROXY", "")
HTTPS_PROXY = os.getenv("HTTPS_PROXY", "")
if HTTP_PROXY or HTTPS_PROXY:
    os.environ.setdefault("HTTP_PROXY", HTTP_PROXY)
    os.environ.setdefault("HTTPS_PROXY", HTTPS_PROXY)
    PROXIES = {"http": HTTP_PROXY, "https": HTTPS_PROXY}
else:
    PROXIES = None

# API Keys
AMAP_KEY = os.getenv("AMAP_KEY", "")
BAIDU_AK = os.getenv("BAIDU_AK", "")
WAQI_TOKEN = os.getenv("WAQI_TOKEN", "")

# 数据目录
DATA_DIR = PROJECT_ROOT / "data" / "raw"

# HTTP 请求头
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}

# 各数据源输出目录 (S1-S8 编号与 data_sources.md 对应)
OUTPUT_DIRS = {
    "s1_geo_road": DATA_DIR / "geo_road",           # S1: OSM 路网
    "s2_health_resource": DATA_DIR / "health_resource",  # S2: 百度医疗 POI
    "s3_env_air": DATA_DIR / "env_air",             # S3a: 空气质量 (Kaggle)
    "s3_env_water": DATA_DIR / "env_water",         # S3b: 水质量 (Kaggle)
    "s4_env_weather": DATA_DIR / "env_weather",     # S4: ERA5 气象
    "s5_health_service": DATA_DIR / "health_service",    # S5: 省级卫生 + WHO + COVID
    "s6_econ": DATA_DIR / "econ_gdp",               # S6: 省级经济指标 (GDP+财政)
    "s6_econ_price": DATA_DIR / "econ_price",       # S6: 价格指数
    "s6_econ_labor": DATA_DIR / "econ_labor",       # S6: 就业与工资
    "s6_econ_income": DATA_DIR / "econ_income",     # S6: 居民人均可支配收入
    "s6_pop_age": DATA_DIR / "pop_age",             # S6: 年龄构成与抚养比
    "s6_pop_life_exp": DATA_DIR / "pop_life_exp",   # S6: 平均预期寿命
    "s7_pop_census": DATA_DIR / "pop_census",       # S7a: 七普人口
    "s7_pop_wb": DATA_DIR / "pop_wb",               # S7b: World Bank
    "s8_geo_boundary": DATA_DIR / "geo_boundary",   # S8: 行政边界
}


def get_output_dir(name: str) -> Path:
    """获取并创建输出目录"""
    d = OUTPUT_DIRS[name]
    d.mkdir(parents=True, exist_ok=True)
    return d


# 中国主要城市（空气质量和POI采集用）
CHINA_CITIES = [
    # 直辖市
    "beijing", "shanghai", "tianjin", "chongqing",
    # 华北
    "shijiazhuang", "tangshan", "handan", "langfang", "taiyuan", "datong",
    "jinan", "qingdao", "yantai", "weifang",
    # 东北
    "shenyang", "dalian", "changchun", "haerbin",
    # 华东
    "nanjing", "suzhou", "wuxi", "xuzhou",
    "hangzhou", "ningbo", "wenzhou",
    "hefei", "wuhu",
    "fuzhou", "xiamen", "quanzhou",
    "nanchang", "ganzhou",
    # 华中
    "zhengzhou", "luoyang", "wuhan", "yichang",
    "changsha", "zhuzhou",
    # 华南
    "guangzhou", "shenzhen", "dongguan", "foshan", "zhuhai",
    "nanning", "beihai", "haikou",
    # 西南
    "chengdu", "mianyang", "guiyang", "kunming",
    # 西北
    "xian", "lanzhou", "wulumuqi", "xining", "yinchuan", "lasa",
]

# 扩展城市列表（第二批地级市）
CHINA_CITIES_EXTENDED = [
    "baoding", "cangzhou", "chengde", "zhangjiakou", "qinhuangdao",
    "benxi", "anshan", "fushun", "jinzhou", "liaoyang",
    "suihua", "mudanjiang", "jixi",
    "xinyang", "nanyang", "zhoukou", "shangqiu", "xuchang",
    "yueyang", "changde", "yiyang", "hengyang", "chenzhou",
    "shaoguan", "huizhou", "jiangmen", "zhongshan", "yangjiang",
    "liuzhou", "guilin", "wuzhou", "yulin",
    "zunyi", "qujing", "lijiang",
    "baoji", "hanzhong", "xianyang", "weinan",
    "baotou", "hohhot", "ordos",
]

# 中国31个省份
CHINA_PROVINCES = {
    "110000": "beijing", "120000": "tianjin", "130000": "hebei",
    "140000": "shanxi", "150000": "neimenggu",
    "210000": "liaoning", "220000": "jilin", "230000": "heilongjiang",
    "310000": "shanghai", "320000": "jiangsu", "330000": "zhejiang",
    "340000": "anhui", "350000": "fujian", "360000": "jiangxi",
    "370000": "shandong", "410000": "henan", "420000": "hubei",
    "430000": "hunan", "440000": "guangdong", "450000": "guangxi",
    "460000": "hainan", "500000": "chongqing", "510000": "sichuan",
    "520000": "guizhou", "530000": "yunnan", "540000": "xizang",
    "610000": "shaanxi", "620000": "gansu", "630000": "qinghai",
    "640000": "ningxia", "650000": "xinjiang",
}
