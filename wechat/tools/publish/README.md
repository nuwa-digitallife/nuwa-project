# 微信公众号发布工具集

将 article_mdnice.md 通过 mdnice 排版后注入微信编辑器的工具链。

## 目录结构

```
publish/
├── README.md              # 本文件
├── https_server.py        # HTTPS 本地服务器（图片上传用）
├── inject_js.py           # AppleScript → Chrome JS 注入
└── js/                    # JS 模板
    ├── find_editor.js     # 检测编辑器
    ├── set_title.js       # 设置标题
    ├── set_description.js # 设置简介
    ├── upload_image.js    # 上传图片到 CDN
    ├── enable_original_reward.js  # 原创 + 赞赏
    ├── click_confirm.js   # 点击确认按钮
    ├── remove_empty_tables.js     # 删除空表格
    └── trigger_save.js    # 触发保存
```

## 完整发布流程

### 前置条件

- Chrome 已登录微信公众号后台
- `source ~/venv/automation/bin/activate`
- 首次使用需在 Chrome 接受自签证书：访问 `https://localhost:18443`

### Step 1：mdnice 排版

1. 打开 mdnice.com
2. 粘贴 article_mdnice.md 内容
3. 选择主题（橙心）
4. 复制富文本到剪贴板

### Step 2：打开微信编辑器 + 粘贴

1. Chrome 中打开微信后台 → 新建图文
2. Cmd+V 粘贴到编辑器

### Step 3：注入标题/简介

```bash
TOOLS=wechat/tools/publish

# 设置标题
python $TOOLS/inject_js.py $TOOLS/js/set_title.js \
  --var '__TITLE__=文章标题'

# 设置简介
python $TOOLS/inject_js.py $TOOLS/js/set_description.js \
  --var '__DESCRIPTION__=文章简介'
```

### Step 4：上传配图

```bash
# 终端 1：启动 HTTPS 服务器
python $TOOLS/https_server.py \
  wechat/公众号选题/YYYY-MM-DD|选题/images 18443

# 终端 2：逐个上传（TOKEN 从编辑器 URL 中提取）
python $TOOLS/inject_js.py $TOOLS/js/upload_image.js \
  --var __IMAGE_URL__=https://localhost:18443/image.png \
  --var __TOKEN__=xxx \
  --var __IMAGE_NAME__=image.png
```

### Step 5：原创 + 赞赏

```bash
python $TOOLS/inject_js.py $TOOLS/js/enable_original_reward.js
python $TOOLS/inject_js.py $TOOLS/js/click_confirm.js --wait 1
```

### Step 6：清理 + 保存

```bash
python $TOOLS/inject_js.py $TOOLS/js/remove_empty_tables.js
python $TOOLS/inject_js.py $TOOLS/js/trigger_save.js
```

### Step 7：人工确认发布

1. 预览确认排版、配图、投票
2. 扫码发布

## 关键经验

### 图片上传方案
微信编辑器在 HTTPS 页面，无法 fetch HTTP localhost（mixed content）。
解决：自签证书 HTTPS 本地服务器 + Chrome 信任证书。

### ProseMirror 陷阱
直接改 `textNode.textContent` 不触发变更检测，Cmd+S 保存的是旧内容。
修改 DOM 后必须 `editor.dispatchEvent(new Event("input", {bubbles: true}))`。

### AppleScript + 中文
中文在 AppleScript 嵌套 JS 时会报转义错误。
解决：JS 写文件 → base64 编码 → `eval(atob('...'))`（inject_js.py 自动处理）。

### Chrome 多窗口
编辑器不一定在 window 1。inject_js.py 自动搜索所有窗口中 URL 包含 `appmsg_edit` 的 tab。
