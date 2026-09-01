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