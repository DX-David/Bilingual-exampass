---
name: bilingual-exampass
description: 将课程资料（PPT/Word/PDF）按章节生成详细全面的中英对照笔记；提供课件后可选纯笔记PDF、含原课件对照和英文测验的完整HTML，或两者都要，保留知识卡、自测答案和章末词汇表。
---

## 命令路由

检查 `args`：
- `"final"` 或 `"final "` 开头 → 出题，详见 `exampass-final.md`。
- `"graph"` 或 `"graph "` 开头 → 知识图谱，详见 `exampass-graph.md`。
- `"grade"` 或 `"批改"` 开头 → **AI批改**（下面）。
- 其他 → **默认流程**（下面）。

> 你需要阅读的文件：`agents/skeleton-agent.md`、`agents/notes-agent.md`（每个的 Part 4 是实际 prompt）；选择完整笔记或两者都要时，另读 `agents/item-agent.md`。生成前读 `references/output-modes.md` 确认输出选择，生成笔记前读 `references/note-depth.md` 与 `references/note-layout.md`。讲解方法参考 `exampass-writing.md`。

---

## 默认流程

先按下面的三选项确定输出，再生成对应文件。各模式共享详细全面的中英对照正文：按主题分区、独立知识卡、引入/结论/动机/定义/应用/易错分块、目录、重要度标记、双语自测答案和章末词汇表。完整笔记另带原课件对照及全英文互动测验。

### 提供课件后的输出选择（先于最终生成）

用户提供课件但尚未指定本批输出时，展示以下**三个选项**并等待选择：

| 选项 | 输出内容 | 文件格式 |
| --- | --- | --- |
| **纯笔记** | 完整中英对照笔记、笔记内自测及答案、词汇表；无旁栏PPT、无独立章节测验 | PDF，便于导入平板批注 |
| **完整笔记（含PPT对照）** | 中英对照笔记 + 原课件对照 + 全英文互动测验 | HTML |
| **两者都要** | 同一份正文分别生成纯笔记PDF与完整笔记HTML | PDF + HTML |

有选择工具时用三个选项提问：「这份课件希望生成哪种结果？」；否则直接列出上述选项让用户回复。用户已明确说「只要PDF」「纯笔记」「带PPT的完整笔记」或「两者都要」时直接采用，不重复询问。同一批课件沿用已选模式；新一批未指定时重新提供选择，不把上次结果当作默认答案。等待期间可先提取、读取和核对资料，最终输出按用户选择执行。

选择记录、文件命名与各模式的导出/验收规则见 `references/output-modes.md`。此选择用于默认课件笔记流程；`final`、`graph`、`grade` 仍按各自命令路由执行。

**固定排版偏好：中英对照段落直接显示正文，不添加「中文」「英文」「English」「ENGLISH」「ZH」「EN」等独立语言标签、前缀或额外提示行，CSS伪元素也不得生成这些标签。保留不可见的 `lang` 属性及中英配对结构，用相邻位置和现有样式区分语言。此要求适用于正文、原例、易错、小结和自测答案；正常的内容标题与词汇表列名保留。**

**紧凑排版偏好：减少段落、中英配对、卡内板块、知识卡及主题大节之间的留白，避免多层 margin/padding 叠加；正文保持易读行距，不靠空行撑开层次。沿用 `templates/notes.css` 的紧凑间距，具体见 `references/note-layout.md`。**

### 默认内容标准：详细、全面（硬约束）

用户未另行要求精简时，默认生成足以深入掌握课件的详解笔记：**逐页核对正文、图表和备注；保留并详细解释全部教学原例；展开机制、条件、步骤和易错点**。不能用摘要、小结或原课件对照栏替代正文讲解，也不能因重要度标签较低而省略课件知识。完整执行要求及交付覆盖核对见 `references/note-depth.md`。详细内容仍按现有知识卡与中英配对格式呈现。

### Phase 0 · 提取

```bash
cd <skill目录>
python scripts/run_exampass.py <课程目录>
```

产 `.epa_work/chapter_manifest.json` + 每章 `chapters/<章名>/_extraction_bundle.json`。manifest 的每个条目有 `source_files`（该章源 PDF 绝对路径）。

提取完成后，按 `references/note-depth.md` 逐页核对原文及原图，补入文字提取遗漏的图表信息。PPT/PPTX 还需读取原文件的非空演讲者备注，不能假定转换后的 PDF 已包含备注。为每章保存内部覆盖记录，并把原例、图表解读、备注及原图路径随对应知识组件提供给后续讲解。

### Phase 1 · 骨架

读 `agents/skeleton-agent.md` Part 4。核心规则：
- 读 manifest + 每章 bundle 的 merged_text 了解内容
- 输出 `knowledge_skeleton.json`：`{title, chapters:[{id:"ch1",label:"章名",kcs:[{id,label,type:"fact|concept|procedure|principle",importance:"must|key|freq|info",deps:[],is_hub:bool,source_refs:["PDF名/页码范围"]}]}]}`
- **source_refs 页码必须真实**（不能超过 PDF 实际页数；先确认 PDF 页数再写页码）
- 再写切片：`slices/<章id>_skeleton.json` + `slices/<章id>_extract.json`
- 切片必须保留相关页的完整教学原例、图表信息和备注；遵循 `references/note-depth.md`，不能在骨架归纳时丢掉细节。

### Phase 2 · 笔记及按需出题

所有模式先生成同一套笔记正文片段 `.epa_work/notes/<章id>.html`，作为内部源稿。仅「完整笔记」和「两者都要」执行下面的题目生成流程；「纯笔记」保留正文内双语自测及答案，但跳过独立章节题库。

**笔记 Agent prompt（精简）**：

```
你是讲解设计师。读 [骨架切片路径] 和 [提取切片路径]。
先读 references/note-depth.md 与 references/note-layout.md，为每个知识组件写一张详细知识卡，输出到 [.epa_work/notes/<章id>.html]。

规则：
1. 叙事弧：Hook（一句话场景/谜题）→ TL;DR（<div class="tldr">粗体一句话结论</div>）→ Why → What → How → Checkpoint自测（<div class="checkpoint">问题<details class="cp-answer"><summary>参考答案</summary>答案</details></div>）。知识讲解、示例、易错点和自测问题/答案均须中英逐段对应；先中文后英文，不能只翻译标题或摘要。
2. 核心概念包 <span class="kp">…</span>，解释包 <span class="exp">…</span>
3. 每个H3末尾标四色标签（中文："必考""重点""高频""了解"），class用 tag-must/tag-key/tag-freq/tag-info
4. Hook/Why/What/How各自用 div.note-block，首行 div.note-label 中英小标题；结论单独 div.tldr，易错单独 blockquote。每块中用 div.bilingual-pair 包 p[lang="zh-CN"] 与 p[lang="en"]。不要混写几个用途、不要每段重复标签。
5. 公式 $$…$$ 或 $…$，引号用「」，箭头 --&gt;
6. 每个H2/H3末尾加 <span data-slides="页码"></span>（从 source_refs 取该KC的起始页码）
7. 只写H2/H3，不写H1。不要输出 <!DOCTYPE>/<html>/<head>/<style>/<body> 标签——只输出 body 内部片段
8. 按主题用 H2 大节、每个知识点用一个 H3 独立卡片。每个概念必答"是什么/为什么需要它/怎么用"，同一知识点的中英文必须表达同一事实、条件、公式和结论。
9. 各大节末尾放小结与自测，章末可另设 H2「章节回顾与自测 / Chapter review and check」。每章所有知识点和自测之后，追加一个 H2「英文生词与解释 / English Vocabulary」。用表格列出课程中实际出现的重要英文术语、中文对应词、英文定义和简明中文释义；至少覆盖骨架中的核心概念，不能臆造术语。
10. 结构按 references/note-layout.md：章首概览 → H2 大节 → H3 独立知识卡 → 大节小结与自测 → 章末词汇表。每个讲解环节使用独立 note-label 和 bilingual-pair，禁止把 Why/What/How 写进同一个段落；目录由引擎分组生成，样式由 notes.css 提供。
11. 默认深度按 references/note-depth.md：完整讲解分配范围的正文、图表、备注和全部教学原例；保留真实数值、单位、条件、分类与例外；逐步展开机制与案例，并说明结果、原理和易错点。TL;DR只限制结论块长度，不限制正文深度。交付前将覆盖记录逐项对应到笔记，发现遗漏先补齐；无法读取或确认的内容明确记录，不能编造补全。
```


## 清晰排版契约（硬约束）

生成前读 `references/note-layout.md`，按其章节、知识卡、讲解环节和双语配对格式输出。页面样式由 `templates/notes.css` 管理。

**题目 Agent prompt（精简）**：

```
你是命题专家。读 [骨架切片路径] 和 [提取切片路径]。
为该章出一套题目，输出到 [.epa_work/questions/<章id>.json]。

规则：
1. 题型按学科选——算法课必须包含 calc 和 code，文科不出 calc/code
2. 题量：每个KC至少1题，枢纽概念至少2题。整章≥8题
3. choice：4个选项，正确答案 A/B/C/D 均匀分布（各字母次数差≤1），干扰项对应真实误解
4. 文本里不等号用 &lt; 和 &gt; 或 $...$，禁止裸 <
5. JSON字符串内引号用「」，禁止裸 "
6. 每题含 kc_id/cognitive_level(remember|understand|apply|analyze)/difficulty(basic|medium|hard)
7. 写完用 json.loads() 自检
8. 整份测验内容必须全英文：题干、选项、填空答案、标准答案、解析、pitfall、题型小标题及测验说明都不得出现中文。JSON 字段名和类型标识保持 schema 原样。

JSON结构：{"chapter_id":"chX","questions":[{"type":"choice|tf|fill|calc|code|short","points":N,"kc_id":"kcX.Y","question":"...","options":["A","B","C","D"],"answer":0,"explanation":"...","cognitive":"...","difficulty":"...","pitfall":"..."}]}
对于 tf（判断）题：answer: true 表示命题正确（正确），answer: false 表示命题错误（错误）。禁止对 tf 题使用数字 0/1 —— 只用布尔值 true/false。
```

> 以上 prompt 中的文件路径：骨架切片在 `.epa_work/slices/<章id>_skeleton.json`，提取切片在 `.epa_work/slices/<章id>_extract.json`。笔记写入 `.epa_work/notes/<章id>.html`，题目写入 `.epa_work/questions/<章id>.json`。
> 
> 如果你自己能逐章写完（不调子Agent），**直接写就行**——质量优先，不要为了并行而并行。如果起子Agent，确保每个子Agent只拿自已那章的切片，不要读整个 bundle。

### Phase 3 · 评审+修订（可选）

如果时间允许，可以起 reviewer-agent + solver-agent 逐章审查。但**不是必须的**——如果 Phase 2 的笔记和题目已经认真写了，跳过评审直接渲染也没问题。

独立评审可选；逐页与逐例的覆盖核对必须完成，具体按 `references/note-depth.md` 的交付要求执行。

### Phase 4 · 按所选模式导出

**纯笔记**：按 `references/output-modes.md` 的PDF规则，将笔记正文源稿导出为 `<课程目录>/EPA/<章名>_纯笔记.pdf`。不运行要求题库的完整页渲染命令，不生成PPT旁栏或章节测验。

**完整笔记**：运行现有完整页渲染命令：

```bash
python scripts/render_chapters.py <课程目录> full
```

这会把每章原课件**全部页**渲染成图贴进右栏（`full` 密度）；PPTX先转换为渲染副本，原课件不改动。只有用户要求只放重点页时才改用 `key`。输出在 `<课程目录>/EPA/`，每章一个HTML合并页，含笔记、原页对照和英文测验。

**两者都要**：对同一份正文分别执行以上PDF导出和完整HTML渲染，交付两种文件。两份都验收后才说明已完成；某一份失败时保留已完成结果，说明未完成项。

交付前按 `references/output-modes.md` 检查实际文件与选择一致。PDF可导入平板笔记软件，HTML在浏览器中使用。

---

## AI批改流程

`args` 形如 `"grade <JSON路径>"` 或 `"批改 <JSON路径>"`。

**读取 answers JSON**（由交互式测试页的「AI一键批改」按钮生成，默认下载到下载文件夹）：
```json
{
  "chapter": "数据结构 - 第3章",
  "saved_at": "2026-06-25T14:30:00",
  "questions": [
    {
      "index": 0, "type": "tf", "question": "...",
      "options": null, "correct_answer": true,
      "user_answer": 0, "points": 2,
      "explanation": "...", "kc_id": "kc3.1", "images": []
    }
  ]
}
```

**Step 1 · 客观题自动批改**（choice / multi / tf / fill）：
- 按与 `test_js_template.js` 相同的逻辑（`tfAnswerIndex`/`choiceAnswerIndex`/`normText`）比对答案
- 得分：全对=满分，多选部分正确=按比例，填空按空批

**Step 2 · 主观题 AI 批改**（short / calc / code / essay / comprehensive）：
- 每题：读题目 + 用户作答 + 分析 `images`（如有）
- 给出 0～满分的得分和简短批改评语
- 参考 `explanation` 字段提供标准解析
- 学生可见的评语、解析和报告文字均用英文，与全英文测验保持一致。

**Step 3 · 统计**：
- 计算 total_score / objective_score / subjective_score
- 按 kc_id 分组求每个知识点的掌握度（得分/满分）

**Step 4 · 生成报告**：

```python
from scripts.template_engine import save_grade_report_html
import os, json
from datetime import datetime

# 构造 grade_data（见 save_grade_report_html 文档）
grade_data = {
    "chapter": answers["chapter"],
    "submitted_at": answers["saved_at"],
    "graded_at": datetime.now().isoformat(),
    "grade_count": 1,   # 根据已有批改报告数量+1
    "total_score": ...,
    "max_score": ...,
    "objective_score": ..., "objective_max": ...,
    "subjective_score": ..., "subjective_max": ...,
    "results": [...],  # 每题: index/type/question/options/user_answer/correct_answer/score/max_points/verdict/comment/explanation/kc_id/images
    "kc_mastery": {...},  # kc_id → {label, score, max, pct}
    "wrong_questions": [...]  # wrong/partial 题的 index 列表
}

# 输出到 answers JSON 所在目录
json_dir = os.path.dirname(json_path)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
ch = answers["chapter"].replace(" ", "_").replace("/", "_")[:30]
out_path = os.path.join(json_dir, f"{ch}_批改_{ts}.html")
save_grade_report_html(grade_data, out_path)
print(f"报告已生成：{out_path}")
```

**判断 grade_count**：扫描同目录下 `*_批改_*.html` 文件数量 + 1。

**注意**：某些 tf 题的 `correct_answer` 字段可能存在数据问题（答案填反了），批改时如果确认 `correct_answer` 与 `explanation` 矛盾，以 `explanation` 为准，并在 `comment` 中注明"数据可能有误，请复核"。

