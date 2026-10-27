"""Tests for knowledge_analyzer.py."""

import pytest
from knowledge_analyzer import build_knowledge_prompt, build_knowledge_markdown


class TestBuildKnowledgePrompt:
    def test_basic_prompt(self):
        text = "## 第一章\n这是测试内容。\n重点概念：机器学习"
        prompt = build_knowledge_prompt(text)
        assert "课程辅导专家" in prompt or "复习" in prompt
        assert text in prompt

    def test_default_mode_is_deep_learning(self):
        prompt = build_knowledge_prompt("content")
        assert "深度学习（默认主模式）" in prompt
        assert "读者读一遍就能理解" in prompt
        assert "一步一步推导或拆流程" in prompt

    def test_exam_mode_can_be_requested(self):
        prompt = build_knowledge_prompt("content", mode="考试")
        assert "当前模式：考试" in prompt

    def test_with_images(self):
        text = "Test content"
        images = ["/tmp/img1.png", "/tmp/img2.png"]
        prompt = build_knowledge_prompt(text, images)
        assert "2 张图片" in prompt

    def test_empty_text(self):
        prompt = build_knowledge_prompt("")
        assert len(prompt) > 0

    def test_long_text(self):
        text = "A" * 10000
        prompt = build_knowledge_prompt(text)
        assert len(prompt) > 10000
        assert text in prompt


class TestBuildKnowledgeMarkdown:
    def test_basic(self):
        analysis = "## 核心知识点\n1. 定义1\n2. 定理1"
        md = build_knowledge_markdown(analysis, "第一章 机器学习基础")
        assert "第一章 机器学习基础" in md
        assert "期末复习知识清单" in md
        assert "核心知识点" in md

    def test_chinese_title(self):
        md = build_knowledge_markdown("content", "深度学习")
        assert "深度学习" in md

    def test_empty_analysis(self):
        md = build_knowledge_markdown("", "Test")
        assert "Test" in md
        assert len(md) > 0
