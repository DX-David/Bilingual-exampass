"""Tests for extract_docx.py."""

import os
import pytest
from conftest import create_sample_docx
from extract_docx import extract_docx, build_text_summary


class TestExtractDOCX:
    def test_basic_extraction(self, temp_dir):
        docx_path = os.path.join(temp_dir, "test.docx")
        create_sample_docx(docx_path, include_image=False, include_table=False)
        data = extract_docx(docx_path)
        assert 'paragraphs' in data
        assert 'tables' in data
        assert 'sections' in data
        assert data['filename'] == "test.docx"

    def test_paragraph_extraction(self, temp_dir):
        docx_path = os.path.join(temp_dir, "test.docx")
        create_sample_docx(docx_path, include_image=False, include_table=False)
        data = extract_docx(docx_path)
        assert len(data['paragraphs']) > 0

    def test_heading_extraction(self, temp_dir):
        docx_path = os.path.join(temp_dir, "test.docx")
        create_sample_docx(docx_path)
        data = extract_docx(docx_path)
        headings = [s['heading'] for s in data['sections'] if s['heading']]
        assert len(headings) >= 2  # At least H1 and H2

    def test_table_extraction(self, temp_dir):
        docx_path = os.path.join(temp_dir, "test.docx")
        create_sample_docx(docx_path, include_image=False, include_table=True)
        data = extract_docx(docx_path)
        assert len(data['tables']) >= 1
        assert len(data['tables'][0]) >= 2  # At least header + 1 row

    def test_table_content(self, temp_dir):
        docx_path = os.path.join(temp_dir, "test.docx")
        create_sample_docx(docx_path, include_image=False, include_table=True)
        data = extract_docx(docx_path)
        first_table = data['tables'][0]
        assert first_table[0][0] == "激活函数"

    def test_with_image(self, temp_dir):
        docx_path = os.path.join(temp_dir, "test.docx")
        create_sample_docx(docx_path, include_image=True, include_table=False)
        data = extract_docx(docx_path)
        assert len(data['paragraphs']) > 0

    def test_text_summary(self, temp_dir):
        docx_path = os.path.join(temp_dir, "test.docx")
        create_sample_docx(docx_path)
        data = extract_docx(docx_path)
        summary = build_text_summary(data)
        assert len(summary) > 0
        assert "深度学习" in summary


class TestCorruptedFile:
    def test_nonexistent_file(self):
        with pytest.raises(Exception):
            extract_docx("/nonexistent/file.docx")
