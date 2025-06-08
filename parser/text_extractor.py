import fitz  # PyMuPDF


def extract_text_from_pdf(pdf_path: str) -> str:
    """PDF에서 텍스트만 추출한다."""
    extracted_text = ""

    with fitz.open(pdf_path) as doc:
        for page in doc:
            width, height = page.rect.width, page.rect.height
            top_margin = 60
            bottom_margin = 70

            # 왼쪽/오른쪽 텍스트 영역 크롭 (헤더/푸터 제거)
            left_rect = fitz.Rect(0, top_margin, width / 2, height - bottom_margin)
            right_rect = fitz.Rect(width / 2, top_margin, width, height - bottom_margin)

            left = page.get_text("text", clip=left_rect)
            right = page.get_text("text", clip=right_rect)

            extracted_text += (left or "") + "\n\n" + (right or "") + "\n\n"

    return extracted_text
