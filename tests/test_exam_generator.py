"""Tests for exam_generator.py."""

import pytest
from exam_generator import (
    build_exam_prompt,
    split_exam_and_answer,
    build_exam_markdown,
    build_exam_answer_markdown,
)


class TestBuildExamPrompt:
    def test_basic(self):
        content = "# 课程内容\n所有章节摘要"
        prompt = build_exam_prompt(
            content,
            difficulty="中等",
            duration_minutes=120,
            question_distribution={"选择题": 30, "填空题": 20, "简答题": 30, "综合题": 20},
        )
        assert "中等" in prompt
        assert "120" in prompt
        assert "选择题" in prompt
        assert content in prompt

    def test_with_web_reference(self):
        prompt = build_exam_prompt(
            "content",
            difficulty="困难",
            duration_minutes=90,
            question_distribution={"选择题": 50, "简答题": 50},
            web_reference="985高校类似试卷：题型以综合题为主",
        )
        assert "网络调研" in prompt
        assert "985" in prompt

    def test_different_difficulties(self):
        for diff in ["简单", "中等", "困难"]:
            prompt = build_exam_prompt(
                "test", diff, 90, {"选择题": 100}
            )
            assert diff in prompt

    def test_custom_distribution(self):
        prompt = build_exam_prompt(
            "test", "简单", 60,
            {"选择题": 40, "填空题": 30, "简答题": 30}
        )
        assert "40" in prompt
        assert "30" in prompt

    def test_choice_quality_and_answer_distribution(self):
        prompt = build_exam_prompt(
            "test", "中等", 90, {"选择题": 100}
        )
        assert "选择题质量要求" in prompt
        assert "概念混淆" in prompt
        assert "正确答案在 A/B/C/D 间随机" in prompt
        assert "次数差不超过 1" in prompt


class TestSplitExamAndAnswer:
    def test_standard_split(self):
        full = "## 试卷\n\n一、选择题\n内容\n\n## 答案与评分标准\n\n一、\nA\n解析"
        exam, ans = split_exam_and_answer(full)
        assert "## 试卷" in exam
        assert "## 答案与评分标准" in ans
        assert "选择题" in exam
        assert "A" in ans

    def test_alternate_marker(self):
        full = "## 试卷\nExam\n\n## 答案\nAnswers"
        exam, ans = split_exam_and_answer(full)
        assert "Exam" in exam
        assert "Answers" in ans

    def test_no_answer_section(self):
        full = "## 试卷\nJust the exam"
        exam, ans = split_exam_and_answer(full)
        assert exam == full
        assert ans == ""

    def test_empty(self):
        e, a = split_exam_and_answer("")
        assert e == ""
        assert a == ""


class TestBuildExamMarkdown:
    def test_exam_markdown(self):
        md = build_exam_markdown("## 试卷\n考试内容", "机器学习", 120)
        assert "机器学习" in md
        assert "期末考试" in md
        assert "120" in md
        assert "考试内容" in md

    def test_answer_markdown(self):
        md = build_exam_answer_markdown("## 答案\n解析内容", "机器学习")
        assert "机器学习" in md
        assert "答案与评分标准" in md
        assert "解析内容" in md
