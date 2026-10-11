#!/usr/bin/env python3
"""
把「跟随官方」的源同步到官方 venera-configs 最新版。

背景（来自 App 源码，非推测）
----------------------------
App 的更新判定是两条独立链路：

  1. 比对版本：checkComicSourceUpdate() 拉取 comicSourceListUrl（= 本仓库 index.json），
     对每个已安装源比较 versions[key] 与本地 version，
     `compareSemver(仓库版本, 本地版本)` 为真才提示更新。
  2. 实际下载：ComicSourcePage.update() 从 **源自身的 url 字段** 下载。

所以本仓库要同时做到：
  - index.json 里的版本号跟得上官方  -> 才会提示更新（靠本脚本）
  - 源文件的 url 指向官方文件         -> 才会真的下到新版（靠 set_url.py）

只做其中之一都不生效：版本号不同步就永不提示；url 不指官方就会下到别处。

用法
----
    python3 tools/sync_official.py           # 检查并同步
    python3 tools/sync_official.py --check   # 只检查，不写入

同步后请执行：
    python3 tools/gen_index.py && node tools/validate.js
"""
import json
import os
import re
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPSTREAM_FILE = os.path.join(REPO, "tools", "upstream.json")
UA = {"User-Agent": "Mozilla/5.0 (compatible; venera-repo-sync/1.0)"}


def fetch(url, timeout=40):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def meta_of(text):
    """读取源文件顶层的 name / key / version。"""
    def f(n):
        m = re.search(rf'^[ \t]{{0,8}}{n}[ \t]*=[ \t]*["\']([^"\']*)["\']', text, re.M)
        return m.group(1) if m else ""
    return {"name": f("name"), "key": f("key"), "version": f("version")}


def main():
    check_only = "--check" in sys.argv

    cfg = json.load(open(UPSTREAM_FILE, encoding="utf-8"))
    upstream = cfg["upstream"]
    base = cfg["officialBase"].rstrip("/")

    print(f"官方仓库: {base}")
    print(f"跟随官方的源: {len(upstream)} 个\n")

    # 官方 index.json，用于交叉核对版本
    try:
        off_index = {e["fileName"]: e for e in json.loads(fetch(f"{base}/index.json"))}
    except Exception as e:
        print(f"✗ 拉取官方 index.json 失败: {e}")
        sys.exit(1)

    print(f"{'文件':<26}{'本地版本':<12}{'官方版本':<12}{'结果'}")
    print("-" * 72)

    changed, same, problems = [], [], []

    for f in upstream:
        path = os.path.join(REPO, f)
        if not os.path.exists(path):
            print(f"{f:<26}{'-':<12}{'-':<12}✗ 本地文件不存在")
            problems.append(f)
            continue

        local_text = open(path, encoding="utf-8").read()
        local = meta_of(local_text)

        try:
            off_text = fetch(f"{base}/{f}")
        except Exception as e:
            print(f"{f:<26}{local['version']:<12}{'ERR':<12}✗ 拉取失败: {e}")
            problems.append(f)
            continue

        off = meta_of(off_text)
        off_idx_ver = (off_index.get(f) or {}).get("version", "")

        # 官方 index.json 与官方文件自述版本不一致时给出警报
        if off_idx_ver and off["version"] and off_idx_ver != off["version"]:
            print(f"{f:<26}{local['version']:<12}{off['version']:<12}"
                  f"! 官方 index.json 写的是 {off_idx_ver}，与文件内版本不一致")

        # key 必须与官方一致，否则可能覆盖错源
        if off["key"] and off["key"] != local["key"]:
            print(f"{f:<26}{local['version']:<12}{off['version']:<12}"
                  f"✗ KEY 不一致 本地={local['key']} 官方={off['key']}")
            problems.append(f)
            continue

        if off["version"] == local["version"]:
            print(f"{f:<26}{local['version']:<12}{off['version']:<12}✓ 已是最新")
            same.append(f)
            continue

        if not check_only:
            with open(path, "w", encoding="utf-8") as fp:
                fp.write(off_text)
        print(f"{f:<26}{local['version']:<12}{off['version']:<12}"
              f"{'→ 已更新' if not check_only else '→ 待更新'}")
        changed.append((f, local["version"], off["version"]))

    print("-" * 72)
    print(f"  最新: {len(same)}   更新: {len(changed)}   异常: {len(problems)}")

    if changed and not check_only:
        print("\n请继续执行，把新版本号写进 index.json 并做回归：")
        print("    python3 tools/gen_index.py && node tools/validate.js")
        print("然后提交：")
        print("    git add -A && git commit -m 'chore: 同步官方源 <版本>' && git push")
    elif changed:
        print("\n（--check 模式，未写入任何文件）")

    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
