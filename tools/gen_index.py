#!/usr/bin/env python3
"""
从仓库内的 .js 源文件生成 index.json。

设计原则（依据 Venera 官方 comic_source.md 与《开发日志》第 2、10 节）：
- index.json 字段：name / fileName / key / version / description(可选)
- key 一律取自源文件内的 key 字段，绝不手写，避免与源内不一致导致 App 无法识别
- name 使用源内 name；若源内 name 是占位符（如 "x"）才用本脚本的覆盖表
- version 取自源内 version
- description 仅写「已取证的事实」，不写推测（日志第 1 节：未验证不得写成已支持）

用法：python3 tools/gen_index.py
"""
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 源文件内 name 为空或为占位符时的显示名覆盖（键为文件名）
NAME_OVERRIDE = {}

# 可选描述。只写客观事实与用户需知，不写未验证的功能宣称。
DESCRIPTION = {
    "copy_manga.js": "拷贝漫画。需要登录后才能阅读部分内容；源会自动管理设备信息。",
    "ikmmh_v2.js": "爱看漫。中国大陆部分网络下首页可能返回 403，源内置多域名回退。",
    "komiic.js": "Komiic（双域名：komiic.cc / komiic.com，自动择优）。",
    "manwaba.js": "漫蛙吧。可在源设置中切换镜像域名。",
    "ykmh.js": "优酷漫画（修复版）。站点有 Cloudflare 防护，中国大陆网络可能需要代理。",
    "manwang.js": "漫网。官方搜索接口不稳定时会自动降级为站内目录检索。",
    "manhuauo_banana.js": "香蕉漫画。站点有 Cloudflare 防护，遇到 403 可稍后重试或更换网络。",
    "bilimanga.js": "嗶哩漫畫。需要登录方可阅读。",
    "dm5.js": "动漫屋。",
    "dongmanmanhua.js": "咚漫（LINE WEBTOON 中国区）。",
    "webtoons_zh_hant.js": "LINE WEBTOON 繁体中文。",
    "tencent_comic_official.js": "腾讯动漫（正版）。仅返回站点标记为可读的章节，付费章节请使用官方客户端。",
    "sfacg_manhua.js": "SF漫画。",
    "mh4399.js": "4399漫画网。",
    "zerobyw33.js": "zero搬运网。源会自动解析当前可用域名。",
    "rumanhua.js": "如漫画。",
    "mojoin.js": "MOJOIN（台湾）。",
    "noymanga.js": "NoyManga。",
    "rawkuma.js": "Rawkuma。",
    "hipmh.js": "嬉皮漫畫。",
    "wmanhua.js": "W漫画。",
    "tuku_cc.js": "图库漫画。",
    "gfmh.js": "古风漫画。",
    "ffppt.js": "飞翔漫画。",
    "guazi_manhua.js": "瓜子漫画。",
    "manga51.js": "51漫画。",
    "laimanhua_split_hosts.js": "来漫画（分流）。图片与页面域名分离，可在源设置中配置。",
    "dongman_la.js": "动漫啦。",
    "manga_dex.js": "MangaDex。官方源同步版本。",
    "wnacg.js": "紳士漫畫。官方源同步版本；不能使用时可在源设置中更换 URL。",
}


def extract(path):
    """从源文件顶层读取 name / key / version 字段。"""
    text = open(path, encoding="utf-8", errors="ignore").read()

    def field(name):
        # 只匹配类体顶层的 `name = "..."`（缩进 <= 8 空格）
        m = re.search(rf'^[ \t]{{0,8}}{name}[ \t]*=[ \t]*["\']([^"\']*)["\']', text, re.M)
        return m.group(1).strip() if m else ""

    return {"name": field("name"), "key": field("key"), "version": field("version")}


def main():
    files = sorted(f for f in os.listdir(REPO) if f.endswith(".js") and not f.startswith("_"))
    entries, problems = [], []

    for f in files:
        meta = extract(os.path.join(REPO, f))
        if not meta["key"]:
            problems.append(f"{f}: 未能提取 key")
            continue
        if not meta["version"]:
            problems.append(f"{f}: 未能提取 version")
            continue
        name = NAME_OVERRIDE.get(f) or meta["name"]
        if not name:
            problems.append(f"{f}: 未能提取 name 且无覆盖")
            continue

        entry = {"name": name, "fileName": f, "key": meta["key"], "version": meta["version"]}
        if f in DESCRIPTION:
            entry["description"] = DESCRIPTION[f]
        entries.append(entry)

    if problems:
        print("生成失败，存在无法解析的源：")
        for p in problems:
            print("  ✗", p)
        sys.exit(1)

    # key 唯一性
    seen = {}
    for e in entries:
        if e["key"] in seen:
            print(f"生成失败: key 重复 {e['key']}（{seen[e['key']]} 与 {e['fileName']}）")
            sys.exit(1)
        seen[e["key"]] = e["fileName"]

    out = os.path.join(REPO, "index.json")
    with open(out, "w", encoding="utf-8") as fp:
        json.dump(entries, fp, ensure_ascii=False, indent=4)
        fp.write("\n")

    print(f"✓ 已生成 {out}")
    print(f"  收录 {len(entries)} 个源，key 全部唯一")
    for e in entries:
        print(f"    {e['fileName']:<32} {e['name']:<16} key={e['key']:<22} v{e['version']}")


if __name__ == "__main__":
    main()
