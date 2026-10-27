"""Integration tests — full pipeline from scan to PDF generation."""

import os
import pytest
from unittest.mock import patch, MagicMock
from conftest import create_sample_pptx, create_sample_docx, create_sample_pdf

from scanner import scan_and_group, get_group_name
from extractor import extract_file, merge_group_content
from knowledge_analyzer import build_knowledge_prompt, build_knowledge_markdown
from test_generator import build_test_prompt, split_test_and_answer
from html_generator import generate_html


class TestFullPipelineSingleFile:
    """Test the complete pipeline: scan → extract → analyze prompt → PDF."""

    def test_pptx_pipeline(self, temp_dir):
        # Setup
        pptx_path = os.path.join(temp_dir, "test.pptx")
        create_sample_pptx(pptx_path, include_image=True, include_table=True)
        images_dir = os.path.join(temp_dir, "images")
        os.makedirs(images_dir)

        # Scan
        groups = scan_and_group(temp_dir)
        assert len(groups) == 1
        group_name = get_group_name(temp_dir, temp_dir)

        # Extract
        result = extract_file(pptx_path, image_output_dir=images_dir)
        assert result['text_summary']

        # Build knowledge prompt
        prompt = build_knowledge_prompt(result['text_summary'], result['images'])
        assert len(prompt) > 0

        # Build knowledge markdown
        simulated_analysis = """## 核心知识点
1. **定义**：机器学习是通过数据学习模式的算法。
2. **分类**：监督学习、无监督学习、强化学习

## 重点解题方法
### 线性回归
- 步骤：计算损失函数 → 求梯度 → 更新参数
- 公式：$\\hat{y} = wx + b$

## 考试高频考点
| 考点 | 重要程度 | 出题形式 |
|------|---------|---------|
| 监督学习 | ⭐⭐⭐ | 选择+简答 |
| 损失函数 | ⭐⭐⭐ | 计算题 |
"""
        md = build_knowledge_markdown(simulated_analysis, group_name)
        assert group_name in md

        # Generate PDF
        output = os.path.join(temp_dir, f"{group_name}-知识清单.html")
        success = generate_html(md, output)
        assert success
        assert os.path.exists(output)
        assert os.path.getsize(output) > 0

    def test_pdf_pipeline(self, temp_dir):
        pdf_path = os.path.join(temp_dir, "test.pdf")
        create_sample_pdf(pdf_path)

        groups = scan_and_group(temp_dir)
        assert len(groups) == 1

        result = extract_file(pdf_path)
        assert 'CNN' in result['text_summary'] or 'Convolutional' in result['text_summary']

        prompt = build_knowledge_prompt(result['text_summary'])
        assert len(prompt) > 0


class TestFullPipelineMultipleFiles:
    """Test merging multiple file types into one knowledge list."""

    def test_merge_pptx_docx_pdf(self, temp_dir):
        # Create 3 files in one directory
        ch_dir = os.path.join(temp_dir, "第一章")
        os.makedirs(ch_dir)

        pptx_path = os.path.join(ch_dir, "slides.pptx")
        create_sample_pptx(pptx_path, include_image=False, include_table=False)

        docx_path = os.path.join(ch_dir, "reading.docx")
        create_sample_docx(docx_path, include_image=False, include_table=False)

        pdf_path = os.path.join(ch_dir, "handout.pdf")
        create_sample_pdf(pdf_path)

        # Scan
        groups = scan_and_group(temp_dir)
        assert ch_dir in groups
        assert len(groups[ch_dir]) == 3

        # Extract all
        results = [extract_file(f) for f in groups[ch_dir]]
        assert len(results) == 3

        # Merge
        merged = merge_group_content(results)
        assert len(merged) > max(len(r['text_summary']) for r in results)

        # Build prompt from merged
        group_name = get_group_name(ch_dir, temp_dir)
        prompt = build_knowledge_prompt(merged)
        assert len(prompt) > 0

        # Generate knowledge markdown
        md = build_knowledge_markdown("## test content\n分析结果", group_name)
        assert group_name in md

        # Generate PDF
        output = os.path.join(ch_dir, f"{group_name}-知识清单.html")
        success = generate_html(md, output)
        assert success
        assert os.path.exists(output)


class TestMultiChapterBatch:
    """Test processing multiple chapters in batch."""

    def test_two_chapters(self, temp_dir):
        for ch in ["第一章-绪论", "第二章-基础"]:
            ch_dir = os.path.join(temp_dir, ch)
            os.makedirs(ch_dir)
            pptx_path = os.path.join(ch_dir, "课件.pptx")
            create_sample_pptx(pptx_path, include_image=False, include_table=False)

        groups = scan_and_group(temp_dir)
        assert len(groups) == 2

        for folder, files in groups.items():
            assert len(files) == 1
            result = extract_file(files[0])
            assert result['text_summary']

            group_name = get_group_name(folder, temp_dir)
            md = build_knowledge_markdown("## Content\n知识要点", group_name)
            output = os.path.join(folder, f"{group_name}-知识清单.html")
            success = generate_html(md, output)
            assert success
            assert os.path.exists(output)


class TestTestGenerationPipeline:
    """Test the test generation part of the pipeline."""

    def test_generate_and_split_test(self, temp_dir):
        pptx_path = os.path.join(temp_dir, "test.pptx")
        create_sample_pptx(pptx_path)
        result = extract_file(pptx_path)

        # Build test prompt
        prompt = build_test_prompt(result['text_summary'], question_count=5)
        assert len(prompt) > 0

        # Simulate Claude output
        simulated_output = """## 题目

### 选择题
1. 监督学习的核心特征是什么？
   A. 使用无标签数据
   B. 使用带标签数据训练
   C. 不使用任何数据
   D. 只使用测试数据

### 填空题
2. 在线性回归中，均方误差的公式为 MSE = \\_\\_\\_\\_\\_\\_。

### 简答题
3. 请简述反向传播算法的基本步骤。

## 答案与解析

1. **B** — 监督学习使用带标签的数据进行训练，每个训练样本都有对应的标签。
   - A错：使用无标签数据是无监督学习
   - C错：所有机器学习都需要数据
   - D错：只使用测试数据无法训练模型

2. **(1/n)Σ(yᵢ - ŷᵢ)²** — 均方误差是回归问题最常用的损失函数之一。

3. **解题步骤**：
   (1) 前向传播计算预测值和损失
   (2) 从输出层开始，用链式法则计算每层梯度
   (3) 使用梯度下降更新权重
   (4) 重复直到收敛
   **评分要点**：提到链式法则得3分，提到梯度更新得2分，满分5分。
"""

        q, a = split_test_and_answer(simulated_output)
        assert "选择题" in q
        assert "答案与解析" in a
        assert "B" in a

        # Generate question PDF
        q_md = """---\ntitle: "第一章 - 章节测试"\nlang: zh-CN\n---\n\n""" + q
        q_pdf = os.path.join(temp_dir, "第一章-章节测试.html")
        assert generate_html(q_md, q_pdf)

        # Generate answer PDF
        a_md = """---\ntitle: "第一章 - 章节测试答案"\nlang: zh-CN\n---\n\n""" + a
        a_pdf = os.path.join(temp_dir, "第一章-章节测试-答案.html")
        assert generate_html(a_md, a_pdf)


class TestExamGenerationPipeline:
    """Test the final exam generation pipeline."""

    def test_exam_generation_flow(self, temp_dir):
        from exam_generator import build_exam_prompt, split_exam_and_answer, build_exam_markdown, build_exam_answer_markdown

        content = "# 全部课程内容\n\n## 第一章\n机器学习基础\n\n## 第二章\n深度学习\n\n## 第三章\nCNN架构"

        prompt = build_exam_prompt(
            content, "中等", 120,
            {"选择题": 30, "填空题": 20, "简答题": 30, "综合题": 20},
            web_reference="参考：某985高校类似课程期末考试，难度中等偏上，重点考察综合应用能力。"
        )
        assert "中等" in prompt
        assert "120" in prompt

        simulated_output = """## 试卷

# 机器学习 期末考试

**考试时间：120 分钟 | 满分：100 分**

### 一、选择题（共 30 分，每题 3 分）

1. 以下哪个不是监督学习算法？
   A. 线性回归  B. K-Means  C. SVM  D. 决策树

### 二、填空题（共 20 分，每空 2 分）

6. 卷积神经网络中，______层用于降低特征图的空间维度。

### 三、简答题（共 30 分，每题 10 分）

11. 请解释反向传播算法中梯度消失问题的原因及解决方案。

### 四、综合题（共 20 分）

14. 给定一个二分类问题，设计完整的机器学习流程。

## 答案与评分标准

1. **B** — K-Means 是无监督聚类算法。（3分）
6. **池化** — 池化层通过下采样降低特征图维度。（2分）
11. **参考答案**：梯度消失是因为深层网络中链式法则连乘导致梯度指数级衰减...
14. **评分标准**：数据预处理(4分)+特征工程(4分)+模型选择(4分)+训练调参(4分)+评估(4分)
"""

        exam, ans = split_exam_and_answer(simulated_output)
        assert "选择题" in exam
        assert "B" in ans

        exam_md = build_exam_markdown(exam, "机器学习", 120)
        assert "机器学习" in exam_md

        ans_md = build_exam_answer_markdown(ans, "机器学习")
        assert "机器学习" in ans_md

        exam_pdf = os.path.join(temp_dir, "期末考试-机器学习.html")
        assert generate_html(exam_md, exam_pdf)

        ans_pdf = os.path.join(temp_dir, "期末考试-机器学习-答案.html")
        assert generate_html(ans_md, ans_pdf)
