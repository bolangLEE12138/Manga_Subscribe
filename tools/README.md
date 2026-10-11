# tools 说明

| 脚本 | 作用 | 命令 |
|---|---|---|
| `upstream.json` | **配置文件**：定义哪些源跟随官方更新。不在此列表 = 私有源 | — |
| `validate.js` | Venera 兼容性校验（L1 语法 → L5 设置），用最小运行时仿真复现 App 的加载流程 | `node tools/validate.js` |
| `gen_index.py` | 从源文件重新生成 `index.json`，`name`/`key`/`version` 一律读取源文件 | `python3 tools/gen_index.py` |
| `set_url.py` | 按 upstream.json 分类设置每个源的 `url`：私有 → 本仓库，跟随官方 → 官方 | `python3 tools/set_url.py <仓库地址>` |
| `sync_official.py` | 把「跟随官方」的源同步到官方最新版 | `python3 tools/sync_official.py` |
| `subscribe_url.sh` | 生成带绕缓存参数的订阅地址（`?v=<commit>`） | `bash tools/subscribe_url.sh` |
| `clean_backup.py` | 清理 `.venera` 备份里重复的源文件（清理 iOS 设备上的重复源） | `python3 tools/clean_backup.py <备份.venera>` |

## 清理 iOS 设备上重复的源文件

### 为什么会重复

App 的「添加源」在目标文件名已存在时，会依次尝试 `名字(0).js`、`名字(1).js`……
（`parser.dart: createAndParse`）。反复添加同一个源，就会在 `comic_source/` 里堆出多份同 key 的文件。

App 启动时按文件系统顺序逐个解析，**第一个成功的占住 key，其余全部以
「该漫画源已存在」失败**。这些失败的文件不会出现在 App 的源列表里，无法在 App 内删除。

实测案例（2026-10-11 设备日志）：9 个 `komiic*.js`、2 个 `copy_manga_multi_accounts*.js`
全部因 key 冲突加载失败，只有 `komiic(0).js` 生效。

### 为什么不能直接用 Finder / 文件 App 删

iOS 文件共享（`UIFileSharingEnabled`）只开放 `Documents/`，
而源文件在 `<App容器>/Library/Application Support/comic_source/`，看不到。

### 正确做法：借备份通道清理

App 导入备份时（`data.dart: importAppData`）会**先把整个 `comic_source/` 目录删掉再重建**，
只复制备份里的文件：

```dart
Directory(.../comic_source).deleteIfExistsSync(recursive: true);
Directory(.../comic_source).createSync();
for (file in 备份里的 comic_source) { await file.copy(target); }
```

而导出时（`data.dart: exportAppData`）是 `listSync()` **打包整个目录**，
所以重复文件确实会进备份——正好可以借这条通道把它们筛掉。

### 操作步骤

1. App 内 **设置 → 备份与恢复 → 导出**，得到 `data.venera`
2. 传到 Mac（AirDrop 或「文件」App）
3. 先预览，确认要删哪些：

   ```bash
   python3 tools/clean_backup.py data.venera
   ```

4. 确认无误后写出清理版：

   ```bash
   python3 tools/clean_backup.py data.venera --apply
   ```

5. 把生成的 `data.cleaned.venera` 传回手机，**设置 → 备份与恢复 → 导入**

保留哪一个的规则：**版本号高者优先；版本相同则不带 `(N)` 后缀者优先**。
可用 `--keep 文件名` 强制保留、`--remove 文件名` 强制删除。
脚本会同步更新 `manifest.json` 并做 zip 自检。

> 导入会重建整个 `comic_source` 目录，所以**清理前请确认清空的文件都是你不要的**。
> 建议先留一份原始备份。

## 订阅地址为什么要绕缓存

仓库更新后，中间层可能仍在返回旧内容：

| 层 | 缓存时长 |
|---|---|
| `raw.githubusercontent.com` | 约 5 分钟 |
| `cdn.jsdelivr.net` 的 `@main` | **最长约 12 小时** |
| App 的 `NetworkCacheManager` | 内存缓存，重启可清 |

**实测踩过的坑**：源从 30 个扩到 54 个之后，raw 地址已是 54 条，jsDelivr 却仍返回 30 条。

`tools/subscribe_url.sh` 会在地址后拼 `?v=<commit 短哈希>` 来绕过全部缓存。
这样做是安全的——App 解析源文件用的是
`地址.substring(0, 地址.lastIndexOf("/") + 1) + fileName`，
最后一个 `/` 在 `index.json` 之前，查询参数会被自然丢弃：

```
https://raw.githubusercontent.com/.../main/index.json?v=0b8391e
  -> base = https://raw.githubusercontent.com/.../main/
  -> jm.js = https://raw.githubusercontent.com/.../main/jm.js   ✓
```

```bash
bash tools/subscribe_url.sh              # raw（推荐）
bash tools/subscribe_url.sh --jsdelivr   # jsDelivr
bash tools/subscribe_url.sh --plain      # 不带缓存戳
```

## 为什么需要区分私有源和跟随官方的源

App 的更新是**两条独立链路**（见 App 源码 `lib/pages/comic_source_page.dart` 与 `parser.dart`）：

```
1. 要不要更新？  checkComicSourceUpdate() 读 comicSourceListUrl（= 本仓库 index.json）
                 比较 versions[key] 与本地 version，严格大于才提示
2. 从哪里下载？  ComicSourcePage.update() 读【已安装源自身的 url 字段】
                 ⚠ 而且是先 remove() 删源，再下载；下载/解析失败 = 源丢失
```

所以：

| 类型 | index.json 版本号 | 源内 url | 效果 |
|---|---|---|---|
| 私有源 | 自己维护 | 本仓库 | 官方永远覆盖不到你的修复 |
| 跟随官方源 | 由 `sync_official.py` 同步 | 官方 jsdelivr | 官方发新版 → 提示更新 → 下到官方新版 |

**只维护其中一条链路不会生效**：版本号没同步就永不提示；url 不指官方就会下到别处。

## 推荐工作流

```bash
# 改动私有源后：
#   1) 先提升该源的 version（否则 App 不会提示更新）
python3 tools/gen_index.py      # 2) 重新生成清单
node tools/validate.js          # 3) 必须全绿才能提交
git add -A && git commit -m "fix: <源名> <改动说明>" && git push

# 定期同步官方源：
python3 tools/sync_official.py --check   # 先看有没有新版
python3 tools/sync_official.py           # 同步
python3 tools/gen_index.py && node tools/validate.js
git add -A && git commit -m "chore: 同步官方源" && git push
```

## 新增源时的归属判断

- **与官方内容一致** → 加进 `tools/upstream.json` 的 `upstream` 数组
- **自研 / 修复 / 官方没有** → 什么都不用加（默认即私有）
- **拿不准** → 按私有处理。宁可不自动更新，也不要被官方静默覆盖

> 反例警示：`comic_walker.js`、`shonen_jump_plus.js` 的版本号与官方**完全相同**，内容却是修复版。
> 因为版本号相同，App 永不提示更新，一旦 url 指官方，任何更新都会把修复换掉。
> 这就是必须有 `upstream.json` 白名单的原因。

## 校验器覆盖范围

| 级别 | 检查内容 |
|---|---|
| L1 | JavaScript 语法 |
| L2 | 类识别（`extends ComicSource`）、实例化、是否误声明多个源类 |
| L3 | `name` / `key` / `version` / `minAppVersion` / `url` 字段合法性 |
| L4 | `explore` / `category` / `search` / `comic` 结构；`explore.type` 取值是否被 App 接受 |
| L4b | `url` 是否疑似指向网页而非 `.js` 更新地址 |
| L5 | `settings` 各项是否有 `title` / 合法 `type` / `default` |

仓库级：`index.json` 结构、`key` 与 `fileName` 唯一性、文件存在性、游离文件、
以及清单与源文件 `name`/`key`/`version` 的交叉一致性。
