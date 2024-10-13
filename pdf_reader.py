import PyPDF2


def parse_pdf(pdf_path: str) -> str:
    result = []
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page_number, page in enumerate(pdf_reader.pages):
            page_content = []
            text = page.extract_text()
            if text:
                page_content.append({"type": "text", "text": text})
            result.append({"page": page_number + 1, "content": page_content})
    return result
