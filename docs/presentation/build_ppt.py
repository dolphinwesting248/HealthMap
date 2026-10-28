# -*- coding: utf-8 -*-
"""HealthMap 项目汇报 PPT 生成（简体中文，16:9，含数据可视化图表与演讲备注）"""
import os
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

BASE = os.path.dirname(os.path.abspath(__file__))
A = lambda name: os.path.join(BASE, "assets", name)

# ------- 配色 -------
PRIMARY = RGBColor(0x16, 0x59, 0x7A)
TEAL    = RGBColor(0x2E, 0x8B, 0x8B)
ORANGE  = RGBColor(0xE8, 0x83, 0x3A)
RED     = RGBColor(0xC0, 0x39, 0x2B)
DARK    = RGBColor(0x25, 0x31, 0x3D)
GRAY    = RGBColor(0x6B, 0x72, 0x80)
LIGHT   = RGBColor(0xF2, 0xF6, 0xF9)
BORDER  = RGBColor(0xC9, 0xD6, 0xDF)
WHITE   = RGBColor(0xFF, 0xFF, 0xFF)
GREEN   = RGBColor(0x1F, 0x7A, 0x4D)
FONT = "PingFang SC"

W, H = 13.333, 7.5
MX = 0.55
TOTAL = 16

prs = Presentation()
prs.slide_width = Emu(int(W * 914400))
prs.slide_height = Emu(int(H * 914400))
BLANK = prs.slide_layouts[6]

def _set_ea(run):
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn('a:ea'))
    if ea is None:
        ea = rPr.makeelement(qn('a:ea'), {})
        rPr.append(ea)
    ea.set('typeface', FONT)

def style(run, size=14, bold=False, color=DARK, font=FONT):
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    _set_ea(run)

def textbox(slide, x, y, w, h, lines, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
            space_after=4, line_spacing=1.12):
    """lines: list of (text, size, bold, color) 或 list of list(runs)"""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space_after)
        p.line_spacing = line_spacing
        runs = ln if isinstance(ln, list) else [ln]
        for spec in runs:
            t, sz, b, c = spec
            r = p.add_run(); r.text = t
            style(r, sz, b, c)
    return tb

def rect(slide, x, y, w, h, fill=LIGHT, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
         radius=0.12, shadow=False):
    sp = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        try:
            sp.adjustments[0] = radius
        except Exception:
            pass
    if fill is None:
        sp.fill.background()
    else:
        sp.fill.solid(); sp.fill.fore_color.rgb = fill
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = line; sp.line.width = Pt(1.0)
    sp.shadow.inherit = False
    return sp

def pic(slide, path, x, y, w=None, h=None):
    iw, ih = Image.open(path).size
    aspect = ih / iw
    if w is None and h is not None:
        w = h / aspect
    if h is None and w is not None:
        h = w * aspect
    return slide.shapes.add_picture(path, Inches(x), Inches(y), Inches(w), Inches(h)), w, h

def new_slide():
    return prs.slides.add_slide(BLANK)

def title(slide, txt, sub=None):
    textbox(slide, MX, 0.30, W - 2*MX, 0.62, [(txt, 25, True, DARK)])
    rect(slide, MX, 0.98, 0.92, 0.055, fill=ORANGE, shape=MSO_SHAPE.RECTANGLE)
    if sub:
        textbox(slide, MX, 1.10, W - 2*MX, 0.34, [(sub, 12.5, False, GRAY)])

def footer(slide, n):
    textbox(slide, MX, 7.13, 6.0, 0.3,
            [("HealthMap · 多源数据融合分析项目汇报", 9, False, GRAY)])
    textbox(slide, W - MX - 1.2, 7.13, 1.2, 0.3, [(f"{n:02d} / {TOTAL}", 9, False, GRAY)],
            align=PP_ALIGN.RIGHT)

def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text

def card(slide, x, y, w, h, fill=LIGHT, line=BORDER):
    return rect(slide, x, y, w, h, fill=fill, line=line)

def bullets(slide, x, y, w, items, size=13, gap=6, marker_color=ORANGE):
    """items: list of (bold_head, rest)"""
    lines = []
    for head, rest in items:
        runs = [("▪ ", size, True, marker_color)]
        if head:
            runs.append((head, size, True, DARK))
        runs.append((rest, size, False, DARK))
        lines.append(runs)
    return textbox(slide, x, y, w, H - y - 0.4, lines, space_after=gap, line_spacing=1.18)

def takeaway(slide, x, y, w, text, fill=PRIMARY):
    rect(slide, x, y, w, 0.62, fill=fill)
    textbox(slide, x + 0.22, y + 0.06, w - 0.44, 0.5,
            [("★ ", 13, True, RGBColor(0xFF, 0xD9, 0x66)), (text, 12.5, True, WHITE)],
            anchor=MSO_ANCHOR.MIDDLE, space_after=0)

def stat_block(slide, x, y, w, big, small, big_color=PRIMARY, big_size=26):
    rect(slide, x, y, w, 1.28, fill=LIGHT, line=BORDER)
    textbox(slide, x + 0.14, y + 0.14, w - 0.28, 0.62,
            [(big, big_size, True, big_color)], align=PP_ALIGN.CENTER)
    textbox(slide, x + 0.1, y + 0.78, w - 0.2, 0.44,
            [(small, 11, False, GRAY)], align=PP_ALIGN.CENTER, line_spacing=1.05)

# ================================================================ S1 封面
s = new_slide()
rect(s, 0, 0, W, 2.6, fill=PRIMARY)
rect(s, 0, 2.6, W, 0.07, fill=ORANGE)
textbox(s, MX + 0.25, 0.55, 9.0, 1.0, [("HealthMap", 44, True, WHITE)])
textbox(s, MX + 0.25, 1.62, 10.5, 0.7,
        [("城市环境、医疗资源与居民健康 —— 多源数据融合分析 · 项目汇报", 19, False, WHITE)])
# 右侧大数字卡
card(s, 9.35, 3.15, 3.35, 3.4)
textbox(s, 9.55, 3.38, 2.95, 3.0, [
    [("8", 40, True, PRIMARY), (" 个独立数据源", 15, True, DARK)],
    [("3", 40, True, PRIMARY), (" 大研究问题", 15, True, DARK)],
    [("31", 40, True, PRIMARY), (" 省 · ", 15, True, DARK), ("363", 40, True, PRIMARY), (" 城", 15, True, DARK)],
    [("93", 40, True, PRIMARY), (" 文件 ≈ 3.7GB", 15, True, DARK)],
], space_after=8)
textbox(s, MX + 0.25, 3.35, 8.3, 2.6, [
    ("核心命题：城市环境质量、医疗资源分布与居民健康之间，", 15.5, False, DARK),
    ("存在怎样的空间关联与公平性差异？", 15.5, False, DARK),
    ("", 8, False, DARK),
    ("方法路线：多源采集 → 清洗 → 跨源融合（空间 / 时间 / 实体）→ 实证分析", 13.5, False, GRAY),
    ("技术栈：Python · GeoPandas · PySAL · statsmodels · osmium", 13.5, False, GRAY),
], space_after=8)
textbox(s, MX + 0.25, 6.55, 11.0, 0.4,
        [("GitHub：github.com/dolphinwesting248/HealthMap      2026 年 10 月", 12, False, GRAY)])
footer(s, 1)
notes(s, "各位老师、同学好。今天由我代表小组汇报 HealthMap 项目。这是一个围绕“城市环境质量、医疗资源分布与居民健康”三个核心议题的多源数据融合分析项目。我们从 8 个独立数据源采集了约 3.7GB、93 个文件的数据，覆盖 31 个省份和 363 个城市，通过空间、时间、实体三种关联维度做跨源融合，再围绕三大研究问题展开实证分析。下面我将从项目概述、数据体系、分析结果、数据质量、协作机制五个部分展开。")

# ================================================================ S2 目录
s = new_slide()
title(s, "汇报目录")
items = [
    ("01", "项目概述", "核心研究问题 Q1 / Q2 / Q3 与总体思路"),
    ("02", "数据体系", "8 个数据源、流水线与跨源融合"),
    ("03", "分析结果", "Q1 环境与健康 · Q2 资源与可达性 · Q3 公平性"),
    ("04", "数据质量与验证", "质量规则、空间关联验证与已知局限"),
    ("05", "协作机制", "分支工作流、数据分发与文档规范"),
    ("06", "总结与展望", "结论、局限与后续可视化计划"),
]
for i, (num, t, d) in enumerate(items):
    r, c = divmod(i, 2)
    x = MX + c * 6.25
    y = 1.55 + r * 1.75
    card(s, x, y, 5.95, 1.45)
    textbox(s, x + 0.3, y + 0.22, 1.0, 1.0, [(num, 28, True, ORANGE)])
    textbox(s, x + 1.35, y + 0.24, 4.4, 1.0, [(t, 17, True, DARK), (d, 11.5, False, GRAY)], space_after=4)
footer(s, 2)
notes(s, "汇报分六个部分：先介绍项目概述和三大研究问题；第二部分讲数据体系，包括 8 个数据源和数据处理流水线；第三部分是今天的重点，Q1 到 Q3 的分析结果，全部配了数据可视化；第四部分讲数据质量与验证；第五部分介绍团队协作机制；最后是总结与展望。")

# ================================================================ S3 项目概述
s = new_slide()
title(s, "项目概述：三大核心研究问题",
      "从 8 个独立数据源采集多维数据，通过空间、时间、实体三种关联维度进行跨源融合分析")
qs = [
    ("Q1", "环境 × 健康", "城市环境质量（空气质量、水质量、气象）是否与居民健康结局存在空间关联？", PRIMARY),
    ("Q2", "资源 × 可达性", "医疗资源（机构 POI、床位、人员）的空间分布是否与就医可达性、区域经济发展相关？", TEAL),
    ("Q3", "公平性", "不同地区医疗服务供给的公平性如何？环境与经济因素如何共同影响健康不平等？", ORANGE),
]
for i, (tag, t, d, c) in enumerate(qs):
    x = MX + i * 4.18
    card(s, x, 1.75, 3.92, 2.5)
    rect(s, x, 1.75, 3.92, 0.14, fill=c, shape=MSO_SHAPE.RECTANGLE)
    textbox(s, x + 0.28, 2.05, 3.4, 2.1, [
        [(tag + "  ", 24, True, c), (t, 16, True, DARK)],
        (d, 12, False, DARK),
    ], space_after=8, line_spacing=1.2)
stat_block(s, MX, 4.62, 2.95, "8 源", "独立数据源\nOSM / 百度 / ERA5 / 国家数据平台 等")
stat_block(s, MX + 3.13, 4.62, 2.95, "93 文件", "原始数据规模约 3.7GB\nMD5 清单校验")
stat_block(s, MX + 6.26, 4.62, 2.95, "7 集成集", "清洗后 15 个数据集\n跨源融合为 7 个分析数据集")
stat_block(s, MX + 9.39, 4.62, 2.95, "363 城", "城市级就医可达性快照\n覆盖 31 个省级行政区")
takeaway(s, MX, 6.25, W - 2*MX, "项目定位：不是单一数据集分析，而是一套“采集 → 清洗 → 融合 → 实证”可复现的完整数据工程")
footer(s, 3)
notes(s, "项目围绕三个研究问题展开。Q1 关注环境质量与健康的空间关联：空气质量、水质、气象条件是否与居民健康结局在空间上相关。Q2 关注医疗资源：床位、人员、机构的空间分布是否与就医可达性和区域经济水平相关。Q3 关注公平性：地区间医疗服务供给是否公平，环境和经济因素如何共同影响健康不平等。支撑这三个问题的是 8 个独立数据源、93 个文件约 3.7GB 的原始数据，经清洗与融合形成 7 个集成数据集，覆盖 31 省 363 城。强调一点：本项目是一套可复现的完整数据工程，而不只是某一次数据分析。")

# ================================================================ S4 数据体系总览
s = new_slide()
title(s, "数据体系总览：8 个独立数据源",
      "矢量、栅格、结构化、统计四类数据互补；数据经 GitHub Release 分发，仓库不含数据本体")
p, pw, ph = pic(s, A("data_sources.png"), MX, 1.62, w=7.55)
right_x = MX + pw + 0.35
bullets(s, right_x, 1.75, W - right_x - MX, [
    ("地理空间底座：", "S1 OSM 路网（1.5GB）+ S8 行政区划边界，支撑 Point-in-Polygon 空间关联"),
    ("医疗资源：", "S2 百度地图 9 类医疗机构 POI，8,005 条（BD-09→WGS-84 坐标修复）"),
    ("环境气象：", "S3 空气/水质（Kaggle）+ S4 ERA5 再分析（1.6GB NetCDF）"),
    ("健康经济人口：", "S5 国家数据平台卫生指标 + S6 省级经济 + S7 七普/世行人口"),
    ("分发方式：", "数据不入 git，经 Release（data-v1）发布，融合数据仅 142KB 即可开工"),
], size=12.5, gap=10)
takeaway(s, MX, 6.25, W - 2*MX, "多源异构 + 跨度互补：省级面板最长 10 年，环境数据 2023–2025，可达性为 363 城单点快照")
footer(s, 4)
notes(s, "这一页是 8 个数据源的全景。横轴是对数刻度，否则从 39KB 到 1.6GB 没法画在一张图上。可以看到数据形态非常异构：有 OSM 路网和行政区划这样的矢量底座，有 ERA5 这样的科研栅格，有百度 POI 这样的结构化数据，还有国家数据平台的统计数据。它们在领域上互补：路网和边界提供空间底座，POI 提供医疗资源点位，环境和气象提供暴露数据，健康、经济、人口提供结局和控制变量。另外说明分发方式：数据不进 git 仓库，而是通过 GitHub Release 发布，做分析只需要下载 142KB 的融合数据包。")

# ================================================================ S5 数据流水线
s = new_slide()
title(s, "数据流水线：从 8 源到三大研究问题",
      "空间关联（严格 Point-in-Polygon）· 时间关联（年份 / 日期）· 实体关联（省份 / 城市名映射）")
pic(s, A("pipeline.png"), (W - 9.2) / 2, 1.62, w=9.2)
takeaway(s, MX, 6.32, W - 2*MX, "可复现性保障：每一层都有对应脚本与文档；文件清单 + MD5 校验确保数据版本可追溯")
footer(s, 5)
notes(s, "这是数据的全景流水线。第一层是 8 个数据源的采集脚本；第二层清洗层，把原始数据规整成 15 个清洗数据集，这里有两个代表性工作：一是百度坐标 BD-09 到 WGS-84 的转换修复，二是用 osmium 做路网预过滤，把处理时间从 70 分钟降到 12 秒；第三层融合层，通过严格的点在多边形内判定加上时间、实体关联，产出 7 个面向研究问题的融合数据集；最右侧的质量保障贯穿全流程：4 类规则 36 项检查、93 个文件的清单和 MD5 校验。所有环节都有脚本和文档，保证可复现。")

# ================================================================ S6 Q1
s = new_slide()
title(s, "Q1 · 环境质量与居民健康：粗相关并不稳健",
      "31 省 × 2023–2024 面板（n=62）；结局变量：急诊病死率等")
p, pw, ph = pic(s, A("pm25.png"), MX, 1.65, w=5.9)
right_x = MX + pw + 0.35
bullets(s, right_x, 1.75, W - right_x - MX, [
    ("现状：", "31 省 PM2.5 年均值 40.3 / 39.3 / 44.7 µg/m³，连续三年高于国家二级标准（35）"),
    ("粗相关：", "r(PM2.5, 急诊病死率) ≈ +0.21（n=62），方向合理但偏弱"),
    ("TWFE 面板回归：", "加入省 / 年固定效应后系数 -0.0008（p=0.27）—— 粗相关被固定效应吸收"),
    ("分位数回归：", "P25 处边缘显著（p=0.084），中位数以上效应发散"),
    ("空间叙事：", "2024 年 PM2.5 的 LISA 显示京津冀高-高聚集显著，是可视化高价值点"),
], size=12.5, gap=9)
takeaway(s, MX, 6.25, W - 2*MX, "方法启示：简单相关会被内生变化解释掉 —— 结论必须建立在面板与空间方法之上")
footer(s, 6)
notes(s, "先看 Q1。左图是 31 省 PM2.5 年均值，三年分别是 40.3、39.3、44.7 微克每立方米，全部高于国家二级标准 35，更远高于 WHO 的 5。粗看 PM2.5 和急诊病死率的的相关系数是正 0.21，方向符合直觉。但当我们做双向固定效应面板回归，把省份和年份固定效应都控制住之后，系数变成负 0.0008 且不显著——粗相关被固定效应吸收了。分位数回归也显示中位数以上效应发散。这页想传达的方法论信息是：不做控制的相关分析很容易误导，这正是我们坚持面板和空间方法的原因。补充一点，2024 年 PM2.5 的 LISA 分析显示京津冀存在显著的高-高聚集，这是很有叙事价值的空间发现。")

# ================================================================ S7 Q2 资源与经济
s = new_slide()
title(s, "Q2 · 医疗资源与区域经济：稳定扩张，同向关联",
      "省 × 年面板 n=279（2016–2024）；模型含省 / 年固定效应，标准误按省聚类")
p, pw, ph = pic(s, A("beds_trend.png"), MX, 1.65, w=6.1)
right_x = MX + pw + 0.35
bullets(s, right_x, 1.75, W - right_x - MX, [
    ("主模型：", "每万人床位 ~ log(总收入) + 城乡收入差距 + 省/年固定效应"),
    ("估计结果：", "log(收入) 系数 +46.99；城乡差距系数 -0.0004；面板 R² = 0.9539"),
    ("反向验证：", "log(收入) ~ 床位 的反向回归 R² 高达 0.9967 —— 高 R² 不构成因果证据"),
    ("口径诚实：", "结果未报告 p 值，因此只解读系数方向，不宣称统计显著"),
], size=12.5, gap=9)
takeaway(s, MX, 6.25, W - 2*MX, "九年间每万人床位 +37%（53.2 → 72.7 张）：供给持续扩张，但它是否转化为均衡的获取体验？——见下页")
footer(s, 7)
notes(s, "Q2 的第一块是资源与经济的关系。左图是 2016 到 2024 年每万人床位数，从 53.2 张稳步增长到 72.7 张，累计增长 37%。主回归是双向固定效应面板，样本 279 个省年观测：收入的对数系数是正的 46.99，城乡收入差距系数是负的 0.0004，面板 R² 0.9539。我们同时做了反向回归，R² 高达 0.9967——但要在强调：这么高的 R² 主要来自固定效应，不能作为因果或“稳定协同”的证据。由于结果文件未报告 p 值，我们只解读方向，不宣称显著。这体现了项目对统计口径的克制。那么资源扩张是否转化成了均衡的就医体验？请看下一页。")

# ================================================================ S8 Q2 可达性
s = new_slide()
title(s, "Q2 · 363 城就医可达性：供给扩张 ≠ 均衡体验",
      "城市级单点快照（296/363 城有有效时间值）；30 分钟不可达为操作性口径（缺失计为不可达）")
p, pw, ph = pic(s, A("accessibility.png"), MX, 1.70, w=8.35)
right_x = MX + pw + 0.30
bullets(s, right_x, 1.85, W - right_x - MX, [
    ("中位数 35.3 分钟", "才能到达最近医院"),
    ("P90 达 77.2 分钟", "最大值 1461.7 分钟（边远城市极端值）"),
    ("90.63%", "的城市 30 分钟内无法到达大医院（329/363）"),
], size=12.5, gap=10)
takeaway(s, MX, 6.25, W - 2*MX, "分布明显右偏：边远地区存在极端就医时间，资源扩张未等比例转化为均衡的获取体验")
footer(s, 8)
notes(s, "这一页是城市级可达性。左图在对数刻度下展示最近医院就医时间的分布：中位数 35.3 分钟，四分位距 20.7 到 54.5 分钟，P90 达 77.2 分钟，最大值是惊人的 1461.7 分钟，说明分布严重右偏，边远城市存在极端值。右边环形图：按操作性口径，363 个城市里 329 个——也就是 90.63%——无法在 30 分钟内到达大医院。这里要诚实说明：这个口径把大医院时间缺失的城市也计为不可达，所以它是操作口径，不全是已观测的超时。核心信息是：床位在扩张，但获取体验并不均衡。")

# ================================================================ S9 Q2 空间统计
s = new_slide()
title(s, "Q2 · 空间自相关检验：未发现稳健的聚集证据",
      "296 个有效城市，KNN-4 球面邻接，9,999 次随机置换，随机种子 42")
p, pw, ph = pic(s, A("moran_lisa.png"), MX, 1.70, w=6.5)
right_x = MX + pw + 0.35
bullets(s, right_x, 1.80, W - right_x - MX, [
    ("全局 Moran's I = 0.00233", "（随机化零假设期望 -0.00339）"),
    ("双侧 p_rand = 0.7210", "：不能拒绝“无全局空间自相关”的零假设"),
    ("局部 LISA：", "未校正 p<0.05 有 35 城（HH 41 / LH 52 / LL 146 / HL 57 象限分布）"),
    ("BH-FDR 校正后：", "显著城市为 0 —— 不把未校正候选点称为“确认热点”"),
], size=12.5, gap=9)
takeaway(s, MX, 6.25, W - 2*MX, "严谨性示范：多重检验校正后宁可“无发现”，也不夸大空间聚集结论")
footer(s, 9)
notes(s, "有同学可能会问：就医时间在空间上是不是聚集的？我们做了严格的检验。对 296 个有效城市构造 KNN-4 球面邻接，9999 次随机置换：全局 Moran's I 只有 0.00233，双侧 p 值 0.72，完全没有全局自相关。局部 LISA 的象限分布如图，未校正 p 小于 0.05 的有 35 个城市，但对 296 次局部检验做 BH-FDR 多重比较校正之后，显著城市归零。所以我们的结论是：没有稳健的空间聚集证据。左图特意标注“未校正象限”，避免把探索性结果当成确认热点。这也是项目在统计严谨性上的一个示范：宁可报告无发现，也不夸大结论。")

# ================================================================ S10 Q3 公平性趋势
s = new_slide()
title(s, "Q3 · 公平性年度趋势：全部指标单调改善",
      "q3_equity_metrics（10 年 × 24 指标，省等权口径）；Mann-Kendall 检验 τ = -1.0")
p, pw, ph = pic(s, A("equity_slope.png"), (W - 9.4) / 2, 1.68, w=9.4)
bullets(s, MX + 0.2, 5.15, W - 2*MX - 0.4, [
    ("泰尔分解：", "东 / 中 / 西部之间的结构差距是主要不平等来源，占比 55.9% → 51.9%，缓慢收敛"),
    ("床位公平：", "每万人床位基尼系数稳定在约 0.075，处于稳态公平水平"),
    ("趋势检验：", "收入基尼、P90/P10、泰尔区间占比均严格单调改善（τ = -1.0，p<0.01）"),
], size=13, gap=7)
footer(s, 10)
notes(s, "进入 Q3 公平性。三个斜率图展示 2016 到 2025 的变化：居民收入基尼从 0.191 降到 0.168；P90/P10 从 2.04 降到 1.79，尾部收敛；泰尔指数中东中西部之间的贡献占比从 55.9% 降到 51.9%——这说明省际之间的结构差距是主要的不平等来源，虽然在改善但仍是主体。另外，每万人床位的基尼系数长期稳定在 0.075 左右，床位分布处于稳态公平。Mann-Kendall 趋势检验显示这些指标都是严格单调改善的，τ 达到负 1，叙事非常干净。")

# ================================================================ S11 Q3 地带不平等
s = new_slide()
title(s, "Q3 · 城市级资源分布：西部最不均衡",
      "363 城医院数分布的基尼系数（Lorenz / 地带分解视角）")
p, pw, ph = pic(s, A("zone_gini.png"), MX, 1.75, w=6.3)
right_x = MX + pw + 0.4
bullets(s, right_x, 1.95, W - right_x - MX, [
    ("全国城市级基尼 0.679", "：医院在城市间的分布明显不均"),
    ("地带梯度成立：", "东部 0.574 < 中部 0.664 < 西部 0.727，西部最不均衡"),
    ("这是本分析的“真发现”：", "文档标注为可直引结论，适合 Lorenz 曲线 + 地带表格呈现"),
    ("与 Q2 呼应：", "可达性右偏 + 西部高基尼，共同指向边远地区的双重劣势"),
], size=13, gap=10)
takeaway(s, MX, 6.25, W - 2*MX, "公平性的短板在地带之间：越往西部，医院资源在城市间的集中程度越高")
footer(s, 11)
notes(s, "把公平性下沉到城市级，会发现清晰的地理梯度：全国 363 个城市之间医院数量分布的基尼系数是 0.679，已经相当不均；分地带看，东部 0.574、中部 0.664、西部 0.727——越往西，资源在城市间的集中程度越高。这和上一页的可达性右偏相互呼应：边远地区同时承受“总量少”和“分布更集中”的双重劣势。这是分析文档里明确标注可直接引用的结论。")

# ================================================================ S12 省份分层
s = new_slide()
title(s, "省份分层画像：KMeans 聚类的健康压力分型",
      "2024 横截面，特征维度：资源密度、老龄化压力、可达性、收入（k=3）")
p, pw, ph = pic(s, A("kmeans.png"), (W - 8.4) / 2, 1.66, w=8.4)
bullets(s, (W - 9.6) / 2, 5.35, 9.6, [
    ("高收入高可达组（粤 · 苏 · 浙 · 闽）：", "收入均值约 55k，平均大医院距离约 31km"),
    ("边远低可达组（新 · 藏 · 蒙 · 黔 · 青 · 琼）：", "收入约 31k，距离约 78km —— 收入低且就医远"),
    ("用途：", "作为“健康压力分型”地图的底图叙事，支撑区域差异化政策讨论"),
], size=13, gap=7)
footer(s, 12)
notes(s, "我们对 31 个省做了一个 KMeans 聚类，特征包括资源密度、老龄化压力、可达性和收入四个维度。结果很清晰：第一组是粤苏浙闽，高收入高可达；第二组是新藏蒙黔青琼六个边远省区，收入只有约 31k，平均到大医院的距离却是 78 公里，是东南沿海的 2.5 倍；其余省份处于中间形态。这张分型图可以直接作为报告里“健康压力地图”的叙事底图。")

# ================================================================ S13 数据质量与验证
s = new_slide()
title(s, "数据质量与验证：把局限写在明处",
      "质量检查报告 · 空间关联验证 · 数据清单（MD5）三份文档支撑可复现性")
p, pw, ph = pic(s, A("pip_validation.png"), MX, 1.70, w=6.6)
right_x = MX + pw + 0.35
bullets(s, right_x, 1.80, W - right_x - MX, [
    ("4 类规则 36 项检查：", "完整性 / 唯一性 / 有效性 / 一致性，输出 data_quality_report.md"),
    ("诚实记录局限：", "如 US AQI 越界 209 行，注明为源数据局限而非隐藏"),
    ("融合修正案例：", "珠海海岛 POI 曾被误判为港澳，改严格 PIP 后与源字段 100% 吻合；ERA5 境外格点 55.3% 剔除而非摊派"),
    ("可追溯：", "93 文件清单 + MD5；发现数据问题须改 processing 脚本重跑，禁止手改 CSV"),
], size=12.5, gap=9)
takeaway(s, MX, 6.25, W - 2*MX, "结论：近似方法在气象格点上只有 33% 一致率 —— 严格空间关联是融合质量的分水岭")
footer(s, 13)
notes(s, "数据质量方面我们做了三件事。第一，建立了四类规则 36 项检查的质量报告，包括完整、唯一、有效、一致；发现的问题如实记录，比如 US AQI 有 209 行越界，就写明是源数据局限。第二，对空间关联本身做了验证：左图显示，如果用近似方法——城市名匹配或最近中心——医疗 POI 与严格点在多边形的一致率只有 84.75%，ERA5 气象格点更是只有 33%。所以融合层全面切换成严格 PIP 加多级回退，修正了珠海海岛被误判到港澳的问题，境外的气象格点直接剔除而不是摊派给最近省份。第三，93 个文件全部有清单和 MD5，而且协作规范明确：发现数据问题只能改脚本重跑，不许手改 CSV。")

# ================================================================ S14 协作机制
s = new_slide()
title(s, "协作机制：分支工作流 + 数据分发 + 文档规范",
      "面向分析与可视化成员的标准协作路径（docs/collaboration.md）")
# 左：分支工作流
lx, lw = MX, 5.9
textbox(s, lx, 1.55, lw, 0.4, [("① Git 分支工作流", 15, True, PRIMARY)])
steps = [
    ("1", "同步 main，从最新代码开新分支（analysis / viz / docs / fix 前缀）"),
    ("2", "在分支上开发，不在 main 直接改动"),
    ("3", "代码与文档同一个 commit 提交，不留“下次再补文档”"),
    ("4", "push 分支并在 GitHub 上发起 Pull Request"),
    ("5", "复核后合并，删除本地分支，回到 main 同步"),
]
for i, (n, t) in enumerate(steps):
    y = 2.05 + i * 0.92
    rect(s, lx, y, 0.42, 0.42, fill=PRIMARY, shape=MSO_SHAPE.OVAL)
    textbox(s, lx, y + 0.045, 0.42, 0.35, [(n, 14, True, WHITE)], align=PP_ALIGN.CENTER)
    textbox(s, lx + 0.6, y - 0.02, lw - 0.7, 0.85, [(t, 12, False, DARK)], line_spacing=1.1)
# 右上：数据分发
rx, rw = MX + lw + 0.4, W - 2*MX - lw - 0.4
textbox(s, rx, 1.55, rw, 0.4, [("② 数据经 Release 分发", 15, True, PRIMARY)])
rows = [
    ("data_integrated.zip", "142KB", "跨源融合数据（分析主用）", TEAL),
    ("data_cleaned.zip", "117MB", "15 个清洗数据集", TEAL),
    ("data_raw01+02.zip", "2×1.53GB", "8 个原始数据源（核对用）", GRAY),
]
for i, (f, sz, d, c) in enumerate(rows):
    y = 2.05 + i * 0.86
    card(s, rx, y, rw, 0.72, fill=LIGHT, line=BORDER)
    rect(s, rx, y, 0.10, 0.72, fill=c, shape=MSO_SHAPE.RECTANGLE)
    textbox(s, rx + 0.28, y + 0.08, rw - 0.4, 0.6,
            [[(f + "  ", 12.5, True, DARK), (sz, 12, True, c)],
             (d, 10.5, False, GRAY)], space_after=1, line_spacing=1.05)
# 右下：文档规范
textbox(s, rx, 4.85, rw, 0.4, [("③ 文档规范", 15, True, PRIMARY)])
bullets(s, rx + 0.05, 5.28, rw - 0.1, [
    ("", "先读 docs/analysis.md（分析路线总纲）"),
    ("", "每块工作写 docs/analysis_<主题>.md（含局限）"),
    ("", "AI 使用逐条记录到 AI_USAGE.md"),
    ("", "禁止 git add data/；文档与代码同步提交"),
], size=11, gap=3)
footer(s, 14)
notes(s, "协作机制有三块。第一，Git 工作流：任何人不在 main 上直接改，每次工作开新分支，用 analysis、viz、docs、fix 这样的前缀命名，完成后提 PR 复核合并，代码和文档必须在同一个 commit 里。第二，数据分发：因为数据体积大，全部走 GitHub Release，做分析只需要 142KB 的融合数据包，需要细粒度字段再下 117MB 的清洗包，原始数据一般不用下。第三，文档规范：动手前先读分析总纲，每块工作留下别人能复核的专题文档，AI 的使用也逐条记录在 AI_USAGE.md 里，包括 AI 出错被纠正的情况。这套机制保证了多人并行开发时仓库不会乱。")

# ================================================================ S15 总结与展望
s = new_slide()
title(s, "总结与展望")
quads = [
    ("核心结论", PRIMARY, [
        "PM2.5 与健康的粗关联不稳健（TWFE 后消失），空间聚集仅在京津冀等地显著",
        "资源持续扩张（+37%），但 90.63% 城市大医院 30 分钟不可达",
        "公平性指标 2016→2025 单调改善；区间差距是主要来源；西部城市级分布最不均",
    ]),
    ("方法亮点", TEAL, [
        "严格 PIP 空间融合 + 多级回退，量化近似法误差",
        "TWFE / 分位数 / LISA / Mann-Kendall / KMeans 方法链完整",
        "FDR 校正后“无发现”也如实报告",
    ]),
    ("主要局限", RED, [
        "可达性为单点快照，不能做时序面板",
        "预期寿命仅 2020 单年，与环境数据有 3 年时差",
        "全部结论为关联描述，不构成因果识别",
    ]),
    ("后续计划", ORANGE, [
        "城市可达性地图（缺失标缺测，不插补）+ LISA 探索图层",
        "PM2.5 空间插值与聚集地图；泰尔分解堆叠图",
        "COVID 冲击 DiD（post 系数 +0.056, p=0.006）扩展因果分析",
    ]),
]
pos = [(MX, 1.55), (MX + 6.25, 1.55), (MX, 4.15), (MX + 6.25, 4.15)]
for (t, c, items), (x, y) in zip(quads, pos):
    card(s, x, y, 5.95, 2.42)
    rect(s, x, y, 5.95, 0.12, fill=c, shape=MSO_SHAPE.RECTANGLE)
    textbox(s, x + 0.25, y + 0.22, 5.5, 0.4, [(t, 15, True, c)])
    lines = [[("· ", 11.5, True, c), (it, 11.5, False, DARK)] for it in items]
    textbox(s, x + 0.25, y + 0.68, 5.5, 1.7, lines, space_after=4, line_spacing=1.12)
footer(s, 15)
notes(s, "总结四点。结论上：环境与健康的粗关联经固定效应检验后不稳健；医疗资源持续扩张但可达性严重不均；公平性指标十年单调改善，但省际结构差距仍是主体，西部城市级分布最不均衡。方法上：严格空间融合、完整的计量方法链，以及 FDR 校正后如实报告无发现的严谨性。局限上：可达性是单点快照、寿命数据有三年时差、所有结论都止于关联描述。展望上：后续优先做可达性地图和 LISA 探索图层、PM2.5 聚集地图，并把 2020 年 COVID 冲击的 DiD 分析扩展为因果方向的尝试——探索性结果显示 2020 之后急诊病死率系统性抬升了 0.056，p 值 0.006，是很值得深挖的信号。")

# ================================================================ S16 结束页
s = new_slide()
rect(s, 0, 0, W, H, fill=PRIMARY)
rect(s, 0, 3.62, W, 0.06, fill=ORANGE)
textbox(s, 0, 2.35, W, 1.1, [("谢谢聆听 · 欢迎提问", 38, True, WHITE)], align=PP_ALIGN.CENTER)
textbox(s, 0, 3.95, W, 1.6, [
    ("仓库：github.com/dolphinwesting248/HealthMap", 15, False, RGBColor(0xDD, 0xE8, 0xEF)),
    ("数据发布：Releases · tag data-v1（融合数据 142KB 即可复现分析）", 15, False, RGBColor(0xDD, 0xE8, 0xEF)),
    ("核心文档：docs/analysis.md · analysis_q2_focused.md · analysis_q2_spatial.md · collaboration.md", 15, False, RGBColor(0xDD, 0xE8, 0xEF)),
], align=PP_ALIGN.CENTER, space_after=10)
notes(s, "我的汇报到这里。所有数字都来自仓库的分析文档，分析脚本和文档都在 GitHub 上，欢迎复现和指正。谢谢大家，下面进入提问环节。")

out = os.path.join(BASE, "HealthMap项目汇报.pptx")
prs.save(out)
print("PPT saved:", out)
