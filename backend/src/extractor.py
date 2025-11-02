import io
from PyPDF2 import PdfReader
import docx

def extract_text_from_pdf_bytes(b: bytes) -> str:
    reader = PdfReader(io.BytesIO(b))
    texts = []
    for page in reader.pages:
        texts.append(page.extract_text() or "")
    return "\n".join(texts)

def extract_text_from_docx_bytes(b: bytes) -> str:
    f = io.BytesIO(b)
    doc = docx.Document(f)
    paragraphs = [p.text for p in doc.paragraphs if p.text]
    return "\n".join(paragraphs)

def extract_text_from_txt_bytes(b: bytes, encoding='utf-8') -> str:
    return b.decode(encoding, errors='ignore')
