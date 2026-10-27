"""Extract content from PDF files."""

import os
from typing import Dict, Any, List


def extract_pdf(filepath: str) -> Dict[str, Any]:
    """
    Extract text and tables from a PDF file.
    Returns: {
        'pages': [{'number': int, 'text': str, 'tables': [...]}],
        'total_pages': int,
        'filename': str
    }
    """
    import pdfplumber

    pages = []
    with pdfplumber.open(filepath) as pdf:
        for page_idx, page in enumerate(pdf.pages, start=1):
            page_data = {
                'number': page_idx,
                'text': '',
                'tables': [],
            }

            text = page.extract_text()
            if text:
                page_data['text'] = text.strip()

            tables = page.extract_tables()
            for table in tables:
                if table:
                    cleaned = []
                    for row in table:
                        cleaned.append([cell or '' for cell in row])
                    page_data['tables'].append(cleaned)

            pages.append(page_data)

    return {
        'pages': pages,
        'total_pages': len(pages),
        'filename': os.path.basename(filepath),
    }


def build_text_summary(data: Dict[str, Any]) -> str:
    """Build a readable text summary from extracted PDF data."""
    lines = [f"# {data['filename']}", f"共 {data['total_pages']} 页\n"]

    for page in data['pages']:
        lines.append(f"\n## 第 {page['number']} 页")
        if page['text']:
            lines.append(page['text'])
        for i, table in enumerate(page.get('tables', [])):
            if not table:
                continue
            lines.append(f"\n### 表格 {i+1}")
            if table[0]:
                lines.append("\n| " + " | ".join(table[0]) + " |")
                lines.append("|" + "|".join(["---"] * len(table[0])) + "|")
            for row in table[1:]:
                cols = len(table[0]) if table else len(row)
                padded = row + [''] * (cols - len(row))
                lines.append("| " + " | ".join(padded[:cols]) + " |")

    return '\n'.join(lines)
