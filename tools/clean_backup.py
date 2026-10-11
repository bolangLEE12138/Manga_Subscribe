#!/usr/bin/env python3
"""
清理 .venera 备份里的重复源文件。

为什么需要
----------
App 的「添加源」在目标文件名已存在时，会依次尝试 `名字(0).js`、`名字(1).js`……
（`parser.dart: createAndParse`）。多次重复添加同一个源，就会在
`comic_source/` 里堆出多份同 key 的文件。

App 启动时按文件系统顺序逐个解析，**第一个成功的占住 key，其余全部
以「该漫画源已存在」失败**，在日志里刷错误。它们不会出现在 App 的源列表里，
所以无法在 App 内直接删除。

而且在 iOS 上，源文件位于
`<App容器>/Library/Application Support/comic_source/`，
而 iOS 的文件共享只开放 `Documents/`，用 Finder / 文件 App 看不到。

解决办法（无需越狱、无需第三方工具）
------------------------------------
App 导入备份时（`data.dart: importAppData`）会：

    Directory(.../comic_source).deleteIfExistsSync(recursive: true);   // 整个删掉
    Directory(.../comic_source).createSync();
    for (file in 备份里的 comic_source) { await file.copy(target); }   // 只复制备份里的

也就是说 **导入会清空现有的 comic_source 目录**。所以：

    导出备份 -> 用本脚本删掉重复文件 -> 导入回去

流程
----
1. App 内「设置 -> 备份与恢复 -> 导出」，得到 data.venera
2. 传到 Mac（AirDrop 或 文件 App）
3. python3 tools/clean_backup.py data.venera
4. 把生成的 data.cleaned.venera 传回手机并导入

用法
----
    python3 tools/clean_backup.py <输入.venera> [-o 输出.venera]
                                  [--apply]            # 默认只预览，加 --apply 才写出
                                  [--keep 文件名]      # 强制保留某文件（可重复）
                                  [--remove 文件名]    # 强制删除某文件（可重复）
"""
import argparse
import json
import os
import re
import shutil
import sys
import zipfile

# 与 App 的 key 解析保持一致：取类体顶层的 key 字段（缩进 <= 8）
KEY_RE = re.compile(r'^[ \t]{0,8}key[ \t]*=[ \t]*["\']([^"\']*)["\']', re.M)
VER_RE = re.compile(r'^[ \t]{0,8}version[ \t]*=[ \t]*["\']([^"\']*)["\']', re.M)


def semver(v):
    """把版本号转成可比较的元组。"""
    parts = re.findall(r'\d+', v or "")
    return tuple(int(x) for x in parts) if parts else (0,)


def read_meta(data):
    """从源文件字节里读出 key / version。"""
    text = data.decode("utf-8", errors="replace")
    km = KEY_RE.search(text)
    vm = VER_RE.search(text)
    return (km.group(1) if km else ""), (vm.group(1) if vm else "")


def rank(name, version):
    """
    决定同名 key 里保留哪一个，返回排序键（越大越优先）。

    优先级：
      1. 版本号高者优先
      2. 文件名不带 (N) 后缀者优先（那是 App 自动生成的重复副本）
      3. 文件名短者优先
    """
    has_suffix = 1 if re.search(r'\(\d+\)\.js$', name) else 0
    return (semver(version), -has_suffix, -len(name))


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("input")
    ap.add_argument("-o", "--output")
    ap.add_argument("--apply", action="store_true", help="真正写出文件（默认只预览）")
    ap.add_argument("--keep", action="append", default=[], help="强制保留的文件名")
    ap.add_argument("--remove", action="append", default=[], help="强制删除的文件名")
    args = ap.parse_args()

    if not zipfile.is_zipfile(args.input):
        sys.exit(f"✗ 不是有效的 zip/备份文件: {args.input}")

    zin = zipfile.ZipFile(args.input)
    names = zin.namelist()

    # 读取所有 comic_source/*.js 的 key / version
    entries = {}          # name -> (key, version, size)
    for n in names:
        if n.startswith("comic_source/") and n.endswith(".js"):
            data = zin.read(n)
            key, ver = read_meta(data)
            entries[n] = {"key": key, "version": ver, "size": len(data)}

    print(f"备份: {args.input}")
    print(f"  条目总数: {len(names)}  源文件: {len(entries)}\n")

    # 按 key 分组
    groups = {}
    for n, m in entries.items():
        groups.setdefault(m["key"] or f"<无key:{n}>", []).append(n)

    remove_set = set()
    for extra in args.remove:
        target = extra if extra.startswith("comic_source/") else f"comic_source/{extra}"
        if target in entries:
            remove_set.add(target)
        else:
            print(f"  ! --remove 指定的文件不存在: {target}")

    print("══ 重复 key 分析 ══")
    dup_found = 0
    for key, files in sorted(groups.items()):
        if len(files) == 1:
            continue
        dup_found += 1
        # 强制保留的优先
        forced = [f for f in files if os.path.basename(f) in args.keep]
        if forced:
            best = forced[0]
        else:
            best = max(files, key=lambda f: rank(os.path.basename(f), entries[f]["version"]))
        print(f"\n  key = {key}   共 {len(files)} 个文件")
        for f in sorted(files):
            mark = "保留" if f == best else "删除"
            if f in remove_set:
                mark = "删除(--remove)"
            star = " ★" if f == best else ""
            print(f"    [{mark}] {os.path.basename(f):<34} v{entries[f]['version'] or '?':<10}{star}")
            if f != best or f in remove_set:
                remove_set.add(f)
        if best in remove_set:
            remove_set.discard(best)

    if dup_found == 0:
        print("  ✓ 没有发现重复 key，无需清理")
    if remove_set:
        print(f"\n══ 计划删除 {len(remove_set)} 个文件 ══")
        for f in sorted(remove_set):
            print(f"  - {f}")
    else:
        print("\n没有需要删除的文件。")
        if not args.apply:
            return

    # manifest.json 同步
    manifest_name = next((n for n in names if n == "manifest.json"), None)
    new_manifest = None
    if manifest_name:
        try:
            mf = json.loads(zin.read(manifest_name).decode("utf-8"))
            if isinstance(mf, dict) and isinstance(mf.get("files"), list):
                kept = [f for f in mf["files"] if f not in remove_set]
                dropped = [f for f in mf["files"] if f in remove_set]
                mf["files"] = kept
                new_manifest = json.dumps(mf, ensure_ascii=False, separators=(",", ":"))
                print(f"\n══ manifest.json ══")
                print(f"  原 {len(mf['files']) + len(dropped)} 条 -> 新 {len(kept)} 条（移除 {len(dropped)} 条）")
            else:
                print("\n! manifest.json 格式非预期，将原样保留")
        except Exception as e:
            print(f"\n! manifest.json 解析失败（{e}），将原样保留")

    if not args.apply:
        print("\n（预览模式，未写出任何文件。加 --apply 才会生成清理后的备份）")
        return

    out = args.output or os.path.splitext(args.input)[0] + ".cleaned.venera"
    tmp = out + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for n in names:
            if n in remove_set:
                continue
            if n == manifest_name and new_manifest is not None:
                zout.writestr(n, new_manifest)
            else:
                zout.writestr(n, zin.read(n))
    zin.close()
    shutil.move(tmp, out)

    # 自检
    with zipfile.ZipFile(out) as z:
        bad = z.testzip()
        cnt = sum(1 for n in z.namelist() if n.startswith("comic_source/") and n.endswith(".js"))
    if bad:
        sys.exit(f"✗ 生成的备份损坏: {bad}")

    print(f"\n✓ 已写出: {out}")
    print(f"  源文件: {cnt} 个")
    print(f"  zip 自检: 通过")
    print("\n下一步：把这个文件传回手机，在 App 的「备份与恢复 -> 导入」中选择它。")
    print("导入会清空并重建 comic_source 目录，重复文件即被彻底移除。")


if __name__ == "__main__":
    main()
