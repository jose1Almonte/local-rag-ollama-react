import io
import re
from PyPDF2 import PdfReader
import docx


def _is_toc_page(text: str) -> bool:
    """Detect if a page is a table of contents / index page.
    TOC pages have many lines ending with dotted leaders followed by page numbers."""
    lines = text.strip().split("\n")
    if len(lines) < 3:
        return False
    toc_lines = 0
    for line in lines:
        if re.search(r'\.\s*\d+\s*$', line.strip()):
            toc_lines += 1
    return toc_lines / len(lines) > 0.3


def extract_text_from_pdf_bytes(b: bytes) -> str:
    reader = PdfReader(io.BytesIO(b))
    texts = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if not _is_toc_page(text):
            texts.append(text)
    return "\n".join(texts)

def extract_text_from_docx_bytes(b: bytes) -> str:
    f = io.BytesIO(b)
    doc = docx.Document(f)
    paragraphs = [p.text for p in doc.paragraphs if p.text]
    return "\n".join(paragraphs)

def extract_text_from_txt_bytes(b: bytes, encoding='utf-8') -> str:
    return b.decode(encoding, errors='ignore')
