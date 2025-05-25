import pdfplumber


def extract_text_from_pdf(pdf_path: str) -> str:
    extracted_text = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            width, height = page.width, page.height
            top_margin = 60
            bottom_margin = 70

            # 왼쪽/오른쪽 텍스트 영역 크롭 (헤더/푸터 제거)
            left_bbox = (0, top_margin, width / 2, height - bottom_margin)
            right_bbox = (width / 2, top_margin, width, height - bottom_margin)

            left = page.crop(left_bbox).extract_text()
            right = page.crop(right_bbox).extract_text()

            extracted_text += (left or "") + "\n\n" + (right or "") + "\n\n"

    return extracted_text
