"""
连接到现有的 Chrome 浏览器并提取微信文章内容
"""
import asyncio
import json
from playwright.async_api import async_playwright


async def connect_to_chrome():
    """连接到正在运行的 Chrome 浏览器"""

    async with async_playwright() as p:
        print("正在连接到 Chrome 浏览器...")
        print("确保 Chrome 已经用远程调试模式启动")
        print("启动命令: /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222\n")

        try:
            # 连接到现有的 Chrome 实例
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            print("✓ 成功连接到 Chrome!\n")

            # 获取所有上下文
            contexts = browser.contexts

            # 获取所有页面
            pages = []
            if contexts:
                for context in contexts:
                    pages.extend(context.pages)

            if not pages:
                print("没有打开的标签页")
                print("提示：请确保在Chrome中打开了文章页面")
                return

            print(f"找到 {len(pages)} 个打开的标签页:\n")

            # 显示所有标签页
            for i, page in enumerate(pages):
                title = await page.title()
                url = page.url
                print(f"{i+1}. {title}")
                print(f"   URL: {url}\n")

            # 查找微信文章标签页
            weixin_page = None
            for page in pages:
                if "mp.weixin.qq.com" in page.url:
                    weixin_page = page
                    break

            if not weixin_page:
                print("未找到微信文章标签页")
                print("请在 Chrome 中打开文章: https://mp.weixin.qq.com/s/_kt0SPuWWiiu7XwqNZKZAw")

                # 让用户选择标签页
                try:
                    choice = input("\n输入标签页序号（或按回车跳过）: ").strip()
                    if choice and choice.isdigit():
                        idx = int(choice) - 1
                        if 0 <= idx < len(pages):
                            weixin_page = pages[idx]
                except:
                    pass

            if not weixin_page:
                print("未选择标签页，退出")
                await browser.close()
                return

            print(f"\n正在提取内容...")
            print(f"当前页面: {await weixin_page.title()}\n")

            # 等待页面加载
            await weixin_page.wait_for_load_state("domcontentloaded")

            # 检查是否需要验证
            page_text = await weixin_page.evaluate('document.body.innerText')

            if '环境异常' in page_text or '验证' in page_text:
                print("⚠️  检测到验证页面")
                print("请在 Chrome 浏览器中手动完成验证")
                print("等待60秒，让您有时间完成验证...")

                # 等待验证完成，每5秒检查一次
                for i in range(12):  # 60秒 / 5秒 = 12次
                    await weixin_page.wait_for_timeout(5000)
                    current_text = await weixin_page.evaluate('document.body.innerText')
                    if '环境异常' not in current_text and '验证' not in current_text and len(current_text) > 200:
                        print("✓ 检测到页面已更新，继续提取内容...")
                        break
                    print(f"等待中... ({(i+1)*5}/60秒)")

            # 提取文章内容
            article_data = await weixin_page.evaluate('''() => {
                // 获取标题
                let title = '';
                const titleSelectors = [
                    '#activity-name',
                    'h1',
                    '.rich_media_title',
                    '[id*="title"]'
                ];

                for (let selector of titleSelectors) {
                    const element = document.querySelector(selector);
                    if (element && element.innerText.trim()) {
                        title = element.innerText.trim();
                        break;
                    }
                }

                if (!title) {
                    title = document.title;
                }

                // 获取文章内容
                let content = '';
                let selector_used = '';

                const contentSelectors = [
                    '#js_content',
                    '.rich_media_content',
                    '#img-content',
                    'div[id*="content"]',
                    'article'
                ];

                for (let selector of contentSelectors) {
                    const element = document.querySelector(selector);
                    if (element && element.innerText.length > 100) {
                        content = element.innerText;
                        selector_used = selector;
                        break;
                    }
                }

                // 如果都找不到，使用 body
                if (!content) {
                    content = document.body.innerText;
                    selector_used = 'body';
                }

                // 清理内容：去掉o1的"长考"示例部分和页尾信息
                let cleanContent = content;

                // 首先去掉附录部分（长考示例）
                const appendixMarkers = ['STRAWBERRY 长考', 'STRAWBERRY长考'];
                for (let marker of appendixMarkers) {
                    const idx = cleanContent.indexOf(marker);
                    if (idx > 0) {
                        cleanContent = cleanContent.substring(0, idx).trim();
                        break;
                    }
                }

                // 然后去掉页尾信息
                const footerMarkers = ['进技术交流群请添加', '关于AINLP'];
                for (let marker of footerMarkers) {
                    const idx = cleanContent.indexOf(marker);
                    if (idx > 0) {
                        cleanContent = cleanContent.substring(0, idx).trim();
                        break;
                    }
                }

                // 获取作者信息
                let author = '';
                try {
                    const authorElem = document.querySelector('#js_name, .profile_nickname');
                    if (authorElem) {
                        author = authorElem.innerText.trim();
                    }
                } catch (e) {}

                return {
                    title: title,
                    author: author,
                    content: cleanContent,
                    originalLength: content.length,
                    cleanedLength: cleanContent.length,
                    selector: selector_used,
                    url: window.location.href
                };
            }''')

            # 保存内容
            title = article_data['title']
            content = article_data['content']
            author = article_data['author']
            selector = article_data['selector']
            url = article_data['url']

            print(f"✓ 使用选择器: {selector}")
            print(f"✓ 标题: {title}")
            if author:
                print(f"✓ 作者: {author}")
            print(f"✓ 原始内容长度: {article_data.get('originalLength', len(content))} 字符")
            print(f"✓ 清理后内容长度: {len(content)} 字符\n")

            # 保存为文本文件
            output_file = "weixin_article.txt"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"标题: {title}\n")
                if author:
                    f.write(f"作者: {author}\n")
                f.write(f"URL: {url}\n")
                f.write("=" * 80 + "\n\n")
                f.write(content)

            print(f"✓ 文章已保存到: {output_file}")

            # 保存为 JSON
            json_file = "weixin_article.json"
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump({
                    "title": title,
                    "author": author,
                    "url": url,
                    "content": content,
                    "length": len(content)
                }, f, ensure_ascii=False, indent=2)

            print(f"✓ JSON 已保存到: {json_file}")

            # 截图（使用视口截图，避免全页截图的重复问题）
            print("正在生成文章截图...")
            try:
                # 滚动到顶部并等待
                await weixin_page.evaluate('window.scrollTo(0, 0)')
                await weixin_page.wait_for_timeout(2000)

                # 使用视口截图（只截取当前可见区域）
                # 微信文章的full_page截图有重复问题，所以只截取视口
                screenshot_file = "weixin_article_screenshot.png"
                await weixin_page.screenshot(path=screenshot_file, full_page=False)
                print(f"✓ 页面截图已保存到: {screenshot_file}（视口截图）")

                # 可选：生成文章主体部分的PDF（无重复问题）
                print("正在生成PDF版本...")
                pdf_file = "weixin_article.pdf"
                await weixin_page.pdf(
                    path=pdf_file,
                    format='A4',
                    print_background=True,
                    margin={'top': '1cm', 'bottom': '1cm', 'left': '1cm', 'right': '1cm'}
                )
                print(f"✓ PDF已保存到: {pdf_file}（完整内容，无重复）")
            except Exception as e:
                print(f"⚠️  截图/PDF生成失败: {e}")

            print("\n✅ 完成！")

            # 不关闭浏览器，因为是用户的浏览器
            # await browser.close()

        except Exception as e:
            print(f"❌ 错误: {e}")
            print("\n请确保:")
            print("1. Chrome 已经用远程调试模式启动")
            print("2. 启动命令: /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222")


if __name__ == "__main__":
    asyncio.run(connect_to_chrome())
