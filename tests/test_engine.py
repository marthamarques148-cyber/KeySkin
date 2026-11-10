"""
KeySkin 测试
- skin_engine：离线编译逻辑（不需要任何外部服务）
- app API：用 Flask test client 验证 /api/generate 与 /api/styles
- 主战场：智能手机 / 平板键盘壁纸（机械键盘已移除）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skin_engine import generate, analyze, list_styles
import app as appmod


# ----------------------------- 引擎测试 -----------------------------
def test_cyberpunk_detected():
    r = generate("赛博朋克、霓虹蓝紫、金属材质、带RGB发光的手机键盘壁纸")
    assert "cyberpunk" in r["prompt"].lower()
    assert "mobile phone keyboard skin" in r["prompt"]
    assert "RGB backlighting" in r["prompt"]
    assert "金属" not in r["attributes"]["color_zh"]   # 不应误判为金色
    assert r["params"]["aspect_ratio"] == "9:16"        # 手机壁纸默认竖屏


def test_kawaii_default_fallback():
    r = generate("想要一个可爱粉色的手机键盘壁纸")
    assert "kawaii" in r["prompt"].lower()
    assert "mobile phone keyboard skin" in r["prompt"]
    assert "soft pink" in r["attributes"]["color_en"] or "pink" in r["prompt"].lower()


def test_no_style_hint_uses_default():
    r = generate("蓝色玻璃材质的键盘")
    assert r["prompt"].startswith("A")
    assert "glass" in r["prompt"].lower()


def test_negative_prompt_present():
    # 科技风格无定制负面词 → 使用全局 NEGATIVE（含 blurry / deformed keys）
    r = generate("科技未来银色手机键盘壁纸")
    assert "blurry" in r["negative_prompt"]
    assert "deformed keys" in r["negative_prompt"]


def test_style_list_nonempty():
    styles = list_styles()
    assert isinstance(styles, list) and len(styles) >= 5
    assert all("en" in s and "zh" in s for s in styles)
    # 机械键盘相关风格已移除
    assert all(s["en"] != "mecha" for s in styles)


def test_analyze_color_join():
    attrs = analyze("红金蓝三色键盘壁纸")
    assert "red" in attrs["color_en"] or "gold" in attrs["color_en"] or "blue" in attrs["color_en"]


def test_no_lighting_redundancy():
    # 模板不再重复拼 "lighting"，光效值本身已是完整描述
    for desc in ["赛博朋克RGB灯手机键盘", "极简白黑键盘壁纸", "暗黑哥特键盘壁纸",
                 "科技未来银色键盘", "发光键盘", "自然森系木纹柔和光"]:
        r = generate(desc)
        p = r["prompt"].lower()
        assert "lighting lighting" not in p, desc
        assert "light lighting" not in p, desc


def test_color_zh_always_chinese():
    r = generate("自然森系 木纹 柔和光")
    cz = r["attributes"]["color_zh"]
    assert not any(c.isascii() and c.isalpha() for c in cz), cz


def test_default_style_color_zh_is_chinese():
    r = generate("一个很大的发光键盘壁纸")
    assert r["attributes"]["color_zh"] == "默认配色", r["attributes"]["color_zh"]
    assert "None" not in r["attributes"]["color_zh"]


def test_four_formats_present():
    r = generate("赛博朋克霓虹紫的手机键盘壁纸，透明质感，RGB灯")
    outs = r["outputs"]
    assert set(outs.keys()) == {"universal", "midjourney", "stable_diffusion", "jimeng"}
    assert "--ar 9:16" in outs["midjourney"]
    assert "--no " in outs["midjourney"]
    assert "Negative prompt:" in outs["stable_diffusion"]
    assert "Size: 720x1280" in outs["stable_diffusion"]
    assert "比例 9:16" in outs["jimeng"]


def test_params_contains_style():
    r = generate("国风红金手机键盘壁纸")
    assert r["params"]["style_en"] == "chinese"
    assert r["params"]["style_zh"] == "国风"


def test_multi_style_conflict_note():
    # 同时给出多个风格时，应提示采用了最先出现的那一个
    r = generate("可爱又暗黑的键盘壁纸")
    note = r["attributes"]["note"]
    assert "可爱" in note and "暗黑" in note
    assert "已采用" in note


# ----------------------------- 方案 B：否定 / 同义词 / 冲突 -----------------------------
def test_negation_removes_color():
    # "不要红色" 不应出现 red
    r = generate("不要红色的蓝色手机键盘壁纸")
    assert "red" not in r["attributes"]["color_en"].lower()
    assert "blue" in r["attributes"]["color_en"].lower()
    assert any("红" in w for w in r["attributes"]["warnings"])


def test_negation_not_tricked_by_feichang():
    # "非常" 不应被误判为 "非" 的否定
    r = generate("非常可爱的手机键盘壁纸")
    assert r["attributes"]["style_en"] == "kawaii"
    assert not any("非" in w for w in r["attributes"]["warnings"])


def test_alias_cool_maps_to_cyberpunk():
    # 同义词：酷炫 → 赛博朋克
    r = generate("酷炫风格的手机键盘壁纸")
    assert r["attributes"]["style_en"] == "cyberpunk"
    assert r["attributes"]["style_zh"] == "赛博朋克"


def test_alias_xiaofresh_maps_to_kawaii():
    r = generate("小清新手机键盘壁纸")
    assert r["attributes"]["style_en"] == "kawaii"


def test_conflict_minimal_vs_ornate():
    # 极简 but 花哨 → 检测到冲突，保留最先出现的极简
    r = generate("极简但很花哨的键盘壁纸")
    a = r["attributes"]
    assert a["style_en"] == "minimal"
    assert any("冲突" in w for w in a["warnings"])


def test_golden_not_yellow():
    # "黄金" 不应被误判为 "黄"
    r = generate("黄金配色的国风键盘壁纸")
    assert "yellow" not in r["attributes"]["color_en"].lower()
    assert "gold" in r["attributes"]["color_en"].lower()


def test_ratio_param_overrides():
    # 用户指定机型比例应生效
    r = generate("手机键盘壁纸", ratio="9:19.5")
    assert r["params"]["aspect_ratio"] == "9:19.5"


def test_mechanical_removed():
    # 机械键盘目标已移除：不再产出 mechanical 类型
    r = generate("机械键盘")
    assert "mechanical" not in r["prompt"].lower()
    assert "mobile phone keyboard skin" in r["prompt"].lower()


# ----------------------------- 方案 C：键盘形态（placement mode） -----------------------------
def test_mode_default_is_standard():
    r = generate("手机键盘壁纸")
    assert r["attributes"]["mode"] == "standard"
    assert r["attributes"]["mode_zh"] == "标准全宽"
    assert r["params"]["aspect_ratio"] == "9:16"


def test_mode_landscape_changes_ar():
    # 横屏形态应切换到 16:9，并在 prompt 里写明横构图
    r = generate("手机键盘壁纸", mode="landscape")
    assert r["params"]["aspect_ratio"] == "16:9"
    assert "landscape aspect ratio" in r["prompt"]


def test_mode_split_composition():
    # 分体键盘：主体居中、从缝隙透出
    r = generate("手机键盘壁纸", mode="split")
    assert r["attributes"]["mode_zh"] == "分体键盘"
    assert "gap between the two" in r["prompt"]


def test_mode_onehand_right_safe_zone():
    r = generate("手机键盘壁纸", mode="onehand_right")
    assert "left two-thirds" in r["prompt"]


def test_mode_explicit_ratio_wins_over_mode_default():
    # 用户显式指定比例时，应优先于形态默认比例
    r = generate("手机键盘壁纸", mode="landscape", ratio="9:19.5")
    assert r["params"]["aspect_ratio"] == "9:19.5"


def test_mode_unknown_falls_back_to_default():
    r = generate("手机键盘壁纸", mode="not_a_real_mode")
    assert r["attributes"]["mode"] == "standard"


# ----------------------------- API 测试 -----------------------------
def test_api_batch_and_export(tmp_path):
    c = _client(tmp_path)
    r = c.post("/api/batch", json={"descriptions": ["赛博朋克手机键盘壁纸", "极简白键盘壁纸"]})
    body = r.get_json()
    assert body["ok"] is True
    assert body["count"] == 2
    assert all("outputs" in item for item in body["results"])

    exp = c.get("/api/export").get_json()
    assert len(exp) == 2
    assert any("赛博朋克" in s["description"] for s in exp)


def test_api_generate_returns_outputs(tmp_path):
    c = _client(tmp_path)
    r = c.post("/api/generate", json={"description": "国风红金手机键盘壁纸"}).get_json()
    assert "outputs" in r and "midjourney" in r["outputs"]


def test_api_styles_shape(tmp_path):
    c = _client(tmp_path)
    data = c.get("/api/styles").get_json()
    assert "styles" in data and len(data["styles"]) >= 5
    assert "ratios" in data and "9:16" in data["ratios"]
    assert data["default_ratio"] == "9:16"


def test_api_generate_with_ratio(tmp_path):
    c = _client(tmp_path)
    r = c.post("/api/generate", json={"description": "手机键盘壁纸", "ratio": "9:20"}).get_json()
    assert r["params"]["aspect_ratio"] == "9:20"


def test_api_styles_includes_keyboard_modes(tmp_path):
    c = _client(tmp_path)
    data = c.get("/api/styles").get_json()
    assert "keyboard_modes" in data and len(data["keyboard_modes"]) >= 6
    assert any(m["en"] == "split" for m in data["keyboard_modes"])
    assert data["default_mode"] == "standard"


def test_api_generate_with_mode(tmp_path):
    c = _client(tmp_path)
    r = c.post("/api/generate", json={"description": "手机键盘壁纸", "mode": "landscape"}).get_json()
    assert r["params"]["aspect_ratio"] == "16:9"
    assert r["attributes"]["mode_zh"] == "横屏键盘"


# ----------------------------- CLI 测试 -----------------------------
def test_cli_single(tmp_path):
    import subprocess, sys
    out = subprocess.run(
        [sys.executable, "keyskin.py", "赛博朋克手机键盘壁纸", "-f", "midjourney"],
        capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    assert out.returncode == 0
    assert "--ar" in out.stdout
    assert "中文解读" in out.stdout


def test_cli_ratio(tmp_path):
    import subprocess, sys
    out = subprocess.run(
        [sys.executable, "keyskin.py", "极简手机键盘壁纸", "-r", "9:19.5"],
        capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    assert out.returncode == 0
    assert "9:19.5" in out.stdout


def test_cli_mode(tmp_path):
    import subprocess, sys
    out = subprocess.run(
        [sys.executable, "keyskin.py", "赛博朋克手机键盘壁纸", "-m", "split"],
        capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    assert out.returncode == 0
    assert "分体键盘" in out.stdout


# ----------------------------- 测试夹具 -----------------------------
def _client(tmp_path):
    appmod.DB_PATH = str(tmp_path / "keyskin.db")
    appmod.init_db()
    appmod.app.config.update(TESTING=True)
    return appmod.app.test_client()
