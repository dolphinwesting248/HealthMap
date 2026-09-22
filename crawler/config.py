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

# 各数据源输出目录
OUTPUT_DIRS = {
    "osm": DATA_DIR / "s1_osm",
    "baidu": DATA_DIR / "s2_baidu",
    "openaq": DATA_DIR / "s3_openaq",
    "era5": DATA_DIR / "s4_era5",
    "gbd": DATA_DIR / "s5_gbd",
    "stats": DATA_DIR / "s6_stats",
    "census": DATA_DIR / "s7_census",
    "admin_boundary": DATA_DIR / "s8_admin_boundary",
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
