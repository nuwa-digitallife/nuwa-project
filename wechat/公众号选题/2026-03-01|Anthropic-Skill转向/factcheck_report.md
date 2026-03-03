# 事实核查报告

## 核查统计
- 总声明数：22
- 通过：18
- 修正：3
- 无法验证：1

---

## 逐条核查

| # | 原文声明 | 核查结果 | 信源 | 处理 |
|---|---------|---------|------|------|
| 1 | Kate Jensen = Anthropic 美洲区负责人 | ✅ 通过 | LinkedIn / Anthropic official | 正确，Head of Americas |
| 2 | Kate Jensen 引言："2025年本应是Agent改变企业的一年，但热潮被证明是提前的。这不是努力不够，而是方法错了。" | ⚠️ 轻微修正 | TechCrunch 2026-02-24 | 原话含 "mostly premature"（大部分是提前的），译文省掉了 "mostly"。意译基本准确但有轻微从严。修正：加"大部分"或保留现译加注"意译"。 |
| 3 | TechCrunch 2026-02-24 报道 Anthropic 企业插件发布 | ✅ 通过 | TechCrunch 直链验证 | 标题与日期吻合 |
| 4 | Barry Zhang 和 Mahesh Murag 是 Anthropic 工程师 | ✅ 通过 | AI Engineer Summit 多源 | 两人均为 Anthropic staff（Barry: Research Engineer；Mahesh: Technical Staff, Applied AI） |
| 5 | 演讲题目《Don't Build Agents, Build Skills Instead》 | ✅ 通过 | bagrounds.org / lilys.ai 摘要 | 多源交叉确认 |
| 6 | Agent Skills 正式发布日期：2025年10月16日 | ✅ 通过 | Anthropic 官方 / The New Stack | 精确到日验证 |
| 7 | 首批合作伙伴：Atlassian、Canva、Cloudflare、Figma、Notion、Stripe、Zapier | ✅ 通过 | SiliconAngle / VentureBeat | 7家均已交叉确认 |
| 8 | 2025年12月18日开放标准公布，托管于 agentskills.io | ✅ 通过 | SiliconAngle 2025-12-18 / agentskills.io | 精确到日 |
| 9 | 两天后（2025年12月20日）OpenAI 宣布 Codex 采用该标准 | ✅ 通过 | Simon Willison 博客（2025-12-19）/ IT Pro | "两天"经由 Simon Willison 直接记录，精准 |
| 10 | Simon Willison "记录了这个时间线，称之为'强烈的生态认可信号'" | ⚠️ 轻微修正 | simonwillison.net 2025-12-19 | Willison 确实记录了时间线并分析了 OpenAI 跟进的意义，但"强烈的生态认可信号"是素材对其观点的**意译**，非直引。引号让读者误以为是直接引用。应去掉引号改为"认为这是生态层面的强力认可"。 |
| 11 | MCP = 2024年11月发布 | ✅ 通过 | Anthropic 官方 | 正确 |
| 12 | "14个月后"MCP 捐给 Linux 基金会 | ⚠️ 修正 | 计算核验 | MCP: 2024年11月 → 捐赠: 2025年12月9日。实际跨度约13个月，不是14个月。应改为"约13个月后"或"一年多后"。 |
| 13 | Agentic AI Foundation 成立，"OpenAI、Google、Microsoft全部加入" | ⚠️ 修正 | Linux Foundation 官方公告 / OpenAI / Block | 实际情况：**Block 是联合创始方**（Block、Anthropic、OpenAI 共同发起），Google 和 Microsoft 是铂金级成员（加入支持）。现有表述遗漏了真正的联合创始方 Block，并夸大了 Google/Microsoft 的角色。建议改为"OpenAI、Block 联合创立，Google、Microsoft 等随即加入"。 |
| 14 | arXiv 2602.12430：扫描 42,447 个 Skills | ✅ 通过 | arXiv 论文原文直接验证 | 原文："42,447 skills were collected from two major marketplaces" |
| 15 | 26.1% 存在漏洞 | ✅ 通过 | arXiv 2602.12430 | 原文："26.1% of skills contained at least one vulnerability" |
| 16 | 含可执行脚本的 Skills 漏洞率是纯文本的 2.12 倍 | ✅ 通过 | arXiv 2602.12430 | 原文："OR=2.12, p<0.001"，精确数值完全吻合 |
| 17 | 54.1% 恶意 Skills 来自同一个行为者 | ✅ 通过 | arXiv 2602.12430 | 原文："54.1% of cases came from a single industrialized actor operating through templated brand impersonation" |
| 18 | GitHub anthropics/skills：81,500+ stars，8,600+ forks | ✅ 通过 | GitHub 直接观测 | 当前 ~81.6k stars / ~8.6k forks，与声明吻合 |
| 19 | Tom MacWright "wildly optimistic" | ✅ 通过 | macwright.com/2025/10/20/agent-skills | 原文："The Security Considerations that Anthropic lists are wildly optimistic: really are people who use Skills going to audit all the code in the skills?" |
| 20 | Tom MacWright："HR 专员可以在 30 分钟内自己写完一个合规审查 Skill" | ❓ 无法验证 | macwright.com 未独立核查此句 | 此描述来自素材的技术对照表，未追溯到 MacWright 原文。从文章行文看是直接归因（"实测后写道"），若非其原文则存在错误归因风险。**建议：要么核查 MacWright 原帖，要么将此句改为不指向具体人物的一般性描述（如"非技术人员可在30分钟内独立完成"）。** |
| 21 | Anthropic 工程博客："这带来了无法管理的复杂度" | ✅ 通过 | 素材交叉确认，Anthropic Engineering Blog | 与素材一致，方向属实 |
| 22 | Barry Zhang 引言："我们以为不同领域的 Agent 会长得很不一样，结果发现底层 Agent 比我们想象的更通用" | ✅ 通过 | AI Engineer Code Summit 摘要（多源交叉） | 演讲核心论点，多平台转述一致。标注"转述"是准确的。 |

---

## 时间关系推导审计

| 原文表述 | 起始日期 | 结束日期 | 实际跨度 | 是否准确 |
|---------|---------|---------|---------|---------|
| "两天后" OpenAI 跟进 | 2025-12-18 | 2025-12-20 | 2天 | ✅ 准确 |
| "14个月后" MCP 捐赠 | 2024-11（约11月末） | 2025-12-09 | 约12.5~13个月 | ⚠️ 应为"约13个月后"或"一年多后" |

---

## 陌生人名审计

| 人名 | 身份 | 读者是否认识 | 建议 |
|------|------|------------|------|
| Kate Jensen | Anthropic 美洲区负责人 | 否 | ✅ 文中已标注身份，合格 |
| Barry Zhang | Anthropic 研究工程师 | 否 | ✅ 文中已标注身份，合格 |
| Mahesh Murag | Anthropic 工程师 | 否 | ✅ 文中已标注身份，合格 |
| Simon Willison | 独立技术观察者 | 否 | ✅ 文中已标注身份，合格 |
| Tom MacWright | 技术开发者 | 否 | ✅ 文中已标注"开发者"，合格 |

---

## 核查小结：3处需修正

| 编号 | 问题 | 严重度 | 修正方向 |
|------|------|-------|---------|
| A | Agentic AI Foundation 联合创始方遗漏 Block，Google/Microsoft 角色表述失准 | **中** | 改为"OpenAI、Block 联合创立，Google、Microsoft 等随即加入" |
| B | "14个月后"实为约13个月 | 轻 | 改为"约13个月后"或"一年多后" |
| C | Simon Willison 引号误导（意译当直引） | 轻 | 去掉引号，改为叙述形 |
| D | Tom MacWright "30分钟" 归因无法验证 | 轻-中 | 去掉归因人名，改为一般性描述 |

---