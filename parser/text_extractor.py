import fitz  # PyMuPDF

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    PDF 파일에서 머리말/꼬리말을 제외한 본문 텍스트를 추출합니다.
    페이지의 상하단 일정 비율을 제외하여 머리말/꼬리말을 제거하고,
    2단 레이아웃을 고려하여 좌우 열의 텍스트를 순서대로 조합합니다.

    Args:
        pdf_path (str): 텍스트를 추출할 PDF 파일의 경로.

    Returns:
        str: 추출된 전체 텍스트.
    """
    extracted_text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            width, height = page.rect.width, page.rect.height
            top_margin = height * 0.08  # 상단 8% 제외
            bottom_margin = height * 0.92  # 하단 8% 제외

            # 좌우 영역 분할
            left_rect = fitz.Rect(0, top_margin, width / 2, bottom_margin)
            right_rect = fitz.Rect(width / 2, top_margin, width, bottom_margin)

            left_text = page.get_text("text", clip=left_rect).strip()
            right_text = page.get_text("text", clip=right_rect).strip()

            if left_text:
                extracted_text += left_text + "\n\n"
            if right_text:
                extracted_text += right_text + "\n\n"
    return extracted_text
