"""
KeySkin —— 键盘皮肤提示词生成器
把小白的"大白话描述"编译成 AI 图像模型（MJ / SD / 即梦 / 可灵 等）直接能用的专业提示词。

后端：Flask + SQLite + 可选 Ollama 本地润色（无 Ollama 时优雅降级）
"""
import os
import sqlite3
import json
from datetime import datetime

import requests
from flask import Flask, jsonify, request, send_from_directory

from skin_engine import generate, list_styles
from knowledge import PHONE_RATIOS, DEFAULT_RATIO, KEYBOARD_MODES, KEYBOARD_MODE_ORDER, DEFAULT_MODE

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "keyskin.db")
STATIC_DIR = os.path.join(BASE_DIR, "static")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

app = Flask(__name__, static_folder=STATIC_DIR)


# ----------------------------- 数据库 -----------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS skins (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            description     TEXT NOT NULL,
            prompt          TEXT NOT NULL,
            negative_prompt TEXT DEFAULT '',
            params          TEXT DEFAULT '{}',
            style           TEXT DEFAULT '',
            outputs         TEXT DEFAULT '{}',
            created_at      TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def now():
    return datetime.now().isoformat(timespec="seconds")


# ----------------------------- 页面 -----------------------------
@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


# ----------------------------- 核心 API -----------------------------
@app.route("/api/styles")
def api_styles():
    return jsonify({
        "styles": list_styles(),
        "ratios": PHONE_RATIOS,
        "default_ratio": DEFAULT_RATIO,
        "keyboard_modes": [
            {"en": m, "zh": KEYBOARD_MODES[m]["zh"], "coverage": KEYBOARD_MODES[m]["coverage"]}
            for m in KEYBOARD_MODE_ORDER
        ],
        "default_mode": DEFAULT_MODE,
    })


@app.route("/api/generate", methods=["POST"])
def api_generate():
    data = request.get_json(force=True)
    description = (data.get("description") or "").strip()
    style = data.get("style") or None
    ratio = data.get("ratio") or None
    mode = data.get("mode") or None
    if not description:
        return jsonify({"ok": False, "error": "请先描述你想要的键盘皮肤"}), 400
    result = generate(description, style, ratio, mode)
    result["ok"] = True
    return jsonify(result)


@app.route("/api/batch", methods=["POST"])
def api_batch():
    """批量编译：一次提交多条描述，逐条生成并存入历史，返回结果列表。"""
    data = request.get_json(force=True)
    descriptions = data.get("descriptions") or []
    style = data.get("style") or None
    ratio = data.get("ratio") or None
    mode = data.get("mode") or None
    descriptions = [d.strip() for d in descriptions if str(d).strip()]
    if not descriptions:
        return jsonify({"ok": False, "error": "请至少提供一条描述"}), 400
    results = []
    conn = get_db()
    for desc in descriptions:
        res = generate(desc, style, ratio, mode)
        res["ok"] = True
        conn.execute(
            "INSERT INTO skins (description, prompt, negative_prompt, params, style, outputs, created_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (
                desc,
                res["prompt"],
                res["negative_prompt"],
                json.dumps(res["params"], ensure_ascii=False),
                res["attributes"].get("style_en", ""),
                json.dumps(res["outputs"], ensure_ascii=False),
                now(),
            ),
        )
        results.append(res)
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "count": len(results), "results": results})


@app.route("/api/enhance", methods=["POST"])
def api_enhance():
    """可选：用本机 Ollama 模型对草稿做智能润色（无 Ollama 时降级）。"""
    data = request.get_json(force=True)
    draft = (data.get("prompt") or "").strip()
    model = data.get("model") or ""
    if not draft:
        return jsonify({"ok": False, "error": "没有可润色的提示词"}), 400
    if not model:
        return jsonify({"ok": False, "error": "请先选择一个本地模型"}), 400
    system = (
        "You are an expert prompt engineer for AI image generators "
        "(Midjourney / Stable Diffusion / 即梦 / 可灵). Rewrite the given "
        "keyboard-skin prompt to be more vivid and detailed, keep English, "
        "return ONLY the improved prompt, no explanation."
    )
    try:
        r = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": model,
                "prompt": f"{system}\n\nDraft: {draft}",
                "temperature": 0.6,
                "stream": False,
            },
            timeout=180,
        )
        r.raise_for_status()
        return jsonify({"ok": True, "prompt": r.json().get("response", draft).strip()})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/models")
def api_models():
    try:
        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        r.raise_for_status()
        models = [m["name"] for m in r.json().get("models", [])]
        return jsonify({"ok": True, "models": models})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "models": []})


# ----------------------------- 历史（我的皮肤） -----------------------------
@app.route("/api/skins", methods=["GET"])
def api_skins_list():
    conn = get_db()
    rows = conn.execute("SELECT * FROM skins ORDER BY created_at DESC").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/skins", methods=["POST"])
def api_skins_create():
    data = request.get_json(force=True)
    ts = now()
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO skins (description, prompt, negative_prompt, params, style, outputs, created_at) "
        "VALUES (?,?,?,?,?,?,?)",
        (
            data.get("description", ""),
            data.get("prompt", ""),
            data.get("negative_prompt", ""),
            json.dumps(data.get("params", {}), ensure_ascii=False),
            data.get("style", ""),
            json.dumps(data.get("outputs", {}), ensure_ascii=False),
            ts,
        ),
    )
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return jsonify({"ok": True, "id": pid})


@app.route("/api/export")
def api_export():
    """导出全部历史为 JSON（供下载 / Agent 批量消费）。"""
    conn = get_db()
    rows = conn.execute("SELECT * FROM skins ORDER BY created_at DESC").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/skins/<int:sid>", methods=["DELETE"])
def api_skins_delete(sid):
    conn = get_db()
    conn.execute("DELETE FROM skins WHERE id=?", (sid,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
