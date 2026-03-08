# 微信公众号浏览器自动化经验总结

> 基于实际项目积累，记录在 Chrome/Playwright 自动化微信公众号后台的踩坑与解法。
> 适用场景：用 Playwright CDP 连接已登录的 Chrome，自动完成图文发布全流程。

---

## 目录

1. [环境搭建](#1-环境搭建)
2. [图片上传](#2-图片上传)
3. [Vue v-model 铁律](#3-vue-v-model-铁律)
4. [ProseMirror 编辑器](#4-prosemirror-编辑器)
5. [原创声明自动化](#5-原创声明自动化)
6. [投票自动化](#6-投票自动化)
7. [封面图自动化](#7-封面图自动化)
8. [赞赏功能自动化](#8-赞赏功能自动化)
9. [mdnice 自动化](#9-mdnice-自动化)
10. [调试原则](#10-调试原则)
11. [代理与网络问题](#11-代理与网络问题)

---

## 1. 环境搭建

### Chrome CDP 模式启动

微信公众号后台要求登录态，必须用已有 profile 的 Chrome，不能用 headless 新实例。
用 `--remote-debugging-port=9222` 启动 Chrome，再用 Playwright `connect_over_cdp` 接管。

```bash
# 启动 Chrome（保持登录 cookie）
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/.chrome-cdp-profile" \
  --ignore-certificate-errors &
```

**注意**：
- `--user-data-dir` 必须指定非默认路径，Chrome 145+ 要求这样才允许 CDP
- 第一次启动需手动扫码登录微信后台，之后 cookie 自动保持
- `--ignore-certificate-errors` 仅用于开发/调试，生产环境请谨慎

### Playwright 连接

```python
from playwright.async_api import async_playwright

async with async_playwright() as p:
    browser = await p.chromium.connect_over_cdp("http://localhost:9222")
    context = browser.contexts[0]
    # 找到编辑器页面
    page = next(
        pg for pg in context.pages
        if "appmsg_edit" in pg.url
    )
```

---

## 2. 图片上传

### 方案：base64 编码直接上传（推荐）

微信编辑器页面是 HTTPS，直接 `fetch("http://localhost:xxx")` 会触发 Mixed Content 拒绝。
**最终方案**：Python 读文件 → base64 → 内嵌进 JS → 在页面内构造 Blob → 上传微信 CDN。

```python
import base64
from pathlib import Path

async def upload_image_file(page, token: str, file_path: Path) -> str:
    """上传本地图片到微信 CDN，返回 cdn_url"""
    data = file_path.read_bytes()
    b64 = base64.b64encode(data).decode()
    mime = "image/png" if file_path.suffix == ".png" else "image/jpeg"

    js = """
    async ([b64, mime, imageName, token]) => {
        var bstr = atob(b64), n = bstr.length, u8 = new Uint8Array(n);
        while (n--) u8[n] = bstr.charCodeAt(n);
        var blob = new Blob([u8], {type: mime});
        var fd = new FormData();
        fd.append("file", blob, imageName);
        var url = "/cgi-bin/filetransfer?action=upload_material&f=json&scene=8"
                  + "&writetype=doublewrite&groupid=1&token=" + token + "&type=10";
        var r = await fetch(url, {method: "POST", body: fd});
        var d = await r.json();
        if (d.cdn_url) return JSON.stringify({ok: true, cdn_url: d.cdn_url});
        return JSON.stringify({ok: false, error: JSON.stringify(d)});
    }
    """
    result_str = await page.evaluate(js, [b64, mime, file_path.name, token])
    result = json.loads(result_str)
    if not result["ok"]:
        raise RuntimeError(f"Upload failed: {result['error']}")
    return result["cdn_url"]
```

**为什么不用 HTTPS 本地服务器**：新 Chrome profile 不自动信任自签证书（旧 profile 可能已手动信任过），
导致 `Failed to fetch`。Base64 方案彻底绕开证书信任问题。

### 获取 token

微信编辑器 URL 中包含 token 参数：

```python
from urllib.parse import urlparse, parse_qs

parsed = urlparse(page.url)
token = parse_qs(parsed.query).get("token", [""])[0]
```

### 把 cdn_url 插入编辑器

上传成功后，找到文章中对应的 `<figure>` 占位元素，用 JS 创建 `<img>` 插入：

```javascript
// 找到第 N 个 figure，插入图片
var figures = document.querySelectorAll('#ueditor_0 figure');
var fig = figures[n];
var img = document.createElement('img');
img.src = cdn_url;
fig.appendChild(img);
// 通知 ProseMirror 内容变化
document.querySelector('[contenteditable=true]')
    .dispatchEvent(new Event('input', {bubbles: true}));
```

---

## 3. Vue v-model 铁律

**微信公众号编辑器的所有输入框都用 Vue v-model，以下方式全部无效：**

| 方式 | 结果 |
|------|------|
| `el.value = xxx` + `dispatchEvent('input')` | ❌ Vue 不响应 |
| Playwright `fill()` | ❌ 无效 |
| Playwright `keyboard.type()` | ❌ 无效 |
| Playwright `press_sequentially()` | ❌ 无效 |
| `Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(el, val)` | ❌ 无效 |

**唯一有效方式：CDP `Input.dispatchKeyEvent`（逐字符）**

```python
async def cdp_type(context, page, selector: str, text: str):
    """用 CDP 逐字输入，绕过 Vue v-model 拦截"""
    await page.click(selector)  # 先 focus
    cdp = await context.new_cdp_session(page)
    for char in text:
        await cdp.send('Input.dispatchKeyEvent', {
            'type': 'keyDown', 'key': char
        })
        await cdp.send('Input.dispatchKeyEvent', {
            'type': 'char', 'text': char  # text 只在 char 事件里发
        })
        await cdp.send('Input.dispatchKeyEvent', {
            'type': 'keyUp', 'key': char
        })
    await cdp.detach()
```

**注意**：`keyDown` 事件不要发 `text` 字段，只在 `char` 事件里发。否则每个字符会输入两次。

**受影响的输入框**：
- 标题：`#title`
- 简介：`#js_description`
- 原创作者：`input[placeholder*="作者"]`
- 投票问题/选项：`.vote_dialog__body input.weui-desktop-form__input`

---

## 4. ProseMirror 编辑器

### 定位编辑器

```javascript
// 微信编辑器是第二个 contenteditable（第一个是标题）
document.querySelectorAll('[contenteditable=true]')[1]
```

### textNode 修改不持久

**陷阱**：直接改 `node.textContent` 不触发 ProseMirror 变更检测，Cmd+S 保存的是旧内容。

**修复**：DOM 修改后必须手动触发 input 事件：

```javascript
var editor = document.querySelectorAll('[contenteditable=true]')[1];
// ... DOM 修改 ...
editor.dispatchEvent(new Event('input', {bubbles: true}));
```

### 加粗语法陷阱

mdnice 渲染时，`**"..."**`（加粗紧邻中文引号）在 ProseMirror 中会渲染失败，显示原始 `**`。
**修复**：在 ProseMirror 中用 DOM API 拆分 span 并包裹 `<strong style="...">`，必须带完整 inline style，否则会被编辑器吞掉。

---

## 5. 原创声明自动化

微信原创声明流程比较复杂，有两个独立的赞赏开关，容易踩坑。

### 完整流程

```
1. 点击开启原创开关（enable_original_only.js）
2. 对话框内关闭赞赏开关（默认 ON，不关会触发"请选择赞赏账户"验证失败）
3. 填写作者（Vue v-model，只能 CDP 输入）
4. 勾选协议 checkbox（点 <i> icon，不是 input 或 label）
5. 点确定
```

### 关键 DOM 结构

```
.weui-desktop-dialog
  ├── #js_original_edit_box        ← 对话框 BODY（作者、赞赏开关）
  └── .weui-desktop-dialog__ft     ← 对话框 FOOTER（checkbox、确定/取消）
```

**易错点**：把所有选择器都限定在 `#js_original_edit_box` 内，导致找不到 footer 里的 checkbox 和按钮。
**正确做法**：footer 里的元素用 `:has(#js_original_edit_box)` 定位整个 dialog：

```python
# 勾选协议
await page.click(
    '.weui-desktop-dialog:has(#js_original_edit_box) '
    '.original_agreement .weui-desktop-icon-checkbox'
)

# 点确定
await page.click(
    '.weui-desktop-dialog:has(#js_original_edit_box) '
    '.weui-desktop-btn_primary'
)
```

### Checkbox 点击方式

```python
# ❌ 不对：input[type="checkbox"] 或 label
# ✅ 正确：点 <i> icon 元素
await page.click('.weui-desktop-icon-checkbox')

# ❌ 不要 force=True（会绕过可见性检查，反而不触发 UI 状态变更）
```

---

## 6. 投票自动化

### 投票按钮定位

**坑**：投票按钮 `#js_editor_insertvote` 是 `<li>` 元素，在页面顶部导航栏，**不在** UEditor toolbar（`.edui-toolbar`）里。

```python
# ✅ 正确：顶部导航栏的 LI 元素
await page.click('#js_editor_insertvote')

# ❌ 错误：在 UEditor toolbar 里找
await page.click('.edui-toolbar #js_editor_insertvote')
```

### 对话框结构

```
.vote_dialog__body
  └── input.weui-desktop-form__input (index 0 = 问题, 1+ = 选项)
a.ic_option_add                       ← 添加选项按钮（圆形 + 按钮）
button:has-text("发起")               ← 确认按钮（不是"确定"）
```

### evaluate() 传参陷阱

```python
# ❌ 错误：多参数会报 TypeError
await page.evaluate(js, DIALOG_SEL, inp_idx)

# ✅ 正确：用数组传，JS 里解构
await page.evaluate(
    "([sel, idx]) => { var el = document.querySelector(sel)... }",
    [DIALOG_SEL, inp_idx]
)
```

### 完整投票创建流程

```python
async def add_poll(page, context, question: str, options: list[str]):
    # 1. 物理点击投票按钮
    await page.click('#js_editor_insertvote')
    await page.wait_for_selector('.vote_dialog__body', timeout=5000)

    # 2. 填写问题（CDP 输入）
    await cdp_type(context, page,
        '.vote_dialog__body input.weui-desktop-form__input:nth-of-type(1)',
        question)

    # 3. 默认有 3 个选项框，多出的要先点 + 添加
    for i, opt in enumerate(options):
        if i >= 3:
            await page.click('a.ic_option_add')
            await page.wait_for_timeout(500)
        sel = f'.vote_dialog__body input.weui-desktop-form__input'
        await page.evaluate(
            "([sel, idx]) => { document.querySelectorAll(sel)[idx].focus() }",
            [sel, i + 1]  # index 0 是问题，1+ 是选项
        )
        await cdp_type(context, page, sel, opt)  # 需要先 focus

    # 4. 点发起
    await page.click('button:has-text("发起")')
```

---

## 7. 封面图自动化

### 点击封面区域

```python
# JS click() 不够，用 Playwright click + force=True
await page.click('.js_cover_btn_area', force=True)
await page.wait_for_timeout(500)
```

这会弹出下拉菜单（从正文选择 / 从图片库选择 / 微信扫码上传 / AI配图）。

### 完整封面设置流程

```python
# 1. 打开封面下拉
await page.click('.js_cover_btn_area', force=True)

# 2. 点"从图片库选择"
await page.click('.pop-opr__button.js_imagedialog', force=True)
await page.wait_for_selector('.weui-desktop-img-picker__item', timeout=10000)

# 3. 找到对应文件名的图片并选中
items = await page.query_selector_all('.weui-desktop-img-picker__item')
for item in items:
    title = await item.get_attribute('title') or ''
    if cover_filename in title:
        await item.click()
        break

# 4. 点下一步
await page.click('button:has-text("下一步")')

# 5. 等待裁切界面加载（有 loading spinner，需要等）
await page.wait_for_timeout(3000)

# 6. 点确认
await page.click('button:has-text("确认")')
```

---

## 8. 赞赏功能自动化

注意：赞赏有两个独立开关：
1. **页面级开关**（`input.js_reward_set`）— 控制文章末尾赞赏按钮
2. **原创声明对话框内的开关**（`#js_original_edit_box .js_reward_switch`）— 仅在原创声明流程中出现

两者完全独立，不要混淆。

```python
async def enable_reward(page, context):
    # 1. 点击赞赏开关（页面级）
    await page.click('.js_reward_open')
    await page.wait_for_timeout(500)

    # 2. 如果弹出选择账户对话框，选第一个账户
    account_sel = '.weui-desktop-dialog .js_reward_account_item'
    if await page.query_selector(account_sel):
        await page.click(account_sel)

    # 3. 点确定
    confirm = '.weui-desktop-dialog .weui-desktop-btn_primary'
    if await page.query_selector(confirm):
        await page.click(confirm)
```

---

## 9. mdnice 自动化

mdnice.com 用 CodeMirror 编辑器 + React，有一些独特的坑。

### 必须用键盘粘贴，不能 setValue

```python
# ❌ 不触发预览渲染
await page.evaluate("editor => editor.setValue(text)", [editor, text])

# ✅ 正确：模拟 Cmd+V
await page.keyboard.press('Meta+a')  # 全选
await page.keyboard.press('Meta+v')  # 粘贴（需提前把内容写入剪贴板）
```

### 必须先创建文章

直接粘贴内容会触发"新增文章"对话框，需要先完成创建流程，否则"复制到微信"会报错。

```python
# 1. 隐藏所有干扰弹窗
await page.evaluate("""
    ['ant-modal-root', 'ant-modal-mask', 'ant-modal-wrap', 'global-mask']
    .forEach(cls => {
        document.querySelectorAll('.' + cls)
            .forEach(el => el.style.display = 'none')
    })
""")

# 2. 粘贴内容（触发"新增文章"对话框）
await page.keyboard.press('Meta+v')

# 3. 恢复弹窗显示
await page.evaluate("""
    ['ant-modal-root', 'ant-modal-mask', 'ant-modal-wrap']
    .forEach(cls => {
        document.querySelectorAll('.' + cls)
            .forEach(el => el.style.display = '')
    })
""")

# 4. 选文件夹 → 点新增
await page.click('.ant-modal .ant-select-selector')
await page.click('.ant-select-item-option')
await page.click('.ant-modal .ant-btn-primary')

# 5. 创建后编辑器被清空，重新粘贴真正内容
await page.keyboard.press('Meta+a')
await page.keyboard.press('Meta+v')
```

### 主题选择

```python
# 1. 打开主题面板
await page.click('a.nice-menu-link:has-text("主题")')

# 2. 在主题列表里找"橙心"
await page.evaluate("""
    var items = document.querySelectorAll('.theme-list > *');
    for (var item of items) {
        if (item.textContent.includes('橙心')) {
            item.querySelector('button').click();
            break;
        }
    }
""")

# 3. 关闭主题面板
await page.keyboard.press('Escape')
```

### 复制到微信

```python
await page.click('a.nice-btn-wechat')
# 成功提示："已复制，请到微信公平台粘贴"
```

### 持久化登录

```python
# 使用 launch_persistent_context 保持 cookie，扫码一次永久有效
context = await p.chromium.launch_persistent_context(
    user_data_dir=Path.home() / '.mdnice-profile',
    headless=False,
)
# 每次启动前清理锁文件
lock = Path.home() / '.mdnice-profile' / 'SingletonLock'
if lock.exists():
    lock.unlink()
```

---

## 10. 调试原则

### 不要每次 launch → 操作 → close

```python
# ❌ 每次改代码都重新走全部流程，效率极低
async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(...)
        # ... 全部步骤 ...
        await browser.close()  # 每次都关

# ✅ 调试时注释掉 close，保持浏览器打开
# 只在正式运行时才关浏览器
```

### 每步截图验证

```python
await page.screenshot(path="/tmp/step_01_after_paste.png")
# 用 subprocess.run(["open", "/tmp/step_01_after_paste.png"]) 自动打开
```

### 连续失败 2 次就停下来搜索

不要用原始猜测反复尝试。搜索 `playwright WeChat vue-model input not working` 往往10秒找到答案。

### `force=True` 绕过 overlay 拦截

当元素被透明遮罩覆盖时（如 modal backdrop），Playwright 默认会等待元素可点击并超时报错。

```python
await page.click(selector, force=True)  # 绕过可见性/交互性检查
```

但注意：**原创声明的 checkbox 不能用 force=True**，会绕过 Vue 事件监听，checkbox 状态不变。

---

## 11. 代理与网络问题

### ClashX / V2Ray 代理拦截 localhost

代理软件会拦截对 `localhost:9222` 的请求，导致 Playwright 连接 CDP 失败。

**必须设置 NO_PROXY**：

```python
import os
os.environ['NO_PROXY'] = 'localhost,127.0.0.1'
os.environ['no_proxy'] = 'localhost,127.0.0.1'
```

或在启动脚本里导出：

```bash
export NO_PROXY=localhost,127.0.0.1
python one_click_publish.py ...
```

### 坐标映射（物理点击，Mac Retina，Chrome 最大化）

当需要用 `cliclick` 等工具做物理点击时（如无法用 Playwright 的场景）：

```
Chrome 窗口 bounds: (0, 34, 1800, 904)
innerHeight: 749, outerHeight: 870
Chrome UI 高度: outerHeight - innerHeight = 121
内容区起始: window_top(34) + chrome_ui(121) = 155

screen_x = page_x
screen_y = 155 + page_y
```

---

## 快速参考：关键选择器

| 元素 | 选择器 |
|------|--------|
| 标题输入框 | `#title` |
| 简介输入框 | `#js_description` |
| 正文编辑器 | `document.querySelectorAll('[contenteditable=true]')[1]` |
| 封面区域 | `.js_cover_btn_area` |
| 图片库按钮 | `.pop-opr__button.js_imagedialog` |
| 图片库列表项 | `.weui-desktop-img-picker__item` |
| 投票按钮（顶部导航）| `#js_editor_insertvote` |
| 投票对话框 | `.vote_dialog__body` |
| 投票输入框 | `.vote_dialog__body input.weui-desktop-form__input` |
| 加选项按钮 | `a.ic_option_add` |
| 原创声明对话框 | `.weui-desktop-dialog:has(#js_original_edit_box)` |
| 原创协议 checkbox | `.weui-desktop-dialog:has(#js_original_edit_box) .original_agreement .weui-desktop-icon-checkbox` |
| 赞赏开关（页面级）| `.js_reward_open` |
| 保存草稿 | `#js_submit` 或触发 Cmd+S |
| mdnice 编辑器 | `.CodeMirror` |
| mdnice 主题按钮 | `a.nice-menu-link:has-text('主题')` |
| mdnice 主题列表 | `.theme-list > *` |
| mdnice 复制微信 | `a.nice-btn-wechat` |

---

*最后更新：2026-03-03 | 基于蒸馏门文章发布实战*
