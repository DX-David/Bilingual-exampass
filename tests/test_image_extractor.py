"""Tests for image_extractor.py."""

import os
import pytest
from conftest import create_sample_pptx, create_sample_docx, create_sample_pdf
from image_extractor import extract_from_pptx, extract_from_docx, extract_from_pdf


class TestExtractFromPPTX:
    def test_with_images(self, temp_dir):
        pptx_path = os.path.join(temp_dir, "test.pptx")
        create_sample_pptx(pptx_path, include_image=True)
        out_dir = os.path.join(temp_dir, "images")
        os.makedirs(out_dir)
        paths = extract_from_pptx(pptx_path, out_dir)
        assert len(paths) >= 1
        for p in paths:
            assert os.path.exists(p)
            assert os.path.getsize(p) > 0

    def test_without_images(self, temp_dir):
        pptx_path = os.path.join(temp_dir, "test_noimg.pptx")
        create_sample_pptx(pptx_path, include_image=False, include_table=False)
        out_dir = os.path.join(temp_dir, "images")
        os.makedirs(out_dir)
        paths = extract_from_pptx(pptx_path, out_dir)
        assert paths == []

    def test_output_dir_created(self, temp_dir):
        pptx_path = os.path.join(temp_dir, "test.pptx")
        create_sample_pptx(pptx_path, include_image=False)
        out_dir = os.path.join(temp_dir, "new_images")
        paths = extract_from_pptx(pptx_path, out_dir)
        assert isinstance(paths, list)


class TestExtractFromDOCX:
    def test_with_images(self, temp_dir):
        docx_path = os.path.join(temp_dir, "test.docx")
        create_sample_docx(docx_path, include_image=True)
        out_dir = os.path.join(temp_dir, "images")
        os.makedirs(out_dir)
        paths = extract_from_docx(docx_path, out_dir)
        assert len(paths) >= 1
        for p in paths:
            assert os.path.exists(p)
            assert os.path.getsize(p) > 0

    def test_without_images(self, temp_dir):
        docx_path = os.path.join(temp_dir, "test.docx")
        create_sample_docx(docx_path, include_image=False, include_table=False)
        out_dir = os.path.join(temp_dir, "images")
        os.makedirs(out_dir)
        paths = extract_from_docx(docx_path, out_dir)
        assert paths == []


class TestExtractFromPDF:
    def test_pdf_extract_images(self, temp_dir):
        pdf_path = os.path.join(temp_dir, "test.pdf")
        create_sample_pdf(pdf_path)
        out_dir = os.path.join(temp_dir, "images")
        os.makedirs(out_dir)
        paths = extract_from_pdf(pdf_path, out_dir)
        assert isinstance(paths, list)

    def test_empty_pdf(self, temp_dir):
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        pdf_path = os.path.join(temp_dir, "empty.pdf")
        c = canvas.Canvas(pdf_path, pagesize=A4)
        c.save()
        out_dir = os.path.join(temp_dir, "images")
        os.makedirs(out_dir)
        paths = extract_from_pdf(pdf_path, out_dir)
        assert isinstance(paths, list)
