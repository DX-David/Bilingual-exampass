"""Prepare prompts and assemble markdown for knowledge list generation."""

DEFAULT_STUDY_MODE = "深度学习"


def _normalize_mode(mode: str = None) -> str:
    """Return the supported study mode name used in prompts."""
    if not mode:
        return DEFAULT_STUDY_MODE

    normalized = str(mode).strip().lower()
    aliases = {
        "exam": "考试",
        "考试": "考试",
        "test": "考试",
        "balanced": "平衡",
        "balance": "平衡",
        "平衡": "平衡",
        "normal": "平衡",
        "deep": "深度学习",
        "deep-learning": "深度学习",
        "deep_learning": "深度学习",
        "深度": "深度学习",
        "深度学习": "深度学习",
    }
    return aliases.get(normalized, DEFAULT_STUDY_MODE)


def build_knowledge_prompt(text_summary: str, images: list = None, mode: str = DEFAULT_STUDY_MODE) -> str:
    """
    Build the analysis prompt for Claude to generate a knowledge list.
    The caller (skill) sends this prompt to Claude and receives markdown.
    """
    mode = _normalize_mode(mode)
    mode_note = {
        "考试": "当前模式：考试。目标是快速复习，但仍要保留最小必要因果链，不写空泛口号。",
        "平衡": "当前模式：平衡。目标是复习效率和理解深度兼顾，每个概念讲清是什么、为什么、怎么用。",
        "深度学习": "当前模式：深度学习（默认主模式）。目标是把难点讲到读者读一遍就能理解、复述、做题。",
    }[mode]

    prompt = f"""你是一位资深的大学课程辅导专家。请根据以下课程资料，生成一份**期末考试复习知识清单**。

{mode_note}

## 主模式硬约束：深度学习式讲透

除非用户明确要求「考试」或「平衡」，默认采用**深度学习模式**。你的任务不是压缩资料，而是把资料中跳跃、隐含、难懂的部分重构成一条清晰教学链，让读者不查外部资料也能读懂。

遇到任何难点时，必须按下面的「一遍读懂」结构展开：
1. **先给直觉**：用生活类比或非常小的例子说明它在解决什么问题。
2. **再给正式定义**：给出准确概念、适用条件和边界。
3. **解释为什么需要它**：说明旧方法哪里不够、这个方法补了什么短板。
4. **一步一步推导或拆流程**：公式不能只摆结论，算法不能只列名字；每一步都解释「这一步在干什么」。
5. **给可执行例子**：至少给一个小规模例子、代入过程或典型题型。
6. **横向对比**：凡是容易混淆的概念，必须用表格比较「相同点、不同点、适用场景、考试陷阱」。
7. **易错辨析**：用引用块单独指出常见误解，并说明错在哪里。
8. **收束成记忆钩子**：每个核心小节结尾用 1-2 句话总结最该记住的判断标准。

## 输出要求

### 1. 核心知识点
- 提取所有**定义、定理、公式、关键概念**
- 每个核心概念都必须讲清**是什么、为什么、怎么用、容易错在哪里**
- 不允许只写「概念 + 一句话解释」；对难点要拆到初学者能顺着读下来
- 公式使用 LaTeX 语法（$...$ 行内，$$...$$ 独立行）

### 2. 重点解题方法
- 整理资料中出现的**解题步骤、技巧、常见陷阱**
- 每个方法附一个**可跟做示例**，展示输入条件、推理步骤和最终结论
- 标注方法适用的**题型类型**
- 如果资料包含算法、证明或计算，必须写出「从问题到方法」的推导路线

### 3. 考试高频考点
- 基于内容强调程度、重复频率、例题密度判断考点重要性
- 用标签标注重要程度：`<span class="tag-must">必考</span>`、`<span class="tag-key">重点</span>`、`<span class="tag-freq">高频</span>`、`<span class="tag-info">了解</span>`
- 给出每个考点的**典型出题形式**

### 4. 格式要求
- 使用 Markdown 层级标题（# ## ###）
- 表格用于对比类内容
- 使用 > 引用块标注特别重要的内容
- 每个一级标题下的内容要有清晰的逻辑顺序
- 核心定义、公式、判断标准可用 `<span class="kp">...</span>` 包裹；解释、类比、动机、例子可用 `<span class="exp">...</span>` 包裹
- 不要堆砌术语；每引入一个术语，都要马上解释它在当前问题链条里的作用

---

## 课程资料内容

"""
    prompt += text_summary

    if images:
        prompt += f"\n\n注意：本课程资料包含 {len(images)} 张图片（图表/示意图），请一并分析。\n"

    return prompt


def build_knowledge_markdown(analysis_result: str, title: str) -> str:
    """Wrap Claude's analysis result into a complete knowledge list markdown document."""
    return f"""---
title: "{title} - 期末复习知识清单"
lang: zh-CN
toc: true
toc-depth: 3
---

# {title}

## 期末复习知识清单

> 生成时间：自动生成 | 建议搭配章节测试题使用

{analysis_result}
"""
