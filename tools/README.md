# tools 说明

| 脚本 | 作用 | 命令 |
|---|---|---|
| `validate.js` | Venera 兼容性校验（L1 语法 → L5 设置），用最小运行时仿真复现 App 的加载流程 | `node tools/validate.js` |
| `gen_index.py` | 从源文件重新生成 `index.json`，`name`/`key`/`version` 一律读取源文件，避免手写不一致 | `python3 tools/gen_index.py` |
| `set_url.py` | 把所有源的顶层 `url` 指向本仓库；`--show` 查看现状，`--restore` 回滚 | `python3 tools/set_url.py <仓库地址>` |

## 推荐工作流

```bash
# 修改某个源后：
#   1) 先提升该源的 version（否则 App 不会提示更新，见 README 第六节）
python3 tools/gen_index.py      # 2) 重新生成清单
node tools/validate.js          # 3) 必须全绿才能提交
git add -A && git commit -m "fix: <源名> <改动说明>" && git push
```

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
