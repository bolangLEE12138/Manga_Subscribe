#!/usr/bin/env python3
"""
把所有源的顶层 `url` 字段统一指向本仓库，使其成为可自我更新的源仓库。

为什么必须做这一步
------------------
App 源码 `lib/pages/comic_source_page.dart` 的 `ComicSourcePage.update()`：

    if (!source.url.isURL) { ... "Invalid url config"; return; }
    ComicSourceManager().remove(source.key);          // ← 先删源
    var res = await AppDio().get<String>(source.url); // ← 再从 url 下载
    await ComicSourceParser().parse(res.data!, ...);  // ← 解析失败则源已丢失

结论有三条：
1. `url` 是**唯一**的更新下载地址；index.json 只用于「检查更新」比对版本。
2. `url` 若是漫画网站首页，更新会下载 HTML、解析失败，而源**已被删除**。
3. 若 `url` 指向别人的仓库，更新会把你的私有修复版**覆盖成对方的版本**。

因此本仓库内每个源的 `url` 都应指向本仓库自身的原始文件地址。

用法
----
    python3 tools/set_url.py https://raw.githubusercontent.com/<用户>/<仓库>/main
    python3 tools/set_url.py https://example.com/venera          # 末尾斜杠可有可无
    python3 tools/set_url.py --show                              # 只查看当前状态
    python3 tools/set_url.py --restore                           # 还原为改动前的备份
"""
import json
import os
import re
import shutil
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKUP = os.path.join(REPO, ".url-backup")


def source_files():
    idx_path = os.path.join(REPO, "index.json")
    if os.path.exists(idx_path):
        idx = json.load(open(idx_path, encoding="utf-8"))
        return [e["fileName"] for e in idx]
    return sorted(f for f in os.listdir(REPO) if f.endswith(".js") and not f.startswith("_"))


def top_level_url(text):
    """读取类体内顶层的 url 字段（缩进 <= 8 空格）。"""
    m = re.search(r'^[ \t]{0,8}url[ \t]*=[ \t]*["\']([^"\']*)["\']', text, re.M)
    return (m.group(1), m.span()) if m else (None, None)


def set_url(text, value):
    """写回顶层 url 字段；若不存在则在 key 字段之后插入。"""
    pattern = r'^([ \t]{0,8})url[ \t]*=[ \t]*["\'][^"\']*["\']'

    def repl(m):
        return f'{m.group(1)}url = "{value}"'

    new, n = re.subn(pattern, repl, text, count=1, flags=re.M)
    if n:
        return new

    # 没有 url 字段：插在 top-level key 之后，保持类体风格
    m = re.search(r'^([ \t]{0,8})key[ \t]*=[ \t]*["\'][^"\']*["\']', text, re.M)
    if not m:
        raise RuntimeError("找不到顶层 key 字段，无法定位插入点")
    indent = m.group(1)
    insert = f'\n\n{indent}url = "{value}"'
    return text[: m.end()] + insert + text[m.end():]


def main():
    args = sys.argv[1:]

    if args and args[0] == "--restore":
        if not os.path.isdir(BACKUP):
            print("没有可还原的备份（.url-backup 不存在）")
            sys.exit(1)
        n = 0
        for f in os.listdir(BACKUP):
            shutil.copy2(os.path.join(BACKUP, f), os.path.join(REPO, f))
            n += 1
        print(f"✓ 已还原 {n} 个文件")
        return

    files = source_files()

    if not args or args[0] == "--show":
        print(f"{'文件':<34}{'顶层 url'}")
        print("-" * 100)
        bad = []
        for f in files:
            p = os.path.join(REPO, f)
            if not os.path.exists(p):
                continue
            url, _ = top_level_url(open(p, encoding="utf-8").read())
            shown = url if url else "(空)"
            print(f"{f:<34}{shown}")
            if url and not re.search(r'\.(js|mjs)(\?|$)', url) and "raw.githubusercontent" not in url \
               and "jsdelivr" not in url and "gitea" not in url and "git." not in url:
                bad.append((f, url))
        if bad:
            print("\n⚠ 以下 url 疑似指向网页而非 .js 更新地址，更新时会先删源再失败：")
            for f, u in bad:
                print(f"    {f}: {u}")
        return

    base = args[0].rstrip("/")
    if not base.startswith(("http://", "https://")):
        print(f"✗ 仓库地址必须以 http:// 或 https:// 开头: {base}")
        sys.exit(1)

    # 备份一次，便于回滚
    if not os.path.isdir(BACKUP):
        os.makedirs(BACKUP)
        for f in files:
            p = os.path.join(REPO, f)
            if os.path.exists(p):
                shutil.copy2(p, os.path.join(BACKUP, f))
        print(f"已备份原始文件到 {BACKUP}\n")

    changed = 0
    for f in files:
        p = os.path.join(REPO, f)
        if not os.path.exists(p):
            print(f"  ! 跳过不存在的文件 {f}")
            continue
        text = open(p, encoding="utf-8").read()
        old, _ = top_level_url(text)
        new_url = f"{base}/{f}"
        if old == new_url:
            continue
        open(p, "w", encoding="utf-8").write(set_url(text, new_url))
        changed += 1
        print(f"  ✓ {f}\n      {old or '(空)'}\n   -> {new_url}")

    print(f"\n✓ 已更新 {changed} 个源，全部指向 {base}")
    print("\n注意：源文件内容已改变，但 version 字段刻意未变。")
    print("原因见 README「版本策略」一节：App 的 update() 会先 remove() 再下载，")
    print("对已安装旧 url 的用户贸然提升版本会导致更新失败并丢失源。")


if __name__ == "__main__":
    main()
