#!/usr/bin/env node
/**
 * Venera 源仓库本地校验器
 *
 * 作用：在没有 App 的情况下，用最小仿真环境复现 Venera 的源加载流程，
 *       对仓库内每个 .js 源执行「语法 -> 类识别 -> 实例化 -> 元数据 -> 接口字段」五级检查。
 *
 * 用法：
 *   node tools/validate.js            # 校验当前目录（仓库根）
 *   node tools/validate.js <目录>
 *
 * 退出码：全部通过 0；有失败 1。
 */

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const REPO = path.resolve(process.argv[2] || path.join(__dirname, '..'));

/* ------------------------------------------------------------------ *
 * 1. 最小 Venera 运行时仿真
 * ------------------------------------------------------------------ */

function makeSandbox() {
  class ComicSource {
    name = '';
    key = '';
    version = '';
    minAppVersion = '';
    url = '';
    // 仿真：未持久化过的数据返回 null，与 App 首次安装行为一致
    loadData(k) { return this.__data && k in this.__data ? this.__data[k] : null; }
    saveData(k, v) { (this.__data = this.__data || {})[k] = v; }
    deleteData(k) { if (this.__data) delete this.__data[k]; }
    loadSetting(k) {
      const s = this.settings && this.settings[k];
      if (!s) return null;
      if (this.__settings && k in this.__settings) return this.__settings[k];
      return s.default;
    }
    init() {}
    get isLogged() { return false; }
    static sources = {};
  }

  class Comic {
    constructor(o = {}) { Object.assign(this, o); }
  }
  class ComicDetails {
    constructor(o = {}) { Object.assign(this, o); }
  }
  class Comment {
    constructor(o = {}) { Object.assign(this, o); }
  }
  class Cookie {
    constructor(o = {}) { Object.assign(this, o); }
  }
  class ImageLoadingConfig {
    constructor(o = {}) { Object.assign(this, o); }
  }

  const notImplemented = (what) => (...args) => {
    throw new Error(`NETWORK_BLOCKED: ${what} 在离线校验中被拦截 (${JSON.stringify(args[0] ?? args[1] ?? '')})`);
  };

  const Network = {
    get: notImplemented('Network.get'),
    post: notImplemented('Network.post'),
    put: notImplemented('Network.put'),
    delete: notImplemented('Network.delete'),
    patch: notImplemented('Network.patch'),
    sendRequest: notImplemented('Network.sendRequest'),
    fetchBytes: notImplemented('Network.fetchBytes'),
    setCookies() {}, getCookies() { return []; }, deleteCookies() {},
  };

  const Convert = new Proxy({}, {
    get: () => (v) => v,   // 离线只做形状校验，不真正加解密
  });

  class HtmlElement {
    text = ''; attributes = {}; children = []; nodes = []; innerHtml = '';
    classNames = []; id = null; localName = 'div'; parent = null;
    previousSibling = null; nextSibling = null;
    querySelector() { return null; }
    querySelectorAll() { return []; }
    getElementById() { return null; }
  }
  class HtmlDocument extends HtmlElement {
    constructor(html = '') { super(); this.__html = html; }
    dispose() {}
  }

  const UI = {
    showMessage() {}, showDialog() {}, launchUrl() {},
    showLoading() { return 0; }, cancelLoading() {},
    showInputDialog() { return null; }, showSelectDialog() { return null; },
  };

  const sandbox = {
    ComicSource, Comic, ComicDetails, Comment, Cookie, ImageLoadingConfig,
    Network, Convert, HtmlDocument, HtmlElement, UI,
    sendMessage: () => null,
    createUuid: () => '00000000-0000-4000-8000-000000000000',
    randomInt: (a, b) => Math.floor((a + b) / 2),
    randomDouble: (a, b) => (a + b) / 2,
    fetch: () => Promise.reject(new Error('NETWORK_BLOCKED')),
    console: { log() {}, error() {}, warn() {}, info() {}, debug() {} },
    setTimeout, clearTimeout, setInterval, clearInterval,
    TextEncoder, TextDecoder, URL, URLSearchParams, Promise, JSON, Math, Date,
    Buffer, atob: (s) => Buffer.from(s, 'base64').toString('binary'),
    btoa: (s) => Buffer.from(s, 'binary').toString('base64'),
  };
  sandbox.globalThis = sandbox;
  sandbox.self = sandbox;
  sandbox.window = sandbox;
  return vm.createContext(sandbox);
}

/* ------------------------------------------------------------------ *
 * 2. 单个源的五级检查
 * ------------------------------------------------------------------ */

const REQUIRED_META = ['name', 'key', 'version'];

// App 源码 lib/foundation/comic_source/parser.dart 中 switch(type) 接受的取值
const EXPLORE_TYPES = new Set([
  'singlePageWithMultiPart',
  'multiPartPage',        // 别名，映射到 singlePageWithMultiPart
  'multiPageComicList',
  'mixed',
]);

function checkSource(file, code) {
  const problems = [];
  const info = { file, name: '', key: '', version: '', minAppVersion: '', caps: [], settings: 0 };

  // ---- L1 语法 ----
  try {
    new vm.Script(code, { filename: file });
  } catch (e) {
    return { ok: false, info, problems: [`L1 语法错误: ${e.message}`] };
  }

  // ---- L2 类识别 + 实例化 ----
  // 类声明在 vm 上下文中是全局词法绑定，不会成为 globalThis 的自有属性，
  // 因此必须先从源码解析出类名，再显式求值取回构造函数。
  const classNames = [...code.matchAll(/^\s*class\s+([A-Za-z_$][\w$]*)\s+extends\s+([A-Za-z_$][\w$.]*)/gm)]
    .map((m) => ({ name: m[1], base: m[2] }));

  if (!classNames.length) {
    return { ok: false, info, problems: ['L2 源码中未声明任何 class ... extends ...'] };
  }
  const csClasses = classNames.filter((c) => c.base.split('.').pop() === 'ComicSource');
  if (!csClasses.length) {
    return { ok: false, info, problems: [`L2 未找到 extends ComicSource 的类（发现: ${classNames.map((c) => c.name + ' extends ' + c.base).join(', ')}）`] };
  }
  if (csClasses.length > 1) {
    problems.push(`L2 文件内声明了多个 ComicSource 子类: ${csClasses.map((c) => c.name).join(', ')}（App 只识别一个）`);
  }

  const ctx = makeSandbox();
  let Ctor = null;
  try {
    vm.runInContext(code, ctx, { filename: file });
    Ctor = vm.runInContext(csClasses[0].name, ctx);
  } catch (e) {
    return { ok: false, info, problems: [`L2 顶层执行失败: ${e.message}`] };
  }
  if (typeof Ctor !== 'function') {
    return { ok: false, info, problems: [`L2 类 ${csClasses[0].name} 求值失败`] };
  }
  if (!(Ctor.prototype instanceof ctx.ComicSource)) {
    return { ok: false, info, problems: [`L2 类 ${csClasses[0].name} 的原型链未继承 ComicSource`] };
  }
  info.class = csClasses[0].name;

  let inst;
  try {
    inst = new Ctor();
  } catch (e) {
    return { ok: false, info, problems: [`L2 实例化失败: ${e.message}`] };
  }

  // ---- L3 元数据 ----
  for (const f of REQUIRED_META) {
    const v = inst[f];
    if (typeof v !== 'string' || v.trim() === '') problems.push(`L3 元数据 ${f} 为空或非字符串`);
    else info[f] = v;
  }
  info.minAppVersion = inst.minAppVersion || '';
  info.url = typeof inst.url === 'string' ? inst.url : '';
  if (inst.url !== undefined && typeof inst.url !== 'string') problems.push('L3 url 字段非字符串');
  if (info.key && !/^[\w\u4e00-\u9fa5$@.\-]+$/.test(info.key)) {
    problems.push(`L3 key 含可疑字符: ${info.key}`);
  }
  // key 不应看起来像密钥/密文
  if (info.key && info.key.length > 32) problems.push(`L3 key 过长(${info.key.length})，疑似误把密钥写成 key`);

  // ---- L4 能力声明 ----
  const needArray = ['explore'];
  if (Array.isArray(inst.explore) && inst.explore.length) info.caps.push(`explore x${inst.explore.length}`);
  else if (inst.explore !== undefined && !Array.isArray(inst.explore)) problems.push('L4 explore 不是数组');

  if (inst.category && typeof inst.category === 'object') {
    info.caps.push('category');
    if (!inst.category.title) problems.push('L4 category.title 为空');
    if (!Array.isArray(inst.category.parts)) problems.push('L4 category.parts 不是数组');
  }
  if (inst.search && typeof inst.search.load === 'function') info.caps.push('search');
  else if (inst.search && typeof inst.search.loadNext !== 'function') problems.push('L4 search 既无 load 也无 loadNext');

  if (inst.comic && typeof inst.comic === 'object') {
    info.caps.push('comic');
    if (typeof inst.comic.loadInfo !== 'function') problems.push('L4 comic.loadInfo 缺失');
    if (typeof inst.comic.loadEp !== 'function') problems.push('L4 comic.loadEp 缺失');
  } else {
    problems.push('L4 comic 对象缺失');
  }

  if (inst.settings) {
    info.settings = Object.keys(inst.settings).length;
    info.caps.push(`settings x${info.settings}`);
  }
  // 校验 explore 每项结构
  if (Array.isArray(inst.explore)) {
    inst.explore.forEach((e, i) => {
      if (!e || typeof e !== 'object') return problems.push(`L4 explore[${i}] 非法`);
      if (!e.title) problems.push(`L4 explore[${i}].title 为空`);
      if (typeof e.load !== 'function' && typeof e.loadNext !== 'function') {
        problems.push(`L4 explore[${i}] 既无 load 也无 loadNext`);
      }
      // 合法值以 App 源码 lib/foundation/comic_source/parser.dart:_loadExploreData 为准：
      //   singlePageWithMultiPart | multiPartPage(别名) | multiPageComicList | mixed
      // 其余值 App 会抛 ComicSourceParseException("Unknown explore page type")
      if (!EXPLORE_TYPES.has(e.type)) {
        problems.push(`L4 explore[${i}].type 非法: ${e.type}`);
      }
    });
  }

  // ---- L4b 顶层 url 必须是 js 更新地址，不能是漫画网站首页 ----
  // 依据 App 的 ComicSourcePage.update：url 仅用于「检查更新」下载。
  // 若指向 HTML 首页，更新时会先 remove() 源再下载，解析失败 => 源被删除。
  if (info.url) {
    if (!/^https?:\/\//.test(info.url)) {
      problems.push(`L4b url 不是合法 http(s) 地址: ${info.url}`);
    } else if (/\.(js|mjs)(\?|$)/i.test(info.url) === false && !/jsdelivr|raw\.githubusercontent|githubusercontent/.test(info.url)) {
      problems.push(`L4b url 疑似指向网页而非 .js 更新地址: ${info.url}`);
    }
  }

  // ---- L5 空值安全：settings 键都有 default ----
  if (inst.settings) {
    for (const [k, s] of Object.entries(inst.settings)) {
      if (!s || typeof s !== 'object') { problems.push(`L5 settings.${k} 非法`); continue; }
      if (!s.title) problems.push(`L5 settings.${k}.title 缺失`);
      if (!['input', 'select', 'switch', 'callback'].includes(s.type)) {
        problems.push(`L5 settings.${k}.type 非法: ${s.type}`);
      }
      if (['input', 'select', 'switch'].includes(s.type) && s.default === undefined) {
        problems.push(`L5 settings.${k} 无 default（首次安装可能异常）`);
      }
      if (s.type === 'select' && !Array.isArray(s.options)) {
        problems.push(`L5 settings.${k} select 无 options`);
      }
    }
  }

  return { ok: problems.length === 0, info, problems };
}

/* ------------------------------------------------------------------ *
 * 3. 仓库级检查
 * ------------------------------------------------------------------ */

function main() {
  const indexPath = path.join(REPO, 'index.json');
  if (!fs.existsSync(indexPath)) {
    console.error(`✗ 找不到 index.json: ${indexPath}`);
    process.exit(1);
  }

  const lines = [];
  const say = (s = '') => { lines.push(s); console.log(s); };

  say(`仓库目录: ${REPO}`);
  say('');

  // --- index.json 结构 ---
  let index;
  try {
    index = JSON.parse(fs.readFileSync(indexPath, 'utf8'));
  } catch (e) {
    console.error(`✗ index.json 解析失败: ${e.message}`);
    process.exit(1);
  }
  say('══ index.json 检查 ══');
  const idxProblems = [];
  if (!Array.isArray(index)) idxProblems.push('index.json 顶层不是数组');
  const seenFiles = new Set(), seenKeys = new Map();
  index.forEach((e, i) => {
    ['name', 'fileName', 'key', 'version'].forEach((f) => {
      if (typeof e[f] !== 'string' || !e[f].trim()) idxProblems.push(`[${i}] 字段 ${f} 缺失或为空`);
    });
    if (e.url && e.fileName) idxProblems.push(`[${i}] url 与 fileName 同时存在（只应提供一个）`);
    if (e.fileName && seenFiles.has(e.fileName)) idxProblems.push(`[${i}] fileName 重复: ${e.fileName}`);
    if (e.fileName) seenFiles.add(e.fileName);
    if (e.key) {
      if (seenKeys.has(e.key)) idxProblems.push(`[${i}] key 重复: ${e.key}（与 ${seenKeys.get(e.key)} 冲突）`);
      else seenKeys.set(e.key, e.fileName || e.url);
    }
    if (!e.fileName && !e.url) idxProblems.push(`[${i}] 缺少 url 和 fileName`);
    if (e.fileName && !fs.existsSync(path.join(REPO, e.fileName))) {
      idxProblems.push(`[${i}] 文件不存在: ${e.fileName}`);
    }
  });
  idxProblems.forEach((p) => say(`  ✗ ${p}`));
  if (!idxProblems.length) say(`  ✓ ${index.length} 条记录，结构合规，key/fileName 均唯一，文件全部存在`);
  say('');

  // --- 逐个源 ---
  say('══ 源文件检查（L1 语法 / L2 类识别+实例化 / L3 元数据 / L4 接口 / L5 设置）══');
  const results = [];
  const diskJs = fs.readdirSync(REPO).filter((f) => f.endsWith('.js'));
  const idxJs = new Set(index.map((e) => e.fileName).filter(Boolean));

  for (const e of index) {
    if (!e.fileName) continue;
    const p = path.join(REPO, e.fileName);
    if (!fs.existsSync(p)) continue;
    const r = checkSource(e.fileName, fs.readFileSync(p, 'utf8'));
    results.push(r);

    // 交叉校验：index 声明的 name/version 必须与源文件内一致
    const mism = [];
    if (r.info.name && r.info.name !== e.name) mism.push(`name index="${e.name}" 源内="${r.info.name}"`);
    if (r.info.version && r.info.version !== e.version) mism.push(`version index="${e.version}" 源内="${r.info.version}"`);
    if (r.info.key && r.info.key !== e.key) mism.push(`key index="${e.key}" 源内="${r.info.key}"`);

    const tag = r.ok && !mism.length ? '✓' : '✗';
    say(`${tag} ${e.fileName}`);
    say(`    name=${r.info.name || '?'}  key=${r.info.key || '?'}  v${r.info.version || '?'}  minApp=${r.info.minAppVersion || '-'}  [${r.info.caps.join(', ')}]`);
    r.problems.forEach((p2) => say(`    ✗ ${p2}`));
    mism.forEach((m) => say(`    ✗ index 不一致: ${m}`));
  }

  // --- 仓库外游离文件 ---
  const orphan = diskJs.filter((f) => !idxJs.has(f) && !f.startsWith('_'));
  say('');
  say('══ 游离文件检查 ══');
  if (orphan.length) orphan.forEach((f) => say(`  ! ${f} 存在于目录但未列入 index.json`));
  else say('  ✓ 无游离 .js 文件');

  // --- 汇总 ---
  const failed = results.filter((r) => !r.ok).length;
  say('');
  say('══ 汇总 ══');
  say(`  源总数: ${index.length}`);
  say(`  通过:   ${results.filter((r) => r.ok).length}`);
  say(`  失败:   ${failed}`);
  say(`  索引问题: ${idxProblems.length}`);
  const bad = failed || idxProblems.length || orphan.length;
  say(bad ? '\n结果: FAIL' : '\n结果: PASS — 全部源通过 Venera 兼容性校验');

  fs.writeFileSync(path.join(REPO, 'tools', 'validation-report.txt'), lines.join('\n') + '\n');
  process.exit(bad ? 1 : 0);
}

main();
