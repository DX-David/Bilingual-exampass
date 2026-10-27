"""Prepare prompts and assemble markdown for final exam generation."""


def build_exam_prompt(
    all_content: str,
    difficulty: str,
    duration_minutes: int,
    question_distribution: dict,
    web_reference: str = "",
) -> str:
    """
    Build the prompt for Claude to generate a comprehensive final exam.
    """
    dist_str = "\n".join([f"- {k}: {v}%" for k, v in question_distribution.items()])

    # Estimate question count based on duration
    total_q = int(duration_minutes * 0.35)  # ~0.35 questions per minute

    prompt = f"""你是一位大学课程教授，需要为你的课程设计一份**期末考试试卷**。

## 考试参数

| 参数 | 值 |
|------|-----|
| 难度 | {difficulty} |
| 时长 | {duration_minutes} 分钟 |
| 总分 | 100 分 |
| 题型分布 | {dist_str} |
| 预估题量 | 约 {total_q} 题 |

## 出题原则

1. **全面覆盖**：覆盖所有章节，重点章节权重更高
2. **难度匹配**：与设定难度一致，{difficulty}难度应有对应的思维深度
3. **题型丰富**：选择题考察概念辨析，填空题考察关键记忆，简答题考察解题能力，综合题考察知识串联
4. **独立性**：各题之间不相互暗示答案
5. **规范性**：题干表述清晰完整，无歧义
6. **区分度**：有送分题（基础），也有拉分题（综合/拔高）

## 选择题质量要求

- 4 个选项必须都具体、有迷惑性，不能只写单个术语；每个选项应包含条件、原因、结论、步骤或应用场景
- 干扰项要来自真实错误理解：概念混淆、条件缺失、因果倒置、公式/步骤少一环、结论正确但不回答题干、适用场景错配
- 禁止「以上都对/以上都错」、明显荒谬选项、靠字面关键词就能秒选的选项
- 正确答案在 A/B/C/D 间随机且尽量均匀分布；选择题较多时，各字母作为正确答案的次数差不超过 1
- 不要连续多题使用同一个正确选项，输出前必须自查答案分布

## 试卷结构

### 一、选择题（共 X 分，每题 Y 分）
### 二、填空题（共 X 分，每空 Y 分）
### 三、简答题（共 X 分，每题 Y 分）
### 四、综合题（共 X 分，每题 Y 分）

## 输出格式

### 先输出试卷（用 `## 试卷` 标记开始），包含：
- 试卷标题
- 考试说明（时长、总分、注意事项）
- 各大题的分值和题量说明
- 每道题的分值标注
- 留出作答空间提示

### 再输出答案（用 `## 答案与评分标准` 标记开始），包含：
- 每道题的**正确答案**
- 选择题给出**解析**（为什么选这个）
- 简答/综合题给出**详细解题步骤**
- **评分要点**和**满分标准**
- **常见错误分析**

---

## 课程全部章节内容

{all_content}
"""

    if web_reference:
        prompt += f"""

---

## 参考信息（来自网络调研）

{web_reference}

请参考以上真实考题的风格和难度设计，但不要照搬。
"""

    prompt += """

---

请严格按照以上要求，先输出"## 试卷"，再输出"## 答案与评分标准"。
"""
    return prompt


def split_exam_and_answer(full_output: str) -> tuple:
    """Split combined output into (exam_only, answer_only)."""
    if "## 答案与评分标准" in full_output:
        parts = full_output.split("## 答案与评分标准", 1)
        exam = parts[0].strip()
        answers = "## 答案与评分标准\n" + parts[1].strip()
        return exam, answers
    elif "## 答案" in full_output:
        parts = full_output.split("## 答案", 1)
        exam = parts[0].strip()
        answers = "## 答案\n" + parts[1].strip()
        return exam, answers
    else:
        return full_output, ""


def build_exam_markdown(exam_content: str, course_name: str, duration: int) -> str:
    """Wrap exam content into a standalone exam markdown."""
    return f"""---
title: "{course_name} - 期末考试"
lang: zh-CN
---

# {course_name}

## 期末考试

> 考试时长：{duration} 分钟 | 满分：100 分 | 请独立完成

{exam_content}
"""


def build_exam_answer_markdown(answers: str, course_name: str) -> str:
    """Wrap answers into a standalone answer markdown."""
    return f"""---
title: "{course_name} - 期末考试答案与评分标准"
lang: zh-CN
---

# {course_name}

## 期末考试 · 答案与评分标准

{answers}
"""
