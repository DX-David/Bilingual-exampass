"""
OCR / document-parsing backend for non-multimodal models.

When the running model cannot see images (Codex / OpenClaw / any text-only
LLM), call ocr_images() to turn extracted picture files into text so the
chart / formula / diagram content in slides is not lost.

Backend priority (first available wins):
  1. MinerU (magic-pdf)  -- best for academic PDFs: formulas, tables, charts
  2. PaddleOCR            -- strong general CN/EN OCR
  3. Tesseract (pytesseract) -- lightweight fallback

All backends are optional. If none is installed, ocr_images() returns an
empty string and prints an install hint -- the pipeline still runs, just
without image text.
"""

import os


def _try_mineru(image_paths):
    """MinerU / magic-pdf. Best quality for academic content."""
    try:
        from magic_pdf.data.data_reader_writer import FileBasedDataReader  # noqa
    except Exception:
        return None
    # MinerU works on full PDFs, not loose images. We expose a hook here;
    # callers that have the original PDF should prefer mineru_parse_pdf().
    return None


def mineru_parse_pdf(pdf_path, out_dir=None):
    """Parse a full PDF with MinerU, returning markdown text (formulas+tables).

    Returns '' if MinerU is not installed or parsing fails.
    """
    try:
        from magic_pdf.pipe.UNIPipe import UNIPipe
        from magic_pdf.data.data_reader_writer import DiskReaderWriter
    except Exception:
        return ''
    try:
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()
        out_dir = out_dir or os.path.join(os.path.dirname(pdf_path), '_mineru')
        os.makedirs(out_dir, exist_ok=True)
        writer = DiskReaderWriter(out_dir)
        pipe = UNIPipe(pdf_bytes, {"_pdf_type": "", "model_list": []}, writer)
        pipe.pipe_classify()
        pipe.pipe_analyze()
        pipe.pipe_parse()
        return pipe.pipe_mk_markdown(out_dir, drop_mode="none")
    except Exception as e:
        print("MinerU parse failed:", e)
        return ''


def _try_paddleocr(image_paths):
    try:
        from paddleocr import PaddleOCR
    except Exception:
        return None
    try:
        ocr = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)
        chunks = []
        for p in image_paths:
            res = ocr.ocr(p, cls=True)
            for line in (res[0] or []):
                chunks.append(line[1][0])
        return '\n'.join(chunks)
    except Exception as e:
        print("PaddleOCR failed:", e)
        return None


def _try_tesseract(image_paths):
    try:
        import pytesseract
        from PIL import Image
    except Exception:
        return None
    try:
        chunks = []
        for p in image_paths:
            chunks.append(pytesseract.image_to_string(Image.open(p), lang='chi_sim+eng'))
        return '\n'.join(chunks)
    except Exception as e:
        print("Tesseract failed:", e)
        return None


def ocr_images(image_paths):
    """Run the best available OCR backend on a list of image files.

    Returns extracted text (possibly empty string).
    """
    if not image_paths:
        return ''
    for backend in (_try_paddleocr, _try_tesseract):
        text = backend(image_paths)
        if text is not None:
            return text
    print(
        "No OCR backend installed. To extract image text on a non-multimodal "
        "model, install one of:\n"
        "  pip install magic-pdf      # MinerU, best for academic PDFs\n"
        "  pip install paddleocr      # general CN/EN OCR\n"
        "  pip install pytesseract    # lightweight (needs Tesseract binary)"
    )
    return ''


def is_multimodal_hint():
    """Heuristic: read EXAMPASS_MULTIMODAL env var. Default True (Claude).

    Set EXAMPASS_MULTIMODAL=0 on text-only platforms to force OCR.
    """
    return os.environ.get('EXAMPASS_MULTIMODAL', '1') not in ('0', 'false', 'False')
