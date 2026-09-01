import fitz


def load_pdf_pages(file_path: str) -> list[dict]:
    pdf_document = fitz.open(file_path)

    pages = []

    for page_index, page in enumerate(pdf_document):
        text = page.get_text()

        if text.strip():
            pages.append(
                {
                    "page_number": page_index + 1,
                    "text": text,
                }
            )

    pdf_document.close()

    return pages
def load_single_pdf_page(
    file_path: str,
    page_number: int,
) -> str:
    pdf_document = fitz.open(file_path)

    page_index = page_number - 1

    if page_index < 0 or page_index >= len(pdf_document):
        pdf_document.close()
        return ""

    page = pdf_document[page_index]
    text = page.get_text()

    pdf_document.close()

    return text