"""
公共清洗工具
"""
import sys
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CLEANED_DIR = PROJECT_ROOT / "data" / "cleaned"

# 确保 cleaned 目录存在
CLEANED_DIR.mkdir(parents=True, exist_ok=True)

# 省份名称统一映射
PROVINCE_NAME_MAP = {
    "北京市": "北京", "天津市": "天津", "河北省": "河北", "山西省": "山西",
    "内蒙古自治区": "内蒙古", "辽宁省": "辽宁", "吉林省": "吉林", "黑龙江省": "黑龙江",
    "上海市": "上海", "江苏省": "江苏", "浙江省": "浙江", "安徽省": "安徽",
    "福建省": "福建", "江西省": "江西", "山东省": "山东", "河南省": "河南",
    "湖北省": "湖北", "湖南省": "湖南", "广东省": "广东", "广西壮族自治区": "广西",
    "海南省": "海南", "重庆市": "重庆", "四川省": "四川", "贵州省": "贵州",
    "云南省": "云南", "西藏自治区": "西藏", "陕西省": "陕西", "甘肃省": "甘肃",
    "青海省": "青海", "宁夏回族自治区": "宁夏", "新疆维吾尔自治区": "新疆",
    # 英文名
    "Beijing": "北京", "Tianjin": "天津", "Hebei": "河北", "Shanxi": "山西",
    "Inner Mongolia": "内蒙古", "Liaoning": "辽宁", "Jilin": "吉林",
    "Heilongjiang": "黑龙江", "Shanghai": "上海", "Jiangsu": "江苏",
    "Zhejiang": "浙江", "Anhui": "安徽", "Fujian": "福建", "Jiangxi": "江西",
    "Shandong": "山东", "Henan": "河南", "Hubei": "湖北", "Hunan": "湖南",
    "Guangdong": "广东", "Guangxi": "广西", "Hainan": "海南", "Chongqing": "重庆",
    "Sichuan": "四川", "Guizhou": "贵州", "Yunnan": "云南", "Tibet": "西藏",
    "Shaanxi": "陕西", "Gansu": "甘肃", "Qinghai": "青海", "Ningxia": "宁夏",
    "Xinjiang": "新疆",
}

# 城市→省份映射
CITY_PROVINCE = {
    "石家庄": "河北", "唐山": "河北", "邯郸": "河北", "保定": "河北", "廊坊": "河北",
    "秦皇岛": "河北", "沧州": "河北", "承德": "河北", "张家口": "河北",
    "太原": "山西", "大同": "山西", "阳泉": "山西", "晋城": "山西", "晋中": "山西",
    # 省会补全 (此前遗漏, 导致 S2 POI 的 province 落成城市名)
    "呼和浩特": "内蒙古", "南昌": "江西", "合肥": "安徽", "福州": "福建",
    "海口": "海南", "拉萨": "西藏",
    "济南": "山东", "青岛": "山东", "烟台": "山东", "潍坊": "山东", "淄博": "山东",
    "济宁": "山东", "东营": "山东", "菏泽": "山东", "日照": "山东",
    "沈阳": "辽宁", "大连": "辽宁",
    "长春": "吉林", "哈尔滨": "黑龙江",
    "无锡": "江苏", "常州": "江苏", "徐州": "江苏", "苏州": "江苏", "南京": "江苏",
    "杭州": "浙江", "温州": "浙江", "宁波": "浙江",
    "郑州": "河南", "洛阳": "河南", "许昌": "河南", "信阳": "河南",
    "武汉": "湖北", "宜昌": "湖北", "十堰": "湖北", "襄阳": "湖北",
    "长沙": "湖南", "株洲": "湖南", "岳阳": "湖南",
    "广州": "广东", "深圳": "广东", "东莞": "广东", "佛山": "广东",
    "珠海": "广东", "中山": "广东", "韶关": "广东", "惠州": "广东",
    "南宁": "广西", "北海": "广西",
    "成都": "四川", "绵阳": "四川",
    "贵阳": "贵州", "昆明": "云南",
    "西安": "陕西", "兰州": "甘肃", "乌鲁木齐": "新疆",
    "西宁": "青海", "银川": "宁夏", "石嘴山": "宁夏",
}


def normalize_province(name):
    """统一省份名称，支持城市名→省份映射"""
    if not name or not isinstance(name, str):
        return name
    name = name.strip()

    # 直接匹配省份名
    if name in PROVINCE_NAME_MAP:
        return PROVINCE_NAME_MAP[name]

    # 去掉"市"后缀再匹配
    if name.endswith("市"):
        short = name[:-1]
        if short in PROVINCE_NAME_MAP:
            return PROVINCE_NAME_MAP[short]
        if short in CITY_PROVINCE:
            return CITY_PROVINCE[short]

    # 直接匹配城市名
    if name in CITY_PROVINCE:
        return CITY_PROVINCE[name]

    return name


def log(msg):
    """打印清洗日志"""
    print(f"  {msg}")
