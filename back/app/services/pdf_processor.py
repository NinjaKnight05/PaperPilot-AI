import re
import fitz  
from langchain_core.documents import Document
from .ocr import ocr_page


def clean_text(text: str) -> str:
    # Remove null bytes and control characters that break JSON encoding
    text = text.replace("\x00", "")
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    text = text.encode("utf-8", errors="ignore").decode("utf-8")
    return text


def normalize_text(text: str) -> str:

    text = re.sub(r"-\n(\w)", r"\1", text)
    text = re.sub(r"\n+", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def needs_ocr(text: str, min_chars: int = 20) -> bool:
    return len(text.strip()) < min_chars


# Matches a line that contains only "References" / "Bibliography"
# (optionally numbered, like "7. References")
REFERENCES_HEADING = re.compile(
    r"^\s*(?:\d+\.?\s*)?(references|bibliography)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    total_pages = len(doc)
    documents = []

    for page_number, page in enumerate(doc, start=1):
        text = page.get_text()
        text = clean_text(text)

        if page_number > total_pages * 0.7:
            match = REFERENCES_HEADING.search(text)
            if match:
                before = normalize_text(text[:match.start()])
                if before:
                    documents.append(
                        Document(
                            page_content=before,
                            metadata={
                                "page_number": page_number,
                                "source": str(file_path),
                                "used_ocr": False
                            }
                        )
                    )
                break

        text = normalize_text(text)

        if needs_ocr(text):
            ocr_text = ocr_page(page)
            ocr_text = clean_text(ocr_text)
            ocr_text = normalize_text(ocr_text)
            text = ocr_text
            used_ocr = True
        else:
            used_ocr = False

        documents.append(
            Document(
                page_content=text,
                metadata={
                    "page_number": page_number,
                    "source": str(file_path),
                    "used_ocr": used_ocr
                }
            )
        )

    doc.close()
    return documents