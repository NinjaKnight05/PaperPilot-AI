from pypdf import PdfReader
from langchain_core.documents import Document

def extract_text_from_pdf(file_path):
    reader  = PdfReader(file_path)
    documents = []
    for page_number, page in enumerate(reader.pages,start=1):
        text = page.extract_text() or ""

        documents.append(
            Document(
                page_content=text,
                metadata={
                   "page_number":page_number,
                   "source":str(file_path)
                }
            )
        )
    return documents