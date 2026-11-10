# -*- coding: utf-8 -*-
"""
KeySkin 命令行入口（本地 Agent 直接调用，无需起 HTTP 服务）

用法示例
--------
# 生成并默认打印「通用」格式的复制即用提示词
python keyskin.py "赛博朋克霓虹紫的手机键盘壁纸，透明质感，RGB灯"

# 指定风格 + 指定平台格式（midjourney / stable_diffusion / jimeng / universal）
python keyskin.py "国风红金手机键盘" -s chinese -f midjourney

# 指定机型比例（适配不同手机屏幕，如 9:19.5 / 9:20）
python keyskin.py "极简手机键盘壁纸" -r 9:19.5

# 指定键盘形态（standard / landscape / onehand_left / onehand_right / split / floating）
# 横屏会切换到 16:9 构图；分体/单手会让主体避开键盘遮挡区
python keyskin.py "赛博朋克手机键盘壁纸" -m split

# 输出完整 JSON（含四种格式与结构化属性），方便程序解析
python keyskin.py "可爱粉色键盘" --json

# 从文件批量生成（每行一条描述）
python keyskin.py --batch descs.txt -f jimeng

# 直接拉起 Web 服务（等价于 python app.py）
python keyskin.py --serve

作为 Python 库调用
------------------
    from skin_engine import generate
    print(generate("赛博朋克键盘")["outputs"]["midjourney"])
"""
import argparse
import json
import sys

from skin_engine import generate, list_styles
from knowledge import PHONE_RATIOS, KEYBOARD_MODE_ORDER, DEFAULT_MODE

VALID_FORMATS = ["universal", "midjourney", "stable_diffusion", "jimeng"]


def _print_one(description, style, fmt, as_json, ratio=None, mode=None):
    res = generate(description, style, ratio, mode)
    if as_json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return
    print(f"# {description}")
    print(res["outputs"].get(fmt, res["outputs"]["universal"]))
    print(f"\n[中文解读] {res['zh']}\n")


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="keyskin",
        description="把大白话描述编译成 AI 图像模型直接可用的键盘皮肤提示词",
    )
    p.add_argument("description", nargs="?", help="一条中文描述")
    p.add_argument("-s", "--style", help="风格预设：" + "/".join(s["en"] for s in list_styles()))
    p.add_argument("-f", "--format", default="universal",
                   choices=VALID_FORMATS, help="输出格式（默认 universal）")
    p.add_argument("-r", "--ratio", default=None, choices=PHONE_RATIOS,
                   help="手机机型比例（适配屏幕，如 9:19.5 / 9:20）")
    p.add_argument("-m", "--mode", default=None, choices=KEYBOARD_MODE_ORDER,
                   help="键盘形态：" + "/".join(KEYBOARD_MODE_ORDER))
    p.add_argument("--json", action="store_true", help="输出完整 JSON")
    p.add_argument("--batch", help="从文本文件批量生成（每行一条描述）")
    p.add_argument("--serve", action="store_true", help="启动 Web 服务")
    args = p.parse_args(argv)

    if args.serve:
        import app
        app.init_db()
        app.app.run(host="0.0.0.0", port=5000, debug=True)
        return

    if args.batch:
        with open(args.batch, "r", encoding="utf-8") as fh:
            lines = [ln.strip() for ln in fh if ln.strip()]
        for ln in lines:
            _print_one(ln, args.style, args.format, args.json, args.ratio, args.mode)
            print("-" * 60)
        return

    if not args.description:
        p.print_help()
        sys.exit(1)

    _print_one(args.description, args.style, args.format, args.json, args.ratio, args.mode)


if __name__ == "__main__":
    main()
