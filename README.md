# Venera 一键整合源仓库

自用的 Venera / 漫阅 漫画源集合，共 **54 个源**，已通过 Venera 兼容性校验（54/54）。

其中分为两类：

| 类型 | 数量 | 说明 | 更新地址指向 |
|---|---:|---|---|
| **私有源** | 30 | 自研修复版，或比官方更新、官方缺少的源 | 本仓库 |
| **跟随官方源** | 24 | 内容与官方一致，收录进来只为了让「一个订阅地址覆盖全部」 | 官方 jsdelivr |

之所以要分两类，是因为 **App 的源清单地址只能填一个**（`appdata.settings['comicSourceListUrl']` 是单个字符串）。
若只收录私有源，切换订阅地址后官方那 24 个源就会从可添加列表里消失。

本仓库解决三个问题：

1. **旧订阅地址（`git.nyne.dev/nyne/venera-configs`）是官方仓库的陈旧镜像**，最后更新于 2026-03-19，多个源仍停留在失效域名（如拷贝漫画的 `copymanga.com` 已 DNS 失效）。
2. **散落在多个第三方仓库里的私有修复版无法统一管理**，重装 App 后难以恢复。
3. **部分私有修复版比官方更新**（拷贝漫画 1.6.6 vs 官方 1.4.2），一旦从官方地址更新就会被降级覆盖。

---

## 一、目录结构

```
.
├── index.json                  # 源清单，App 订阅的就是这个文件
├── *.js                        # 54 个源文件，必须与 index.json 同目录
├── tools/
│   ├── upstream.json           # 「哪些源跟随官方」的名单（私有/官方分界）
│   ├── validate.js             # 本地兼容性校验器（Node.js）
│   ├── gen_index.py            # 从源文件重新生成 index.json
│   ├── set_url.py              # 按分类设置每个源的 url 字段
│   ├── sync_official.py        # 把「跟随官方」的源同步到官方最新版
│   └── validation-report.txt   # 最近一次校验报告
└── README.md
```

> **关键约束**：App 取源文件的逻辑是
> `listUrl.substring(0, listUrl.lastIndexOf("/") + 1) + fileName`
> （见 App 源码 `lib/pages/comic_source_page.dart`）。
> 因此 **`.js` 文件必须与 `index.json` 位于同一目录**，不能放进子目录。

---

## 二、部署与订阅

> **本仓库已配置完成**，部署地址为 `github.com/bolangLEE12138/Manga_Subscribe`。

### 1. 在 App 中订阅

源清单地址填：

```
https://raw.githubusercontent.com/bolangLEE12138/Manga_Subscribe/main/index.json
```

若 `raw.githubusercontent.com` 在你的网络下不通，改用 jsDelivr 镜像：

```
https://cdn.jsdelivr.net/gh/bolangLEE12138/Manga_Subscribe@main/index.json
```

> jsDelivr 对 `@main` 有缓存（最长约 12 小时）。改了源需要立刻生效时用 raw 地址，
> 或改用 commit hash / tag 固定版本。

### 2. 源的更新地址

30 个源的顶层 `url` 已全部指向本仓库的原始文件地址，用
`python3 tools/set_url.py --show` 可复查，`--restore` 可回滚。

**为什么必须做**：`copy_manga` / `komiic` / `manwaba` / `ykmh` 原本指向官方 jsDelivr，
而它们的版本比官方新——一旦在 App 内触发更新，会被**降级覆盖**成官方旧版。

若以后仓库改名或迁移，只需重跑：

```bash
python3 tools/set_url.py <新的仓库地址>
git add -A && git commit -m "chore: 更新源地址" && git push
```

### 3. 推送到 GitHub（首次）

```bash
git remote add origin git@github.com:bolangLEE12138/Manga_Subscribe.git
git push -u origin main
```

> 仓库必须为 **Public**。私有仓库的 raw 地址需要 token，App 不支持。

---

## 三、收录清单（54 个源）

### 私有源（30 个）—— url 指向本仓库，绝不能被官方覆盖

#### A 组：官方仓库没有的源（23 个）

| 源 | 文件 | key | 版本 |
|---|---|---|---|
| 嗶哩漫畫 | `bilimanga.js` | `bilimanga` | 1.1.3 |
| 动漫屋 | `dm5.js` | `dm5` | 7.0.2 |
| 动漫啦 | `dongman_la.js` | `dongman_la` | 1.0.1 |
| 咚漫 | `dongmanmanhua.js` | `dongmanmanhua` | 1.0.6 |
| 飞翔漫画 | `ffppt.js` | `ffppt` | 1.0.1 |
| 古风漫画 | `gfmh.js` | `GfmhApp` | 1.3.0 |
| 瓜子漫画 | `guazi_manhua.js` | `guazimanhua` | 1.0.4 |
| 嬉皮漫畫 | `hipmh.js` | `hipmh` | 1.0.1 |
| 来漫画（分流） | `laimanhua_split_hosts.js` | `laimanhua_split` | 1.2.1 |
| 51漫画 | `manga51.js` | `manga51` | 1.2.0 |
| 香蕉漫画 | `manhuauo_banana.js` | `manhuauo_banana_v2` | 1.0.3 |
| 漫网 | `manwang.js` | `manwang` | 1.2.0 |
| 4399漫画网 | `mh4399.js` | `mh4399` | 1.0.3 |
| MOJOIN | `mojoin.js` | `mojoin_v2` | 1.0.7 |
| NoyManga | `noymanga.js` | `noymanga` | 1.1.3 |
| Rawkuma | `rawkuma.js` | `rawkuma` | 1.1.0 |
| 如漫画 | `rumanhua.js` | `rumanhua_fixed_v15` | 1.2.7 |
| SF漫画 | `sfacg_manhua.js` | `sfacg_manhua` | 1.0.0 |
| 腾讯动漫（正版） | `tencent_comic_official.js` | `qq_comic_official_v1` | 1.0.3 |
| 图库漫画 | `tuku_cc.js` | `tuku_cc` | 1.0.1 |
| LINE WEBTOON | `webtoons_zh_hant.js` | `webtoons_zh_hant` | 1.0.0 |
| W漫画 | `wmanhua.js` | `wmanhua` | 1.0.1 |
| zero搬运网 | `zerobyw33.js` | `zerobyw33` | 1.2.0 |


#### B 组：比官方更新的修复版（5 个）

| 源 | 文件 | key | 版本 |
|---|---|---|---|
| 拷贝漫画 | `copy_manga.js` | `copy_manga` | 1.6.6 |
| 爱看漫 | `ikmmh_v2.js` | `ikmmh_v2` | 3.0.0 |
| Komiic | `komiic.js` | `Komiic` | 1.0.8 |
| 漫蛙吧 | `manwaba.js` | `manwaba` | 1.1.3 |
| 优酷漫画 (修复版) | `ykmh.js` | `ykmh` | 1.0.6 |


#### C 组：版本号与官方相同、但内容是修复版（2 个）⚠️

这两个源最容易被静默降级：**版本号与官方一模一样，App 不会提示更新**，如果 url 指向官方，任何一次更新都会把修复换掉。

| 源 | 文件 | key | 版本 |
|---|---|---|---|
| カドコミ | `comic_walker.js` | `comic_walker` | 1.0.1 |
| 少年ジャンプ＋ | `shonen_jump_plus.js` | `shonen_jump_plus` | 1.1.1 |


- `comic_walker.js`：用 `latestVersion = "1.6.4"` 并在 `init()` 里从 App Store 自动获取最新版本。
  官方仍硬编码 `1.4.13`，而服务端会以 `upgrade_required` 拒绝旧版本 UA，导致 token 刷新失败。
- `shonen_jump_plus.js`：`latestVersion = "4.5.24"`，官方是 `4.0.24`。

### 跟随官方源（24 个）—— url 指向官方 jsdelivr，由 sync_official.py 同步

| 源 | 文件 | key | 版本 |
|---|---|---|---|
| 百合会 | `baihehui.js` | `baihehui` | 1.0.0 |
| 包子漫画 | `baozi.js` | `baozi` | 1.1.6 |
| CCC追漫台 | `ccc.js` | `ccc` | 1.0.1 |
| comick | `comick.js` | `comick` | 1.2.0 |
| ehentai | `ehentai.js` | `ehentai` | 1.2.0 |
| GoDa漫画 | `goda.js` | `goda` | 1.2.1 |
| H-Comic | `hcomic.js` | `hcomic` | 1.0.0 |
| hitomi.la | `hitomi.js` | `hitomi` | 1.1.2 |
| 热辣漫画 | `hot_manga.js` | `hot_manga` | 1.0.0 |
| jcomic.net | `jcomic.js` | `jcomic` | 1.0.0 |
| 禁漫天堂 | `jm.js` | `jm` | 1.4.0 |
| Kavita | `kavita.js` | `kavita` | 1.0.0 |
| Komga | `komga.js` | `komga` | 1.0.0 |
| MangaDex | `manga_dex.js` | `manga_dex` | 1.2.0 |
| 漫画柜 | `manhuagui.js` | `ManHuaGui` | 1.2.1 |
| 漫画人 | `manhuaren.js` | `manhuaren` | 1.0.0 |
| 漫画1234 | `mh1234.js` | `mh1234` | 1.0.0 |
| 18漫画 | `mh18.js` | `mh18` | 1.0.0 |
| 漫小肆 | `mxs.js` | `mxs` | 1.0.0 |
| MYCOMIC | `mycomic.js` | `mycomic` | 1.1.0 |
| nhentai | `nhentai.js` | `nhentai` | 1.1.0 |
| Picacg | `picacg.js` | `picacg` | 1.0.6 |
| 紳士漫畫 | `wnacg.js` | `wnacg` | 1.0.6 |
| 再漫画 | `zaimanhua.js` | `zaimanhua` | 1.0.2 |

---

## 四、必须先读：App 的三个关键机制

以下结论来自 Venera 源码 `lib/foundation/comic_source/parser.dart` 与
`lib/pages/comic_source_page.dart`，不是推测。

### 机制 1：重复 key 会导致「添加」直接报错

```dart
for (var source in ComicSource.all()) {
  if (source.key == key) {
    throw ComicSourceParseException("key($key) already exists");
  }
}
```

**从源清单里点「添加」时，如果该 key 已安装，会直接失败**，而不是覆盖。

### 机制 2：「检查更新」会先删除源，再下载

```dart
if (!source.url.isURL) { ... "Invalid url config"; return; }
ComicSourceManager().remove(source.key);           // ← 先删
var res = await AppDio().get<String>(source.url);  // ← 再下载
await ComicSourceParser().parse(res.data!, ...);   // ← 失败则源已丢失
```

**推论（很重要）**：
- `url` 字段必须是 `.js` 文件的地址。若填成漫画网站首页，更新时会下载 HTML、解析失败，**结果是源被删除**。
- 若 `url` 指向别人的仓库，你的私有修复版会被**覆盖成对方的版本**。

本仓库已修正 4 个此类错误（`dm5`、`gfmh`、`ikmmh_v2`、`rawkuma` 原本把漫画网站首页写进了 `url`）。

### 机制 3：源清单只用于比对版本，实际下载走源自身的 `url`

```dart
versions[source['key']] = source['version'];   // 清单提供版本号
// 仅在 compareSemVer(清单版本, 已安装版本) 为真时提示更新
```

也就是说：**`index.json` 决定「要不要更新」，源文件里的 `url` 决定「从哪里更新」**。两者缺一不可。

---

## 五、迁移到你现有的 App

你当前 App 里**已经装有这些源**（来自 `.venera` 备份），因此请注意：

### 情况一：全新安装 / 换机（推荐路径）

没有 key 冲突，直接订阅源清单地址，逐个点「添加」即可，30 个源全部可装。

### 情况二：在现有安装上切换订阅地址

1. 先把 App 的源清单地址改成你的新仓库地址。
2. **`manga_dex` 和 `wnacg` 会显示可更新**（1.1.1→1.2.0、1.0.5→1.0.6），可以直接在 App 内更新。
3. 其余 28 个源版本与你本地一致，**不会提示更新，也不需要动**——它们本来就是同一份文件。
4. 若你想让某个源改用本仓库的 `url`（从而获得后续自动更新能力），需要**先删除该源，再从新仓库添加**。原因见机制 1。

> **不要**为了强制触发更新而手动抬高 `version`。机制 2 决定了：一旦本地源的 `url` 有误或指向别处，更新会在删源后失败，源就丢了。详见下一节。

---

## 六、版本策略（为什么没有统一升版本号）

本仓库私有源的 `version` 与你 `.venera` 备份中的**完全一致**，这是刻意的：

- App 的更新判定是 `compareSemVer(清单版本, 已安装版本)`，仅在**严格大于**时才提示更新。
- 若为了「强制迁移」而抬高版本，App 会走机制 2：先删源，再用**已安装源里的旧 `url`** 下载。
- 对于原本 `url` 填错的源，这一步必然失败，**源会被删除**。

因此正确做法是：保持版本不变，通过「删除 + 重新添加」完成迁移；之后源文件内的 `url` 已指向本仓库，未来的版本提升才能安全生效。

### 但有一个反例必须记住：版本号相同 ≠ 内容相同

`comic_walker.js` 和 `shonen_jump_plus.js` 的**版本号与官方完全相同**，内容却是修复版。

| 源 | 版本号 | 你的修复版 | 官方 |
|---|---|---|---|
| `comic_walker.js` | 都是 `1.0.1` | `latestVersion = "1.6.4"` + App Store 自动获取 | `latestVersion = "1.4.13"` |
| `shonen_jump_plus.js` | 都是 `1.1.1` | `latestVersion = "4.5.24"` | `latestVersion = "4.0.24"` |

因为版本号一样，App **永远不会提示更新**，所以一旦这两个源的 `url` 指向官方，
任何一次手动或自动更新都会把修复悄悄换成官方旧版。

**这就是 `tools/upstream.json` 存在的意义**：把「跟随官方」和「私有」的边界写死成配置，
让 `set_url.py` 和 `sync_official.py` 都不会误伤私有源。
新增源时如果拿不准，默认归入私有（不列入 upstream），宁可不自动更新也不要被覆盖。

---

## 七、已知限制

### 带设置项的源（全部有默认值，安装即可用）

不存在「必须先配置才能安装」的源。以下设置项均有合理默认值，按需调整即可：

| 源 | 设置项 |
|---|---|
| `copy_manga` | 收藏排序、设备指纹重置（谨慎开启）、虚拟 IP 轮换（实验性）、CDN 线路、图片质量、搜索方式、API 地址、重置设备指纹池 |
| `wnacg` | 刷新域名列表、启动时刷新、域名选择、自定义域名 |
| `noymanga` | 账号登录、签到、自动签到、连接测试 |
| `laimanhua_split_hosts` | 搜索域名、主页域名 |
| `komiic` | API 域名（默认 `komiic.cc`） |
| `dm5` | 主域名（默认 `m.dm5.com`） |
| `ikmmh_v2` | 站点地址（须本机浏览器可直连） |
| `rawkuma` | 站点域名（默认 `rawkuma.net`） |
| `manwang` | 搜索 Cookie（可选，效果待验证） |
| `zerobyw33` | 刷新域名 |
| `manga_dex` | 图片质量 |
| `manhuauo_banana` / `rumanhua` | 图片质量 |
| `webtoons_zh_hant` | 是否显示官方版权提示图 |

需要登录才能阅读的源：`copyright` 类如 `bilimanga`（嗶哩漫畫）、`copy_manga`（部分内容）、
`nhentai` / `ehentai` / `jm`（禁漫天堂需自己在源设置里配置）、`picacg`（需账号）。

### 数据文件（`.data`）

部分源会把登录态或缓存写入 `comic_source/<key>.data`（如 `copy_manga`、`komiic`、`noymanga`、`rawkuma`、`zerobyw33`、`picacg`、`jm`）。
这些文件是**用户本地数据，不需要、也不应该放进本仓库**——App 会在首次使用时自动创建。
发布仓库只包含 `.js` 文件。

### 站点侧限制（源无法解决）

- **Cloudflare 403**：`ikmmh_v2`、`manhuauo_banana`、`ykmh`、`baozi` 等。多为网络出口/地区问题，与源无关；`ykmh` 在中国大陆通常需要代理。
- **地区限制**：`ehentai` 在部分地区返回 451；`nhentai` / `jm` 对部分地区 403。
- **正版权限**：`tencent_comic_official` 只返回站点标记为可读的章节，付费章节请使用官方客户端。这是刻意设计的边界，不会绕过。
- **搜索接口失效**：`manwang` 官方搜索接口长期不稳定（返回 0 结果或「搜索繁忙」），源已内置站内目录兜底；但无法凭空恢复服务器没有提供的索引。
- **需要自建服务**：`kavita`、`komga` 需要你自己的服务器地址，`lanraragi` 同理（本仓库未收录 lanraragi）。

### 与官方仓库同名 key 的源

本仓库有 7 个私有源的 key 与官方重合：
`copy_manga`、`Komiic`、`manwaba`、`ykmh`、`comic_walker`、`shonen_jump_plus`，
以及内容取自官方的 `manga_dex`、`wnacg`。

**不要同时订阅官方仓库和本仓库**——App 只支持一个清单地址，混用会让更新来源互相打架。


---

## 八、维护流程

### 改动私有源

```bash
# 1. 提升该源的 version（必须，否则 App 不会提示更新）
# 2. 重新生成 index.json（脚本会从源文件读取 name/key/version，避免手写不一致）
python3 tools/gen_index.py

# 3. 跑兼容性校验
node tools/validate.js

# 4. 提交
git add -A && git commit -m "fix: <源名> <改动说明>" && git push
```

### 同步官方源（24 个跟随官方的源）

定期执行，把官方的新版本拉下来：

```bash
python3 tools/sync_official.py --check   # 先看有没有新版
python3 tools/sync_official.py           # 真正同步
python3 tools/gen_index.py               # 新版本号写进 index.json
node tools/validate.js                   # 必须全绿
git add -A && git commit -m "chore: 同步官方源" && git push
```

两条链路缺一不可，原因见第四节机制 3：

| 环节 | 由谁负责 | 作用 |
|---|---|---|
| `index.json` 版本号 | `sync_official.py` + `gen_index.py` | 决定**要不要**提示更新 |
| 源文件内的 `url` | `set_url.py` + `upstream.json` | 决定**从哪里**下载 |

### 新增源

1. 把 `.js` 放进仓库根目录
2. 判断归属：**与官方内容一致** → 加进 `tools/upstream.json` 的 `upstream` 数组；
   **自研/修复/官方没有** → 什么都不用加（默认即私有）。拿不准就按私有处理。
3. `python3 tools/gen_index.py`
4. `node tools/validate.js`（必须全绿）
5. `git add -A && git commit && git push`

`tools/gen_index.py` 的设计原则：**`name` / `key` / `version` 一律从源文件内读取，绝不手写**。
手写 index.json 极易造成清单与源文件不一致，导致 App 显示错误版本或拒绝加载。

### 校验器做了什么

`tools/validate.js` 用最小 Venera 运行时仿真复现 App 的加载流程，逐源执行五级检查：

| 级别 | 检查内容 |
|---|---|
| L1 | JavaScript 语法 |
| L2 | 类识别（`extends ComicSource`）、实例化、是否误声明多个源类 |
| L3 | `name` / `key` / `version` / `minAppVersion` / `url` 字段合法性 |
| L4 | `explore` / `category` / `search` / `comic` 能力声明与结构；`explore.type` 是否为 App 接受的取值 |
| L4b | `url` 是否疑似指向网页而非 `.js` 更新地址 |
| L5 | `settings` 各项是否有 `title` / 合法 `type` / `default`（首次安装安全性） |

另含仓库级检查：`index.json` 结构、`key` 唯一性、`fileName` 唯一性、文件存在性、游离文件、
清单与源文件的 `name` / `key` / `version` 交叉一致性。

---

## 九、改动记录

### 第二批：补录官方源，凑齐 54 个

| 改动 | 依据 | 影响范围 |
|---|---|---|
| 补录 24 个「跟随官方」的源 | 用户反馈 `jm`、`picacg` 等缺失；App 只能订阅一个清单地址，不收录就会从列表消失 | +24 个源 |
| 引入 `tools/upstream.json` 区分私有/官方 | 防止 `set_url.py` 把跟随官方的源错改成本仓库地址，也防止将来误伤私有源 | 工具链 |
| 新增 `tools/sync_official.py` | App 的更新提示靠 index.json 版本号，实际下载靠源内 `url`，两者必须一起维护 | 工具链 |
| **`comic_walker` / `shonen_jump_plus` 归入私有** | 版本号与官方相同但内容是修复版：官方 `1.4.13` 会被服务端以 `upgrade_required` 拒绝；`shonen_jump_plus` 官方为 `4.0.24`（修复版 `4.5.24`）。版本号相同 → App 永不提示更新 → 跟官方同步就是静默降级 | 2 个源 |
| `set_url.py` 支持两行 `url =` 写法 | 官方 `jcomic` / `zaimanhua` / `comic_walker` / `shonen_jump_plus` 用值换行的写法，原正则匹配不到 | 工具链 |

### 第一批：建立 30 源仓库

| 改动 | 依据 | 影响范围 |
|---|---|---|
| 建立统一源仓库 | 用户 `.venera` 备份 + 官方 venera-configs | 全部 |
| `manga_dex` 用官方 1.2.0 | 官方版本高于备份中的 1.1.1 | 1 个源 |
| `wnacg` 用官方 1.0.6 | 官方版本高于备份中的 1.0.5 | 1 个源 |
| 修正 `dm5` / `gfmh` / `ikmmh_v2` / `rawkuma` 的 `url` | 原值指向漫画网站首页，触发更新会先删源后失败 | 4 个源 |
| `index.json` 由源文件自动生成 | 避免清单与源文件版本不一致 | 全部 |
| 诊断漫蛙吧封面不显示 | nyne 与官方版均无图片解密逻辑，而站点封面是 AES 加密的 | `manwaba` |


---

## 十、参考

- Venera 官方源开发文档：<https://github.com/venera-app/venera/blob/master/doc/comic_source.md>
- Venera JavaScript API：<https://github.com/venera-app/venera/blob/master/doc/js_api.md>
- 官方源仓库：<https://github.com/venera-app/venera-configs>
- 开发日志：《Venera 漫画源开发日志（统一合并版 v3）》
