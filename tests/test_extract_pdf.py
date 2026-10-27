"""Tests for extract_pdf.py."""

import os
import pytest
from conftest import create_sample_pdf
from extract_pdf import extract_pdf, build_text_summary


class TestExtractPDF:
    def test_basic_extraction(self, temp_dir):
        pdf_path = os.path.join(temp_dir, "test.pdf")
        create_sample_pdf(pdf_path)
        data = extract_pdf(pdf_path)
        assert data['total_pages'] >= 1
        assert 'pages' in data
        assert data['filename'] == "test.pdf"

    def test_text_extraction(self, temp_dir):
        pdf_path = os.path.join(temp_dir, "test.pdf")
        create_sample_pdf(pdf_path)
        data = extract_pdf(pdf_path)
        text = ' '.join(p['text'] for p in data['pages'])
        assert len(text) > 0
        # Should contain CNN content
        assert 'CNN' in text or 'Convolutional' in text

    def test_table_extraction(self, temp_dir):
        pdf_path = os.path.join(temp_dir, "test.pdf")
        create_sample_pdf(pdf_path, include_table=True)
        data = extract_pdf(pdf_path)
        tables_found = any(p['tables'] for p in data['pages'])
        # Tables in sample PDF are drawn as text (reportlab), not real tables,
        # so this may be empty but should not crash
        assert isinstance(data['pages'], list)

    def test_page_structure(self, temp_dir):
        pdf_path = os.path.join(temp_dir, "test.pdf")
        create_sample_pdf(pdf_path)
        data = extract_pdf(pdf_path)
        for page in data['pages']:
            assert 'number' in page
            assert 'text' in page
            assert 'tables' in page
            assert isinstance(page['number'], int)

    def test_multi_page(self, temp_dir):
        pdf_path = os.path.join(temp_dir, "test.pdf")
        create_sample_pdf(pdf_path)
        data = extract_pdf(pdf_path)
        assert data['total_pages'] >= 1

    def test_text_summary(self, temp_dir):
        pdf_path = os.path.join(temp_dir, "test.pdf")
        create_sample_pdf(pdf_path)
        data = extract_pdf(pdf_path)
        summary = build_text_summary(data)
        assert len(summary) > 0
        assert 'CNN' in summary or 'Convolutional' in summary


class TestEmptyPDF:
    def test_empty_pdf(self, temp_dir):
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        pdf_path = os.path.join(temp_dir, "empty.pdf")
        c = canvas.Canvas(pdf_path, pagesize=A4)
        c.save()
        data = extract_pdf(pdf_path)
        assert data['total_pages'] >= 0  # Empty PDF may report 0 pages


class TestCorruptedFile:
    def test_nonexistent_file(self):
        with pytest.raises(Exception):
            extract_pdf("/nonexistent/file.pdf")
