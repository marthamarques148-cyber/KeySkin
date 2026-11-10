# -*- coding: utf-8 -*-
"""
KeySkin 知识库（数据层 · 用户可自由调整）

这是整个项目的「大脑数据」。想加风格、改词意、加同义词、加冲突规则，
**只改这个文件即可**，引擎逻辑不用动。

────────────────────────────────────────────────────────
【怎么改？一眼看懂】
1. 加一个新风格：在 STYLE_PRESETS 里加一段（见底部示例）。
2. 让某个中文词被识别：在对应 MAP（颜色/材质/光效…）里加 "中文": "英文"。
3. 加同义词（小白爱说的口头禅）：在 ALIASES 里加 "口头禅": ("维度", "规范英文")。
4. 加一条"互相矛盾"的规则：在 CONTRADICTIONS 里加一对 ((维度, 值), (维度, 值))。
5. 否定词想增减：改 NEG_HARD / NEG_SOFT。
────────────────────────────────────────────────────────
"""

# ---------------------------------------------------------------------------
# 1) 维度词表：中文关键词 → 英文属性（用于拼进 prompt）
#    注意：尽量用「完整词」做键，避免子串误判（如 "黄" 误吞 "黄金"）。
# ---------------------------------------------------------------------------

# 风格：中文片段 → 英文风格键（键必须存在于 STYLE_PRESETS）
STYLE_MAP = {
    "赛博朋克": "cyberpunk",
    "赛博": "cyberpunk",
    "蒸汽波": "vaporwave",
    "少女": "kawaii",
    "可爱": "kawaii",
    "卡哇伊": "kawaii",
    "极简": "minimal",
    "简约": "minimal",
    "复古": "retro",
    "怀旧": "retro",
    "自然": "nature",
    "森系": "nature",
    "国风": "chinese",
    "古风": "chinese",
    "中国风": "chinese",
    "暗黑": "gothic",
    "哥特": "gothic",
    "科技": "tech",
    "未来": "tech",
    "梦核": "dreamcore",
    "梦幻": "dreamcore",
    "花哨": "ornate",
    "繁复": "ornate",
    "华丽": "ornate",
    "性冷淡": "minimal",
}

# 颜色：中文 → 英文
COLOR_MAP = {
    "马卡龙": "macaron pastel",
    "莫兰迪": "morandi muted",
    "彩虹": "rainbow",
    "霓虹": "neon",
    "黄金": "gold",          # 放在 "黄" 之前（最长匹配优先），避免 "黄金" 被误判成 "黄"
    "粉": "pink",
    "红": "red",
    "蓝": "blue",
    "紫": "purple",
    "青": "cyan",
    "绿": "green",
    "金色": "gold",
    "银色": "silver",
    "黑": "black",
    "白": "white",
    "橙": "orange",
    "黄": "yellow",
    "灰": "gray",
    "酒红": "wine red",
    "天蓝": "sky blue",
    "嫩绿": "light green",
}

# 材质
MATERIAL_MAP = {
    "亚克力": "acrylic",
    "铝合金": "aluminum",
    "金属": "metal",
    "木质": "wood",
    "木": "wood",
    "硅胶": "silicone",
    "玻璃": "glass",
    "碳纤维": "carbon fiber",
    "皮革": "leather",
    "大理石": "marble",
    "塑料": "matte plastic",
    "原木": "wood",
    "透明": "transparent",
}

# 光效：值必须是「完整光效描述」，模板不会再加 "lighting" 后缀
LIGHTING_MAP = {
    "rgb": "RGB backlighting",
    "发光": "glowing",
    "灯": "backlit",
    "镜面": "glossy reflective lighting",
    "磨砂": "frosted matte lighting",
    "哑光": "matte soft lighting",
    "透亮": "translucent glowing",
    "流光": "flowing light",
    "霓虹光": "neon glow",
    "柔光": "soft glow",
}

# 键帽形状
SHAPE_MAP = {
    "圆角": "rounded keycaps",
    "方形": "square keycaps",
    "球形": "spherical keycaps",
    "梯形": "sculpted keycaps",
    "扁平": "flat keycaps",
    "复古球": "vintage spherical keycaps",
    "矮轴": "low profile keycaps",
}

# 背景
BG_MAP = {
    "纯色": "solid color background",
    "渐变": "gradient background",
    "图案": "patterned background",
    "透明": "transparent background",
    "星空": "starry sky background",
    "网格": "grid background",
    "花朵": "floral background",
    "云纹": "cloud pattern background",
    "花纹": "patterned background",
}

# 类型：主战场是「智能手机 / 平板键盘皮肤壁纸」，不做实体键盘
TYPE_MAP = {
    "手机": "mobile phone keyboard skin",
    "平板": "tablet keyboard skin",
}

# ---------------------------------------------------------------------------
# 2) 风格预设：未提到的维度用这里兜底，保证 prompt 永远完整
#    每个预设可含：zh 中文名、phrase 风格短语、color/material/lighting/shape/bg
#                  ar 竖屏比例(手机壁纸)、negative 该风格定制负面词(可选)
#    主战场为手机壁纸 → 默认竖屏 9:16 / 3:4；物理键盘会由引擎自动转 16:9。
# ---------------------------------------------------------------------------
STYLE_PRESETS = {
    "cyberpunk": {
        "zh": "赛博朋克",
        "phrase": "cyberpunk aesthetic with futuristic neon-city vibe",
        "color": "neon blue and purple", "material": "metal",
        "lighting": "RGB backlighting", "shape": "sculpted keycaps",
        "bg": "grid background", "ar": "9:16",
        "negative": "organic, nature, soft pastel, low-tech",
    },
    "kawaii": {
        "zh": "可爱少女",
        "phrase": "kawaii cute pastel style",
        "color": "soft pink and cream", "material": "acrylic",
        "lighting": "soft pastel glow", "shape": "rounded keycaps",
        "bg": "floral background", "ar": "3:4",
        "negative": "gore, dark, scary, harsh",
    },
    "minimal": {
        "zh": "极简",
        "phrase": "minimalist clean design",
        "color": "monochrome black and white", "material": "matte plastic",
        "lighting": "soft even lighting", "shape": "flat keycaps",
        "bg": "solid color background", "ar": "9:16",
        "negative": "clutter, ornate decoration, busy patterns",
    },
    "retro": {
        "zh": "复古",
        "phrase": "retro vintage style",
        "color": "cream and beige", "material": "wood",
        "lighting": "warm ambient lighting", "shape": "vintage spherical keycaps",
        "bg": "solid color background", "ar": "3:4",
    },
    "nature": {
        "zh": "自然森系",
        "phrase": "nature organic style",
        "color": "sage green and wood", "material": "wood",
        "lighting": "soft natural lighting", "shape": "rounded keycaps",
        "bg": "floral background", "ar": "3:4",
    },
    "chinese": {
        "zh": "国风",
        "phrase": "Chinese traditional ink style",
        "color": "ink black and crimson", "material": "lacquer",
        "lighting": "soft warm lighting", "shape": "sculpted keycaps",
        "bg": "cloud pattern background", "ar": "3:4",
    },
    "gothic": {
        "zh": "暗黑哥特",
        "phrase": "dark gothic style",
        "color": "black and deep red", "material": "metal",
        "lighting": "moody rim lighting", "shape": "sculpted keycaps",
        "bg": "solid color background", "ar": "9:16",
        "negative": "bright cheerful colors, pastel",
    },
    "tech": {
        "zh": "科技未来",
        "phrase": "futuristic tech style",
        "color": "electric blue and white", "material": "glass",
        "lighting": "glossy reflective", "shape": "flat keycaps",
        "bg": "gradient background", "ar": "9:16",
    },
    "dreamcore": {
        "zh": "梦核梦幻",
        "phrase": "dreamy surreal style",
        "color": "pastel rainbow", "material": "translucent acrylic",
        "lighting": "soft glow", "shape": "rounded keycaps",
        "bg": "starry sky background", "ar": "3:4",
    },
    "ornate": {
        "zh": "繁复华丽",
        "phrase": "ornate lavish decorative style",
        "color": "rich jewel tones", "material": "gilded",
        "lighting": "dramatic lighting", "shape": "intricate keycaps",
        "bg": "patterned background", "ar": "3:4",
        "negative": "minimal, plain, empty space",
    },
    # 未指定风格时的兜底预设（主战场=手机键盘壁纸，故默认竖屏）
    "default": {
        "zh": "通用",
        "phrase": "clean aesthetic keyboard skin",
        "color": "elegant gradient", "material": "smooth glass-like",
        "lighting": "soft ambient lighting", "shape": "rounded keycaps",
        "bg": "gradient background", "ar": "9:16",
        "negative": "cluttered, harsh contrast, deformed keys",
    },
}

# ---------------------------------------------------------------------------
# 3) 同义词 / 口头禅：小白爱说的词 → (维度, 规范英文)
#    维度取值：style / color / material / lighting / shape / bg
#    加这一层后，"酷炫""小清新""性冷淡" 这类词也能被听懂。
# ---------------------------------------------------------------------------
ALIASES = {
    # 风格
    "酷炫": ("style", "cyberpunk"),
    "霓虹城": ("style", "cyberpunk"),
    "科技风": ("style", "tech"),
    "科技感": ("style", "tech"),
    "小清新": ("style", "kawaii"),
    "软妹": ("style", "kawaii"),
    "萌系": ("style", "kawaii"),
    "性冷淡风": ("style", "minimal"),
    "极简风": ("style", "minimal"),
    "干净": ("style", "minimal"),
    "怀旧风": ("style", "retro"),
    "蒸汽": ("style", "vaporwave"),
    "梦": ("style", "dreamcore"),
    "华丽风": ("style", "ornate"),
    # 颜色
    "湖蓝": ("color", "lake blue"),
    "嫩绿": ("color", "light green"),
    "酒红": ("color", "wine red"),
    "金色感": ("color", "gold"),
    "渐变彩": ("color", "rainbow"),
    # 材质
    "金属感": ("material", "metal"),
    "玻璃感": ("material", "glass"),
    "磨砂感": ("material", "frosted plastic"),
    "通体透明": ("material", "transparent"),
    # 光效
    "流光溢彩": ("lighting", "flowing light"),
    "霓虹光": ("lighting", "neon glow"),
    "柔光": ("lighting", "soft glow"),
    # 背景
    "渐变底": ("bg", "gradient background"),
    "纯色底": ("bg", "solid color background"),
    "花纹": ("bg", "patterned background"),
}

# 预计算：按维度拆分别名表，引擎里按维度直接用
ALIASES_BY_DIM = {"style": {}, "color": {}, "material": {}, "lighting": {}, "shape": {}, "bg": {}, "type": {}}
for _alias, (_dim, _en) in ALIASES.items():
    ALIASES_BY_DIM[_dim][_alias] = _en

# ---------------------------------------------------------------------------
# 4) 否定词：被这些词修饰的关键词会被「去掉」或「降权」
#    HARD（直接去掉）：不要 / 别 / 去掉 / 非（紧贴时）/ 无 / 不含 …
#    SOFT（保留但降权，prompt 里加 subtle）：少 / 淡 / 不太 …
#    注：单独 "非" 只在「紧贴关键词」时才算否定，以区分 "非机械"(否定) 与 "非常机械"(非否定)。
# ---------------------------------------------------------------------------
NEG_HARD = ["不要", "别", "去掉", "去除", "无", "不含", "不准", "别用", "不要有", "移除", "没有", "别要", "非"]
NEG_SOFT = ["少", "淡", "不太", "尽量不", "别太", "轻", "弱化"]

# ---------------------------------------------------------------------------
# 5) 冲突规则：成对出现的相反维度 → 引擎检测后保留「最先出现」的那个并提示
#    写法：((维度, 规范英文值), (维度, 规范英文值))
# ---------------------------------------------------------------------------
CONTRADICTIONS = [
    (("style", "minimal"), ("style", "ornate")),             # 极简 vs 花哨
    (("lighting", "matte soft lighting"), ("lighting", "glossy reflective lighting")),  # 哑光 vs 镜面
    (("material", "transparent"), ("material", "wood")),     # 透明 vs 木质
    (("material", "transparent"), ("material", "metal")),    # 透明 vs 金属
    (("lighting", "matte soft lighting"), ("lighting", "translucent glowing")),  # 哑光 vs 透亮
]

# ---------------------------------------------------------------------------
# 6) 全局质量词与默认负面词
# ---------------------------------------------------------------------------
QUALITY = ("ultra detailed, 8k product render, centered, clean layout, "
           "professional photography, mobile keyboard wallpaper, full-bleed art")
NEGATIVE = ("blurry, low resolution, deformed keys, missing or extra keys, "
            "misaligned layout, wrong key shapes, text errors, watermark, "
            "logo, hands, people, real photo of hands typing")

# ---------------------------------------------------------------------------
# 7) 手机机型比例：不同品牌/型号屏幕比例不同，供用户按自己手机选择
#    默认 9:16；常见还有 9:18 / 9:19.5 / 9:20 等全面屏比例。
# ---------------------------------------------------------------------------
DEFAULT_RATIO = "9:16"
PHONE_RATIOS = ["9:16", "9:18", "9:19.5", "9:20", "3:4", "16:9"]

# ---------------------------------------------------------------------------
# 8) 手机键盘「形态模式」：键盘在屏幕上怎么摆，决定壁纸的"安全区"和构图
#    一张壁纸背景要能适配各种键盘形态，关键不是画什么，而是主体放哪、
#    键盘半透明浮上去时才不会被挡住。不同形态覆盖屏幕的区域不同：
#      - standard   标准全宽：底部约 45%
#      - landscape  横屏：旋转后横向键盘带
#      - onehand_left / onehand_right 单手左右：只占一侧窄条约 30%
#      - split      分体：左右两半、中间留空一列
#      - floating   浮窗：一个小窗，绝大部分屏幕可见
#    composition_en 会被写进 prompt，告诉 AI 把主体放在不被遮挡的位置。
#    注：输入法（字母/数字/符号/表情/手写/九宫格）都是叠在同一张背景上的，
#        所以"一张壁纸通吃所有输入模式"，无需为每种输入法单独生成。
# ---------------------------------------------------------------------------
KEYBOARD_MODES = {
    "standard": {
        "zh": "标准全宽",
        "en": "standard full-width on-screen keyboard",
        "coverage": "覆盖屏幕底部约 45%",
        "default_ar": "9:16",
        "composition_en": (
            "main focal subject anchored in the upper 40% of the frame, "
            "lower area kept as a soft ambient gradient so it stays readable "
            "behind a translucent full-width keyboard"
        ),
    },
    "landscape": {
        "zh": "横屏键盘",
        "en": "landscape on-screen keyboard",
        "coverage": "旋转后横向键盘带，占满宽度、高度偏矮",
        "default_ar": "16:9",
        "composition_en": (
            "designed for landscape aspect ratio, focal subject placed on the "
            "left or right third, central horizontal band kept clear for the keyboard"
        ),
    },
    "onehand_left": {
        "zh": "单手·左",
        "en": "one-handed keyboard docked to the left",
        "coverage": "只占左侧窄条，约 30% 宽",
        "default_ar": "9:16",
        "composition_en": (
            "focal subject placed on the right two-thirds of the screen, "
            "left edge kept as a soft gradient for the narrow left-docked keyboard"
        ),
    },
    "onehand_right": {
        "zh": "单手·右",
        "en": "one-handed keyboard docked to the right",
        "coverage": "只占右侧窄条，约 30% 宽",
        "default_ar": "9:16",
        "composition_en": (
            "focal subject placed on the left two-thirds of the screen, "
            "right edge kept as a soft gradient for the narrow right-docked keyboard"
        ),
    },
    "split": {
        "zh": "分体键盘",
        "en": "split keyboard with a central gap",
        "coverage": "左右两半、中间留空一列",
        "default_ar": "9:16",
        "composition_en": (
            "focal subject centered so it shows through the gap between the two "
            "keyboard halves, both side edges kept as soft gradient"
        ),
    },
    "floating": {
        "zh": "浮窗键盘",
        "en": "floating compact keyboard window",
        "coverage": "一个小浮窗，绝大部分屏幕可见",
        "default_ar": "9:16",
        "composition_en": (
            "composition works full-bleed since only a small floating window covers "
            "part of the screen; keep a single clear focal point"
        ),
    },
}
# UI 展示顺序
KEYBOARD_MODE_ORDER = ["standard", "landscape", "onehand_left", "onehand_right", "split", "floating"]
DEFAULT_MODE = "standard"
