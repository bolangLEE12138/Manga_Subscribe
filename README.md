# Venera 一键整合源仓库

自用的 Venera / 漫阅 漫画源集合，共 **30 个源**，已通过 Venera 兼容性校验（30/30）。

本仓库解决三个问题：

1. **旧订阅地址（`git.nyne.dev/nyne/venera-configs`）是官方仓库的陈旧镜像**，最后更新于 2026-03-19，多个源仍停留在失效域名（如拷贝漫画的 `copymanga.com` 已 DNS 失效）。
2. **散落在多个第三方仓库里的私有修复版无法统一管理**，重装 App 后难以恢复。
3. **部分私有修复版比官方更新**（拷贝漫画 1.6.6 vs 官方 1.4.2），一旦从官方地址更新就会被降级覆盖。

---

## 一、目录结构

```
.
├── index.json                  # 源清单，App 订阅的就是这个文件
├── *.js                        # 30 个源文件，必须与 index.json 同目录
├── tools/
│   ├── validate.js             # 本地兼容性校验器（Node.js）
│   ├── gen_index.py            # 从源文件重新生成 index.json
│   ├── set_url.py              # 把所有源的 url 字段指向本仓库
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

## 三、收录清单（30 个源）

### A 组：第三方独有源（官方仓库没有，共 23 个）

| 源 | 文件 | key | 版本 | 站点实测 |
|---|---|---|---|---|
| 嗶哩漫畫 | `bilimanga.js` | `bilimanga` | 1.1.3 | 403（需登录） |
| 动漫屋 | `dm5.js` | `dm5` | 7.0.2 | 200 |
| 动漫啦 | `dongman_la.js` | `dongman_la` | 1.0.1 | 200 |
| 咚漫 | `dongmanmanhua.js` | `dongmanmanhua` | 1.0.6 | 200 |
| 飞翔漫画 | `ffppt.js` | `ffppt` | 1.0.1 | 200 |
| 古风漫画 | `gfmh.js` | `GfmhApp` | 1.3.0 | 200 |
| 瓜子漫画 | `guazi_manhua.js` | `guazimanhua` | 1.0.4 | 200 |
| 嬉皮漫畫 | `hipmh.js` | `hipmh` | 1.0.1 | 200 |
| 来漫画（分流） | `laimanhua_split_hosts.js` | `laimanhua_split` | 1.2.1 | 200 |
| 51漫画 | `manga51.js` | `manga51` | 1.2.0 | 200 |
| 香蕉漫画 | `manhuauo_banana.js` | `manhuauo_banana_v2` | 1.0.3 | 403（Cloudflare） |
| 漫网 | `manwang.js` | `manwang` | 1.2.0 | 200 |
| 4399漫画网 | `mh4399.js` | `mh4399` | 1.0.3 | 200 |
| MOJOIN | `mojoin.js` | `mojoin_v2` | 1.0.7 | 200 |
| NoyManga | `noymanga.js` | `noymanga` | 1.1.3 | 200 |
| Rawkuma | `rawkuma.js` | `rawkuma` | 1.1.0 | 200 |
| 如漫画 | `rumanhua.js` | `rumanhua_fixed_v15` | 1.2.7 | 200 |
| SF漫画 | `sfacg_manhua.js` | `sfacg_manhua` | 1.0.0 | 200 |
| 腾讯动漫（正版） | `tencent_comic_official.js` | `qq_comic_official_v1` | 1.0.3 | 200 |
| 图库漫画 | `tuku_cc.js` | `tuku_cc` | 1.0.1 | 200 |
| LINE WEBTOON | `webtoons_zh_hant.js` | `webtoons_zh_hant` | 1.0.0 | 200 |
| W漫画 | `wmanhua.js` | `wmanhua` | 1.0.1 | 200 |
| zero搬运网 | `zerobyw33.js` | `zerobyw33` | 1.2.0 | 200 |

### B 组：比官方更新的私有修复版（5 个）

| 源 | 文件 | key | 本仓库 | 官方 | 说明 |
|---|---|---|---|---|---|
| 拷贝漫画 | `copy_manga.js` | `copy_manga` | **1.6.6** | 1.4.1 | 官方会降级，务必用本仓库 |
| 爱看漫 | `ikmmh_v2.js` | `ikmmh_v2` | **3.0.0** | 1.0.6 | 独立 key，与官方 `ikmmh` 并存 |
| Komiic | `komiic.js` | `Komiic` | **1.0.8** | 1.0.3 | 双域名自动择优 |
| 漫蛙吧 | `manwaba.js` | `manwaba` | **1.1.3** | 1.0.2 | 站点已换域名 |
| 优酷漫画 | `ykmh.js` | `ykmh` | **1.0.6** | 1.0.0 | 站点已换域名 |

### C 组：采用官方较新版本（2 个）

| 源 | 文件 | key | 本仓库 | 你备份中的旧版 |
|---|---|---|---|---|
| MangaDex | `manga_dex.js` | `manga_dex` | 1.2.0 | 1.1.1 |
| 紳士漫畫 | `wnacg.js` | `wnacg` | 1.0.6 | 1.0.5 |

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

本仓库的 `version` 与你 `.venera` 备份中的**完全一致**，这是刻意的：

- App 的更新判定是 `compareSemVer(清单版本, 已安装版本)`，仅在**严格大于**时才提示更新。
- 若为了「强制迁移」而抬高版本，App 会走机制 2：先删源，再用**已安装源里的旧 `url`** 下载。
- 对于原本 `url` 填错的源，这一步必然失败，**源会被删除**。

因此正确做法是：保持版本不变，通过「删除 + 重新添加」完成迁移；之后源文件内的 `url` 已指向本仓库，未来的版本提升才能安全生效。

---

## 七、已知限制

### 带设置项的源（13 个，全部有默认值，安装即可用）

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

### 数据文件（`.data`）

部分源会把登录态或缓存写入 `comic_source/<key>.data`（如 `copy_manga`、`komiic`、`noymanga`、`rawkuma`、`zerobyw33`）。
这些文件是**用户本地数据，不需要、也不应该放进本仓库**——App 会在首次使用时自动创建。
发布仓库只包含 `.js` 文件。

### 站点侧限制（源无法解决）

- **Cloudflare 403**：`ikmmh_v2`、`manhuauo_banana`、`ykmh`、`baozimh` 等。多为网络出口/地区问题，与源无关；`ykmh` 在中国大陆通常需要代理。
- **正版权限**：`tencent_comic_official` 只返回站点标记为可读的章节，付费章节请使用官方客户端。这是刻意设计的边界，不会绕过。
- **搜索接口失效**：`manwang` 官方搜索接口长期不稳定（返回 0 结果或「搜索繁忙」），源已内置站内目录兜底；但无法凭空恢复服务器没有提供的索引。

### 与官方仓库同名 key 的源

`copy_manga`、`Komiic`、`manwaba`、`ykmh`、`manga_dex`、`wnacg` 这 6 个 key 与官方仓库重合。
**不要同时订阅官方仓库和本仓库**，否则更新来源会互相打架。建议只保留本仓库。

---

## 八、维护流程

### 修改某个源之后

```bash
# 1. 提升该源的 version（必须，否则 App 不会提示更新）
# 2. 重新生成 index.json（脚本会从源文件读取 name/key/version，避免手写不一致）
python3 tools/gen_index.py

# 3. 跑兼容性校验
node tools/validate.js

# 4. 提交
git add -A && git commit -m "fix: <源名> <改动说明>" && git push
```

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

### 新增源

把 `.js` 放进仓库根目录 → `python3 tools/gen_index.py` → 如需在
`tools/gen_index.py` 的 `DESCRIPTION` 表里补充说明 → `node tools/validate.js` → 提交。

---

## 九、本期改动记录

| 改动 | 依据 | 影响范围 |
|---|---|---|
| 建立 30 源统一仓库 | 用户 `.venera` 备份 + 官方 venera-configs | 全部 |
| `manga_dex` 用官方 1.2.0 | 官方版本高于备份中的 1.1.1 | 1 个源 |
| `wnacg` 用官方 1.0.6 | 官方版本高于备份中的 1.0.5 | 1 个源 |
| 修正 `dm5` / `gfmh` / `ikmmh_v2` / `rawkuma` 的 `url` | 原值指向漫画网站首页，触发更新会先删源后失败 | 4 个源 |
| `index.json` 由源文件自动生成 | 避免清单与源文件版本不一致 | 全部 |

---

## 十、参考

- Venera 官方源开发文档：<https://github.com/venera-app/venera/blob/master/doc/comic_source.md>
- Venera JavaScript API：<https://github.com/venera-app/venera/blob/master/doc/js_api.md>
- 官方源仓库：<https://github.com/venera-app/venera-configs>
- 开发日志：《Venera 漫画源开发日志（统一合并版 v3）》
