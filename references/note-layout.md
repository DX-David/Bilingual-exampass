# 分层笔记格式

生成笔记前读取本文件及 `note-depth.md`。读者只看标题和边界，就应能辨认「当前大节 → 当前知识点 → 当前讲解环节」。本格式适用于本技能全部笔记。

## 内容组织

- 默认采用紧凑排版：段落不额外加上下内边距，中英之间约2px，相邻配对约6px，卡内板块的上边距与上内边距各约6px，知识卡之间约10px，小结外边距约8px，大节标题前约14–16px、后约8px。正文行高约1.5–1.55，表格单元格上下内边距约6px；移动端同样紧凑。通过标题、底色和细边线保留层次，避免嵌套容器重复留白、空段落和额外换行。间距由 `templates/notes.css` 统一维护，保持详细完整的双语内容。

- 开头用 `.chapter-overview` 给出简短中英章节概览：本章目标、主要大节及其关系。目录由引擎根据 H2/H3 自动生成，不要手写重复目录。
- 按知识结构划分大节，每节使用 `.note-section`，以 H2 命名。大节遵循知识依赖顺序，不为视觉分组改变先修关系。
- 每个知识点独占 `.kc-card`，在 `.kc-header` 中标明编号、H3 标题、重要度与真实 PPT 页码，用 `.kc-content` 容纳讲解。
- 卡片内按「先想一想 → 核心结论 → 为什么重要 → 概念与定义 → 应用与步骤 → 易错提醒」组织。每个环节有独立 `.note-label` 和内容区。引入只需一个具体问题，结论只需一句，其余按知识需要展开。**禁止把 Why / What / How 合写在一个段落中，禁止用正文里的连续粗体标签暗示分区。**
- 默认详细全面：按 `note-depth.md` 保留全部教学原例，使用可辨认的「课件原例 / Original slide example」分块；较长因果链或过程拆成步骤，多个例子分别标明。卡片正文可按内容充分扩展，不因保持短卡片而压缩或遗漏细节。
- 每个 `.bilingual-pair` 承载一项完整意思，中文与对应英文分别使用不可见的 `lang="zh-CN"` 和 `lang="en"`。直接呈现中英正文，**不得在段前或另起一行添加「中文」「英文」「English」「ENGLISH」「ZH」「EN」等语言标签，也不得通过 CSS 伪元素补上标签或占位行**。用相邻配对和现有底色、边线、间距区分语言。长环节可有多个配对块；并列条件用列表、操作顺序用编号列表、对比用表格，英文逐项对应中文。
- 小标题使用 `.note-label`，不要用 H2/H3 充当卡内小标题。重点用 `.kp`、解释用 `.exp`，避免整段加粗。
- 每个大节末尾给出 2–4 条关键结论的小结（`.section-summary`），并放 1–2 道带折叠双语答案的 `.checkpoint` 自测。小结和自测放在知识卡片外，不归入最后一个知识点；卡片内确需自测时可另放，不重复同一道题。
- 章末词汇表单独使用 `.note-section`，作为最后一个内容区。列保持 English term、中文对应词、English definition、中文释义。表格外包 `.table-scroll`，窄屏只让表格内部滚动。
- 笔记创作的内部源稿只输出正文片段，网页样式由 `templates/notes.css` 提供，不写内联样式、完整文档或脚本。最终按 `output-modes.md` 的已选模式交付纯笔记PDF、完整HTML或两者；PDF保留相同层次并适配分页。知识覆盖和讲解深度默认按 `note-depth.md`，用户当次指定范围与深度优先；测验难度沿用任务要求。

## HTML 示例

以下是结构示例；真实输出须按课件补全讲解、小结、自测和词汇表，不照抄示例内容或页码。

```html
<div class="chapter-overview">
  <div class="note-label">本章概览 / Chapter overview</div>
  <div class="bilingual-pair">
    <p lang="zh-CN">先理解抗原识别，再区分诱导应答与结合抗体这两种能力。</p>
    <p lang="en">First understand antigen recognition, then distinguish inducing a response from binding an antibody.</p>
  </div>
</div>
<section class="note-section">
  <header class="section-heading">
    <span class="section-number">01</span>
    <h2>抗原的基本性质 / Basic properties of antigens <span data-slides="10"></span></h2>
  </header>
  <article class="kc-card">
    <header class="kc-header">
      <div class="kc-index">知识点 01.1 / Knowledge point</div>
      <h3>免疫原性与免疫反应性 / Immunogenicity and immunoreactivity <span class="tag-must">必考</span><span data-slides="10"></span></h3>
    </header>
    <div class="kc-content">
      <div class="note-block">
        <div class="note-label">先想一想 / Start here</div>
        <div class="bilingual-pair">
          <p lang="zh-CN">能结合抗体的分子，一定能单独诱导抗体产生吗？</p>
          <p lang="en">Can every molecule that binds an antibody induce antibody production on its own?</p>
        </div>
      </div>
      <div class="tldr">
        <div class="note-label">核心结论 / Key takeaway</div>
        <div class="bilingual-pair">
          <p lang="zh-CN"><span class="kp">免疫原性指诱导应答；免疫反应性指特异性结合。</span></p>
          <p lang="en"><span class="kp">Immunogenicity means inducing a response; immunoreactivity means specific binding.</span></p>
        </div>
      </div>
      <!-- 为什么重要、概念与定义、应用与步骤分别使用 note-block + note-label + bilingual-pair。 -->
      <blockquote class="pitfall">
        <div class="note-label">易错提醒 / Common mistake</div>
        <div class="bilingual-pair">
          <p lang="zh-CN">能结合抗体，不代表能单独诱导抗体产生。</p>
          <p lang="en">Binding an antibody does not imply inducing antibody production on its own.</p>
        </div>
      </blockquote>
    </div>
  </article>
  <!-- 本大节小结和带折叠答案的 checkpoint 在 article 外。 -->
</section>
<!-- 最后一个 note-section 为英文词汇表，table 外包 div.table-scroll。 -->
```

## 交付检查

检查目录的大节归属、知识卡边界、环节小标题、相邻中英内容是否一致、例子/易错/自测是否可辨认，以及词汇表是否独立并位于最后。旧版平铺笔记的 H2/H3 和相邻双语段落会由引擎补上卡片与配对容器；新笔记应直接遵循本格式。
