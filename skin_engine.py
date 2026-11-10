# -*- coding: utf-8 -*-
"""
键盘皮肤提示词引擎（离线、零依赖）

把小白的"大白话描述"编译成 AI 图像模型（Midjourney / Stable Diffusion /
即梦 / 可灵 等）能直接看懂的专业提示词。

流程：中文描述 → 解析（含否定词 / 同义词 / 冲突消解）→
套用专业英文模板 → 输出 prompt + 负面词 + 参数 + 中文解读 + 警告。

【数据都放在 knowledge.py，想调风格/词意/规则只改那一个文件。】
"""

from knowledge import (
    STYLE_MAP, COLOR_MAP, MATERIAL_MAP, LIGHTING_MAP, SHAPE_MAP, BG_MAP, TYPE_MAP,
    STYLE_PRESETS, ALIASES_BY_DIM, NEG_HARD, NEG_SOFT, CONTRADICTIONS,
    QUALITY, NEGATIVE, DEFAULT_RATIO, PHONE_RATIOS,
    KEYBOARD_MODES, KEYBOARD_MODE_ORDER, DEFAULT_MODE,
)

# 英文属性值 → 中文标签（用于把冲突警告里的值翻成中文给用户看）
_REV = {}
for _m in (STYLE_MAP, COLOR_MAP, MATERIAL_MAP, LIGHTING_MAP, SHAPE_MAP, BG_MAP, TYPE_MAP):
    for _zh, _en in _m.items():
        _REV.setdefault(_en, _zh)


def _resolve_mode(mode):
    """把用户传入的形态键解析成 (mode_en, cfg)；非法值回退默认。"""
    if mode in KEYBOARD_MODES:
        return mode, KEYBOARD_MODES[mode]
    return DEFAULT_MODE, KEYBOARD_MODES[DEFAULT_MODE]


# ---------------------------------------------------------------------------
# 解析工具
# ---------------------------------------------------------------------------

def _scan(mapping, text):
    """找出所有命中的 (idx, en, zh)。

    采用「最长匹配优先 + 区间占用」策略，避免子串误判：
      - "赛博" 不会被误吞为 "赛博朋克"（后者更长，同起点优先）
      - "黄" 不会误吞 "黄金"（黄金 是更长键，占用区间）
    """
    raw = []
    for zh, en in mapping.items():
        start = 0
        while True:
            idx = text.find(zh, start)
            if idx == -1:
                break
            raw.append((idx, len(zh), en, zh))
            start = idx + len(zh)
    raw.sort(key=lambda h: (h[0], -h[1]))  # 先按位置，同位置长者优先
    taken = []
    out = []
    for idx, ln, en, zh in raw:
        s, e = idx, idx + ln
        if any(s >= ts and e <= te for ts, te in taken):
            continue
        taken.append((s, e))
        out.append((idx, en, zh))
    return out


def _is_negated(keyword_zh, text):
    """判断关键词是否被否定。

    返回 "hard"（应去掉）/ "soft"（保留但降权）/ None（未否定）。
    关键细节：单独 "非" 只在「紧贴关键词」时才算否定，
    从而区分 "非机械"(否定) 与 "非常机械"(非否定)。
    """
    i = text.find(keyword_zh)
    if i == -1:
        return None
    for m in NEG_HARD:
        gap = 1 if len(m) == 1 else len(m)
        if text[max(0, i - gap):i] == m:
            return "hard"
    kw_end = i + len(keyword_zh)
    for m in NEG_SOFT:
        before = text[max(0, i - 3):i]
        after = text[kw_end:kw_end + 3]
        if m in before or m in after:
            return "soft"
    return None


def _dim_scan(mapping, dim, text, warnings):
    """扫描某维度（含同义词），返回 (idx, en, zh, soft) 列表，并收集否定警告。"""
    hits = []
    for idx, en, zh in _scan(mapping, text):
        neg = _is_negated(zh, text)
        if neg == "hard":
            warnings.append(f"已忽略被否定的「{zh}」")
            continue
        hits.append((idx, en, zh, neg == "soft"))
    for idx, en, zh in _scan(ALIASES_BY_DIM[dim], text):
        neg = _is_negated(zh, text)
        if neg == "hard":
            continue
        hits.append((idx, en, zh, neg == "soft"))
    return hits


# ---------------------------------------------------------------------------
# 主解析
# ---------------------------------------------------------------------------

def analyze(description, style_hint=None, ratio=None, mode=None):
    """把中文描述解析成结构化属性（含否定 / 同义词 / 冲突消解 / 警告 / 机型比例 / 键盘形态）。"""
    text = description.lower()   # 中文无大小写影响；仅用于匹配 rgb 等英文关键词
    warnings = []

    # 键盘形态：决定壁纸"安全区"与构图（详见 knowledge.KEYBOARD_MODES）
    mode_en, mode_cfg = _resolve_mode(mode)
    mode_zh = mode_cfg["zh"]
    mode_coverage = mode_cfg["coverage"]
    composition = mode_cfg["composition_en"]

    # 风格：关键词 + 别名，排除 hard 否定，按出现顺序
    style_hits = []
    for idx, en, zh in _scan(STYLE_MAP, text):
        if _is_negated(zh, text) != "hard":
            style_hits.append((idx, en, zh))
    for idx, en, zh in _scan(ALIASES_BY_DIM["style"], text):
        if _is_negated(zh, text) != "hard":
            style_hits.append((idx, en, zh))
    style_hits.sort(key=lambda t: t[0])

    style_en = None
    if style_hits:
        style_en = style_hits[0][1]
    if not style_en and style_hint in STYLE_PRESETS:
        style_en = style_hint
    if not style_en:
        style_en = "default"
    style_zh = STYLE_PRESETS[style_en]["zh"]

    if len(style_hits) > 1:
        others = "、".join(STYLE_PRESETS[h[1]]["zh"] for h in style_hits[1:])
        warnings.append(f"检测到多个风格：{style_zh}、{others}，已采用最先出现的「{style_zh}」")

    preset = STYLE_PRESETS.get(style_en, STYLE_PRESETS["default"])

    # 各维度扫描
    color_hits = _dim_scan(COLOR_MAP, "color", text, warnings)
    mat_hits = _dim_scan(MATERIAL_MAP, "material", text, warnings)
    light_hits = _dim_scan(LIGHTING_MAP, "lighting", text, warnings)
    shape_hits = _dim_scan(SHAPE_MAP, "shape", text, warnings)
    bg_hits = _dim_scan(BG_MAP, "bg", text, warnings)
    type_hits = _dim_scan(TYPE_MAP, "type", text, warnings)

    # 维度 → [(en, idx, soft)]，供冲突消解使用
    chosen = {
        "style": [(en, idx, False) for idx, en, zh in style_hits],
        "color": [(en, idx, soft) for idx, en, zh, soft in color_hits],
        "material": [(en, idx, soft) for idx, en, zh, soft in mat_hits],
        "lighting": [(en, idx, soft) for idx, en, zh, soft in light_hits],
        "shape": [(en, idx, soft) for idx, en, zh, soft in shape_hits],
        "bg": [(en, idx, soft) for idx, en, zh, soft in bg_hits],
        "type": [(en, idx, soft) for idx, en, zh, soft in type_hits],
    }

    # 冲突消解：成对相反维度，保留「最先出现」的那个，丢弃另一个并警告
    for (d1, v1), (d2, v2) in CONTRADICTIONS:
        list1 = chosen.get(d1, [])
        list2 = chosen.get(d2, [])
        if any(v1 in e for e, _, _ in list1) and any(v2 in e for e, _, _ in list2):
            idx1 = min(i for e, i, _ in list1 if v1 in e)
            idx2 = min(i for e, i, _ in list2 if v2 in e)
            if idx1 <= idx2:
                chosen[d2] = [(e, i, s) for e, i, s in list2 if not (v2 in e and i == idx2)]
                keep, drop = v1, v2
            else:
                chosen[d1] = [(e, i, s) for e, i, s in list1 if not (v1 in e and i == idx1)]
                keep, drop = v2, v1
            warnings.append(f"检测到冲突：{_REV.get(drop, drop)} 与 {_REV.get(keep, keep)} 不能同时成立，已按出现顺序保留「{_REV.get(keep, keep)}」")

    # 取值（soft 降权 → 英文前加 "subtle "）
    def _pick(d, default):
        lst = chosen.get(d, [])
        if not lst:
            return default, False
        en, _, soft = lst[0]
        return ("subtle " + en) if soft else en, soft

    material, _ = _pick("material", preset.get("material", "acrylic"))
    lighting, _ = _pick("lighting", preset.get("lighting", "soft lighting"))
    shape, _ = _pick("shape", preset.get("shape", "rounded keycaps"))
    bg, _ = _pick("bg", preset.get("bg", "gradient background"))

    colors_en = [(("subtle " + e) if s else e) for e, _, s in chosen["color"]]
    color_en = ", ".join(colors_en) if colors_en else preset.get("color", "elegant")
    colors_zh = [zh for _, _, zh, _ in color_hits]

    ktype, _ = _pick("type", "mobile phone keyboard skin")

    # 比例优先级：用户指定的机型比例 > 键盘形态默认比例 > 风格预设比例
    ar = ratio if ratio else (mode_cfg.get("default_ar") or preset.get("ar", DEFAULT_RATIO))
    phrase = preset.get("phrase", "stylish")

    # 解读栏 color_zh 必须保持中文
    if colors_zh:
        color_zh = "、".join(colors_zh)
    elif style_en != "default":
        color_zh = f"{style_zh}配色"
    else:
        color_zh = "默认配色"

    return {
        "type": ktype,
        "style_en": style_en,
        "style_zh": style_zh,
        "color_en": color_en,
        "color_zh": color_zh,
        "material": material,
        "lighting": lighting,
        "shape": shape,
        "bg": bg,
        "ar": ar,
        "phrase": phrase,
        "mode": mode_en,
        "mode_zh": mode_zh,
        "mode_coverage": mode_coverage,
        "composition": composition,
        "warnings": warnings,
        "note": "；".join(warnings),
    }


def build_prompt(attrs, description=""):
    """根据属性拼出英文 prompt 主体 + 负面词 + 参数（含风格，便于 Agent 消费）。"""
    theme = f', theme: "{description}"' if description.strip() else ""
    prompt = (
        f"A {attrs['type']}, {attrs['phrase']}, "
        f"{attrs['color_en']} color scheme, made of {attrs['material']}, "
        f"{attrs['lighting']}, {attrs['shape']}, {attrs['bg']}{theme}. "
        f"Composition: {attrs['composition']}. "
        f"{QUALITY}."
    )
    negative = STYLE_PRESETS.get(attrs["style_en"], {}).get("negative", NEGATIVE)
    params = {
        "aspect_ratio": attrs["ar"],
        "style_en": attrs["style_en"],
        "style_zh": attrs["style_zh"],
    }
    return prompt, negative, params


# 四种目标平台的"复制即用"格式。Agent 可按需取用其一。
FORMATS = ["universal", "midjourney", "stable_diffusion", "jimeng"]

_AR_WH = {
    "1:1": (1024, 1024),
    "3:4": (768, 1024),
    "9:16": (720, 1280),
    "9:18": (720, 1440),
    "9:19.5": (720, 1560),
    "9:20": (720, 1600),
    "3:2": (1024, 683),
    "16:9": (1280, 720),
}


def _ar_to_wh(ar):
    return _AR_WH.get(ar, (1024, 1024))


def format_outputs(prompt, negative, params):
    """把核心 prompt 渲染成四种平台各自的复制即用文本。"""
    ar = params["aspect_ratio"]
    w, h = _ar_to_wh(ar)
    universal = f"{prompt}\n[负面词] {negative}\n[比例] {ar}"
    midjourney = f"{prompt} --ar {ar} --style raw\n--no {negative}"
    stable_diffusion = (
        f"{prompt}\nNegative prompt: {negative}\n"
        f"Steps: 30, Sampler: DPM++ 2M Karras, CFG scale: 7, Size: {w}x{h}"
    )
    jimeng = f"{prompt}\n比例 {ar}　|　负面词：{negative}"
    return {
        "universal": universal,
        "midjourney": midjourney,
        "stable_diffusion": stable_diffusion,
        "jimeng": jimeng,
    }


def zh_summary(attrs):
    """给小白看的中文解读：工具"听懂"了什么。"""
    base = (
        f"风格：{attrs['style_zh']}　颜色：{attrs['color_zh']}　"
        f"材质：{attrs['material']}　光效：{attrs['lighting']}　"
        f"键帽：{attrs['shape']}　背景：{attrs['bg']}　"
        f"类型：{attrs['type']}　键盘形态：{attrs['mode_zh']}"
    )
    if attrs.get("warnings"):
        base += "\n⚠️ " + "；".join(attrs["warnings"])
    return base


def generate(description, style=None, ratio=None, mode=None):
    """总入口：描述 → 完整结果字典（可直接返回给前端 / Agent）。

    返回同时包含：单条 prompt / negative / params（兼容旧调用），
    以及 outputs 字典（四种平台复制即用文本）与 attributes（含 warnings）。

    ratio: 可选，指定手机机型比例（如 "9:19.5"），用于适配不同手机屏幕。
    mode:  可选，键盘形态（standard/landscape/onehand_left/onehand_right/
           split/floating），决定壁纸构图安全区与默认比例。
    """
    attrs = analyze(description, style, ratio, mode)
    prompt, negative, params = build_prompt(attrs, description)
    return {
        "prompt": prompt,
        "negative_prompt": negative,
        "params": params,
        "attributes": attrs,
        "zh": zh_summary(attrs),
        "outputs": format_outputs(prompt, negative, params),
    }


def list_styles():
    """供前端风格预设 chips 使用。"""
    return [
        {"en": en, "zh": v["zh"], "phrase": v["phrase"]}
        for en, v in STYLE_PRESETS.items()
        if en != "default"
    ]


if __name__ == "__main__":
    demo = "我想要一个赛博朋克风格、霓虹蓝紫、金属质感、带RGB发光的手机键盘壁纸"
    import json
    print(json.dumps(generate(demo), ensure_ascii=False, indent=2))
