#!/usr/bin/env python3
"""
为每个源设置顶层 `url` 字段（更新地址）。

为什么要区分两类源
------------------
App 源码 `lib/pages/comic_source_page.dart` 的 `ComicSourcePage.update()`：

    if (!source.url.isURL) { ... "Invalid url config"; return; }
    ComicSourceManager().remove(source.key);          // ← 先删源
    var res = await AppDio().get<String>(source.url); // ← 再从 url 下载
    await ComicSourceParser().parse(res.data!, ...);  // ← 解析失败则源已丢失

结论：
1. `url` 是**唯一**的更新下载地址；index.json 只用于「检查更新」比对版本。
2. `url` 若是漫画网站首页，更新会下载 HTML、解析失败，而源**已被删除**。
3. 若 `url` 指向别人的仓库，你的私有修复版会被**覆盖成对方的版本**。

因此本仓库把源分两类（名单见 tools/upstream.json）：

  私有源（30 个）    url -> 本仓库文件。自研修复或比官方更新，绝不能被官方覆盖。
  跟随官方源（24 个） url -> 官方 jsdelivr 文件。内容与官方一致，
                     让 App 的「检查更新」仍能从官方拿到新版。

用法
----
    python3 tools/set_url.py https://raw.githubusercontent.com/<用户>/<仓库>/main
    python3 tools/set_url.py --show         # 查看当前 url 与分类
    python3 tools/set_url.py --restore      # 还原为改动前的备份
"""
import json
import os
import re
import shutil
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKUP = os.path.join(REPO, ".url-backup")
UPSTREAM_FILE = os.path.join(REPO, "tools", "upstream.json")


def load_upstream():
    """返回 (跟随官方的文件名集合, 官方 base)。"""
    if not os.path.exists(UPSTREAM_FILE):
        return set(), ""
    d = json.load(open(UPSTREAM_FILE, encoding="utf-8"))
    return set(d.get("upstream", [])), d.get("officialBase", "").rstrip("/")


def source_files():
    idx_path = os.path.join(REPO, "index.json")
    if os.path.exists(idx_path):
        idx = json.load(open(idx_path, encoding="utf-8"))
        return [e["fileName"] for e in idx]
    return sorted(f for f in os.listdir(REPO) if f.endswith(".js") and not f.startswith("_"))


"""匹配类体顶层的 url 字段，兼容两种官方写法：

    url = "https://.../x.js";          // 单行
    url =                              // 两行（官方 jcomic/zaimanhua/comic_walker 等）
      "https://.../x.js";

缩进限制在 8 空格以内以避免误匹配方法体内的赋值；由于取第一个匹配，
类字段一定先于任何方法体出现。
"""
URL_RE = re.compile(
    r'^(?P<indent>[ \t]{0,8})url[ \t]*=[ \t]*'
    r'(?P<nl>\r?\n[ \t]*)?'
    r'(?P<q>["\'])(?P<val>[^"\']*)(?P=q)',
    re.M,
)


def top_level_url(text):
    m = URL_RE.search(text)
    return (m.group("val"), m.span()) if m else (None, None)


def set_url(text, value):
    def repl(m):
        indent, q, nl = m.group("indent"), m.group("q"), m.group("nl")
        if nl:                       # 保持原有的换行与缩进风格
            return f'{indent}url ={nl}{q}{value}{q}'
        return f'{indent}url = {q}{value}{q}'

    new, n = URL_RE.subn(repl, text, count=1)
    if n:
        return new

    m = re.search(r'^([ \t]{0,8})key[ \t]*=[ \t]*["\'][^"\']*["\']', text, re.M)
    if not m:
        raise RuntimeError("找不到顶层 key 字段，无法定位插入点")
    indent = m.group(1)
    return text[: m.end()] + f'\n\n{indent}url = "{value}"' + text[m.end():]


def main():
    args = sys.argv[1:]
    upstream, official_base = load_upstream()

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
        print(f"{'文件':<32}{'类型':<12}{'顶层 url'}")
        print("-" * 116)
        bad = []
        for f in files:
            p = os.path.join(REPO, f)
            if not os.path.exists(p):
                continue
            url, _ = top_level_url(open(p, encoding="utf-8").read())
            kind = "跟随官方" if f in upstream else "私有"
            print(f"{f:<32}{kind:<12}{url or '(空)'}")
            if url and not re.search(r'\.js(\?|$)', url):
                bad.append((f, url))
        print()
        print(f"私有 {len([f for f in files if f not in upstream])} 个 / 跟随官方 {len([f for f in files if f in upstream])} 个")
        if bad:
            print("\n⚠ 以下 url 疑似指向网页而非 .js 更新地址，更新时会先删源再失败：")
            for f, u in bad:
                print(f"    {f}: {u}")
        return

    base = args[0].rstrip("/")
    if not base.startswith(("http://", "https://")):
        print(f"✗ 仓库地址必须以 http:// 或 https:// 开头: {base}")
        sys.exit(1)

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
        if f in upstream and official_base:
            new_url = f"{official_base}/{f}"
        else:
            new_url = f"{base}/{f}"

        text = open(p, encoding="utf-8").read()
        old, _ = top_level_url(text)
        if old == new_url:
            continue
        open(p, "w", encoding="utf-8").write(set_url(text, new_url))
        changed += 1
        tag = "跟随官方" if f in upstream else "私有    "
        print(f"  ✓ [{tag}] {f}\n      {old or '(空)'}\n   -> {new_url}")

    print(f"\n✓ 已更新 {changed} 个源")
    print(f"    私有源 -> {base}")
    print(f"    跟随官方源 -> {official_base}")
    print("\n注意：源文件内容已改变，但 version 字段刻意未变。")
    print("原因见 README「版本策略」：App 的 update() 会先 remove() 再下载，")
    print("对已安装旧 url 的用户贸然提升版本会导致更新失败并丢失源。")


if __name__ == "__main__":
    main()
