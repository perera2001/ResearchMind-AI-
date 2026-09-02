import fitz
from langchain_core.documents import Document


def load_pdf_pages(
    file_path: str,
    metadata_file_path: str,
    user_id: int,
    document_id: int,
    file_name: str,
) -> list[Document]:
    pages = []

    with fitz.open(file_path) as pdf_document:
        for page_index, page in enumerate(pdf_document):
            text = page.get_text()

            pages.append(
                Document(
                    page_content=text,
                    metadata={
                        "user_id": user_id,
                        "document_id": document_id,
                        "source": file_name,
                        "file_path": metadata_file_path,
                        "page_number": page_index + 1,
                    },
                )
            )

    return pages


def load_single_pdf_page(
    file_path: str,
    page_number: int,
) -> str:
    with fitz.open(file_path) as pdf_document:
        page_index = page_number - 1

        if page_index < 0 or page_index >= len(pdf_document):
            return ""

        page = pdf_document[page_index]
        text = page.get_text()

    return text
