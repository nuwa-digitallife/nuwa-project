# 内容残缺复盘：engine.py 全流程产出的遗漏清单

**日期**: 2026-03-13
**涉及文章**: OpenClaw算力涟漪、AI就业冲击

---

## OpenClaw算力涟漪

### 1. 太空数据中心（马斯克 Starlink 算力节点）完全缺失
- **严重度**: 高（用户明确指出的选题核心角度之一）
- **原因**: 迭代检索跑了3轮、提取131个实体，但实体图扩展只能发现"已提到的关联实体"。"马斯克太空数据中心"是跨领域创意联想（算力→卫星→太空基建），不在现有实体图的邻域内
- **根因**: `deep_research.py` 的迭代收敛算法按实体图谱扩展，擅长深挖已知分支，但无法做"跨域跳跃"。创意角度/反直觉联想仍需人工种子
- **修复建议**: 在 `topic_brief.md` 中增加"必须覆盖的角度/实体"字段，作为检索种子注入第一轮 prompt

### 2. 配图文件名不匹配
- **严重度**: 中
- **原因**: `collect_images` (image_collector.py) 生成的文件名（img_1_nvidia_market_share等）与 article_mdnice.md 中引用的文件名（img_0_claude_code_growth等）不一致
- **根因**: image_collector 和 article 写作是独立 pass，没有文件名协调机制。article 里的图片描述 alt text → 文件名映射，与 image_collector 从 publish_guide 提取的映射不同
- **影响**: 磁盘上有5张图但只有2张能被文章正确引用，3张实际缺失
- **修复建议**:
  - image_collector 应以 article_mdnice.md 中的 `![alt](path)` 为准生成文件名
  - 或在 post-processing 增加"文件名对齐"步骤

### 3. 标题缺少 "AI" 关键词
- **严重度**: 中
- **原因**: Pass 4.5 标题优化Agent 偏好文学性标题，没有 SEO/搜索发现性约束
- **修复建议**: 在 `pass4b_title.md` prompt 中增加约束："标题必须包含 AI/Agent/模型 等关键词之一，确保公众号搜索可发现性"

### 4. 简介推荐标注不清晰
- **严重度**: 低
- **原因**: `description_options.md` 列出3个备选但没标推荐（title_options.md 有推荐，但 publish_guide 引用的是 description_options.md）
- **修复建议**: 统一在 `publish_guide.md` 顶部同时标注推荐标题和推荐简介

---

## AI就业冲击

### 1. 封面图完全缺失
- **严重度**: 高（发布必需）
- **原因**: Gemini API key 未配置，gen_image.py 跳过了封面生成
- **根因**: .env 文件不存在，API key 没有持久化配置
- **修复建议**: 在 engine.py post-processing 中，封面生成失败应该是 FATAL 而非 WARNING

### 2. 配图文件名全部不匹配
- **严重度**: 高（6张图全部引用失败）
- **原因**: 同 OpenClaw #2 —— image_collector 生成的文件名（img_0_theory_vs_reality_gap 等）与 article_mdnice.md 引用的名字（img_1_gap_94vs33 等）完全不同
- **影响**: 看似有5张图，实际文章中一张都加载不了
- **修复建议**: 同上，image_collector 应以 article 中的实际引用路径为准

### 3. MIT冰山图缺失（img_4_mit_iceberg.png）
- **严重度**: 中
- **原因**: image_collector 按自己的编号生成了 img_0~img_5，跳过了 MIT 冰山这个概念
- **根因**: 同 #2 的文件名映射问题

### 4. 标题缺少 "AI" 关键词
- **严重度**: 中
- **原因**: 同 OpenClaw #3

---

## 系统性根因总结

| 根因 | 影响范围 | 修复优先级 |
|------|---------|-----------|
| image_collector 文件名与 article 引用不对齐 | 所有文章 | **P0** — 每篇都会命中 |
| 标题优化 prompt 缺 SEO 约束 | 所有文章 | P1 |
| 封面生成失败不阻断流水线 | 无封面时 | P1 |
| 迭代检索无法做跨域跳跃 | 需要创意角度的选题 | P2（设计层面，短期用人工种子补） |
| publish_guide 推荐标注不统一 | 发布效率 | P2 |

---

## 本次人工补救清单

- [x] AI就业冲击：重命名5张图文件名对齐（img_0→img_1, img_1→img_2...）
- [x] OpenClaw：用 matplotlib 生成 3 张缺失图（claude_code_growth, air_vs_liquid, smr_timeline）
- [x] AI就业冲击：用 matplotlib 生成 MIT 冰山图 + 封面图
- [ ] 两篇标题加 "AI" 关键词
- [ ] OpenClaw：太空数据中心内容（本次不加，下版迭代）
