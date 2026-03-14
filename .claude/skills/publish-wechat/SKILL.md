# Skill: publish-wechat

微信公众号发布自动化。

## Trigger

用户说以下任意一种时触发：
- "发布公众号" / "发布文章" / "重新发" / "再发一次"
- "调试原创" / "调试赞赏" / "调试发布"
- "继续发布" / "publish"

## ⛔ 执行前强制读取（不读不做）

**每次**触发本 skill，在执行任何代码或调试前，必须先读以下文件：

```
1. Read memory/wechat-publish-automation.md    — 发布流程经验（原创/赞赏/编辑器/图片上传）
2. Read memory/browser-automation-lessons.md   — UI 自动化调试铁律
```

读完后，在输出中列出关键要点确认已读：
- 原创：作者默认公众号名，**不用填**
- 赞赏：账户默认公众号名，点确定即可
- Chrome CDP：必须 `--user-data-dir`
- 调试时**不要关闭浏览器**，修改代码后重试
- 同一方法失败 3 次 → 立刻 WebSearch

## 发布流程

```
1. Chrome CDP 已固化在代码里——connect() 发现 CDP 没响应会自动启动 Chrome
   无需手动启动。如需确认：curl -s http://localhost:9222/json | head -1

2. 运行发布脚本：
   cd wechat/tools/publish
   python3 one_click_publish.py --topic-dir "../../公众号选题/XXXX/"

3. 检查输出：
   - 图片上传成功？
   - mdnice 渲染成功？
   - 粘贴成功？
   - 原创/赞赏成功？
   - DOM 验证通过？

4. 如果某步失败：
   a. 先读 memory 文件看是否已有解决方案
   b. 修改代码
   c. 不关闭浏览器，直接重跑
   d. 失败 3 次 → WebSearch
```

## 调试铁律

1. **不要关闭浏览器** — 修改代码后重试，`browser.close()` 只断 CDP 不关 Chrome
2. **试三遍就查资料** — WebSearch "微信公众号 XX playwright"
3. **先查记忆再动手** — 本 skill 已强制读取
4. **理解 UI 再自动化** — 不确定字段要不要填？先截图看，然后查记忆
