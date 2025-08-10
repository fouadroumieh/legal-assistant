
import io
import zipfile
import xml.etree.ElementTree as ET
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# Optional parsers (graceful if not present)
try:
    from pypdf import PdfReader
    logger.info("pypdf module loaded successfully")
except Exception as e:
    PdfReader = None
    logger.warning("Failed to load pypdf: %s", e)

try:
    import docx  # python-docx
    logger.info("docx module loaded successfully")
except Exception as e:
    docx = None
    logger.warning("Failed to load docx: %s", e)

def normalize_ext(key: str) -> str:
    dot = key.rfind(".")
    return key[dot + 1:].lower() if dot != -1 else ""

def _extract_text_pdf(data: bytes) -> Tuple[str, int]:
    if PdfReader is None:
        logger.warning("PdfReader not available; skipping PDF text")
        return "", 0
    pdf = PdfReader(io.BytesIO(data))
    pages = len(pdf.pages)
    out = []
    for i in range(pages):
        try:
            out.append(pdf.pages[i].extract_text() or "")
        except Exception as e:
            logger.warning("Failed to extract text from page %d: %s", i, e)
            out.append("")
    text = "\n".join(out).strip()
    logger.info("Extracted PDF text length: %d", len(text))
    return text, pages

def _extract_text_docx_stdlib(data: bytes) -> Tuple[str, int]:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            with z.open("word/document.xml") as f:
                xml = f.read()
        root = ET.fromstring(xml)
        texts = []
        for node in root.iter():
            tag = node.tag.split("}")[-1]
            if tag == "t":
                if node.text:
                    texts.append(node.text)
            elif tag == "br":
                texts.append("\n")
            elif tag == "p":
                texts.append("\n")
        text = "".join(texts)
        lines = [ln.strip() for ln in text.splitlines()]
        text = "\n".join([ln for ln in lines if ln])
        pages = max(1, text.count("\n") // 40)
        logger.info("Extracted DOCX(stdlib) text length: %d", len(text))
        return text, pages
    except Exception as e:
        logger.warning("DOCX stdlib parse failed: %s", e)
        return "", 0

def _extract_text_docx(data: bytes) -> Tuple[str, int]:
    if docx is not None:
        try:
            document = docx.Document(io.BytesIO(data))
            paras = [p.text for p in document.paragraphs if p.text]
            text = "\n".join(paras).strip()
            page_count = max(1, len(paras) // 40)
            logger.info("Extracted DOCX(python-docx) text length: %d", len(text))
            return text, page_count
        except Exception as e:
            logger.warning("python-docx failed, falling back to stdlib: %s", e)
    return _extract_text_docx_stdlib(data)

def _extract_text_plain(data: bytes) -> Tuple[str, int]:
    try:
        text = data.decode("utf-8", errors="ignore")
        page_count = max(1, text.count("\n") // 40)
    except Exception:
        text = ""
        page_count = 0
    return text, page_count

def extract_text(data: bytes, ext: str) -> Tuple[str, int]:
    if ext == "pdf":
        return _extract_text_pdf(data)
    elif ext in ("docx", "doc"):
        return _extract_text_docx(data)
    else:
        return _extract_text_plain(data)
