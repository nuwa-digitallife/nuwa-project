ni'x# 微信文章爬虫项目记录

## 项目背景
使用Playwright连接到已打开的Chrome浏览器来爬取微信公众号文章，绕过反爬虫机制。

## 核心方案
**通过Chrome远程调试协议(CDP)连接到用户已登录的浏览器**
- 启动命令：`./start_chrome_debug.sh` (端口9222)
- 运行脚本：`python connect_chrome.py`

## 技术要点

### 1. 绕过反爬虫的关键
- 使用用户已登录的Chrome浏览器（携带登录状态和cookies）
- 通过CDP协议直接读取页面内容
- 自动检测验证页面并等待用户手动完成验证（60秒超时）

### 2. 内容清理规则
需要过滤的内容：
- **长考附录**：以"STRAWBERRY 长考"开始的o1模型思考过程
- **页尾信息**：包含"进技术交流群"、"关于AINLP"等
- 清理逻辑在 `connect_chrome.py:148-165`

### 3. 截图问题及解决
- **问题**：微信页面的`full_page=True`截图会产生大量重复内容
- **解决方案**：
  - 使用视口截图（`full_page=False`）获取顶部预览
  - 同时生成PDF版本保存完整内容（无重复问题）

## 文件说明

### 核心脚本
- `connect_chrome.py` - 主爬虫脚本（推荐使用）
- `start_chrome_debug.sh` - Chrome调试模式启动脚本
- `get_chrome_cookies.py` - Cookie提取工具
- `fetch_with_cookies.py` - 基于Cookie的爬虫（备用方案）

### 输出文件
- `weixin_article.txt` - 纯文本格式
- `weixin_article.json` - JSON格式（包含元数据）
- `weixin_article.pdf` - PDF版本（推荐，完整无重复）
- `weixin_article_screenshot.png` - 视口截图

## 使用流程

1. **启动Chrome调试模式**
   ```bash
   ./start_chrome_debug.sh
   ```

2. **在Chrome中打开微信文章**
   - 手动打开文章链接
   - 完成任何必要的验证

3. **运行爬虫脚本**
   ```bash
   source .venv/bin/activate
   python connect_chrome.py
   ```

4. **等待处理**
   - 脚本会自动检测验证页面
   - 如需验证，在60秒内手动完成
   - 自动提取内容并保存

## 已验证示例
- URL: https://mp.weixin.qq.com/s/_kt0SPuWWiiu7XwqNZKZAw
- 标题: 万字长文推演OpenAI o1 self-play RL 技术路线
- 作者: AINLP
- 原始长度: 25,759字符 → 清理后: 9,259字符

## 技术细节

### 验证处理逻辑
```python
# 检测验证页面关键词
if '环境异常' in page_text or '验证' in page_text:
    # 等待60秒，每5秒检查一次页面状态
    # 检测到内容更新后自动继续
```

### 内容提取选择器优先级
1. `#js_content` (首选)
2. `.rich_media_content`
3. `#img-content`
4. `div[id*="content"]`
5. `article`

### PDF生成参数
```python
await page.pdf(
    path=pdf_file,
    format='A4',
    print_background=True,
    margin={'top': '1cm', 'bottom': '1cm', 'left': '1cm', 'right': '1cm'}
)
```

## 待扩展功能

- [ ] 批量爬取文章列表
- [ ] 支持其他公众号平台
- [ ] 自动化验证处理
- [ ] 图片下载和本地保存
- [ ] Markdown格式输出
- [ ] 数据库存储

## 依赖
- Python 3.9+
- Playwright 1.40.0
- Chrome浏览器

## 注意事项
1. Chrome必须在调试模式下运行（端口9222）
2. 脚本不会关闭用户的Chrome浏览器
3. 遇到验证时需要手动完成（60秒超时）
4. PDF版本最可靠，无重复且格式完整

## 最后更新
2025-10-19 - 完成长考过滤和截图修复
