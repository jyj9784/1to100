import pdfplumber

def extract_text_from_pdf(pdf_path: str) -> str:
    extracted_text = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # 페이지 크기 가져오기
            width = page.width
            height = page.height

            # 왼쪽 영역 crop
            left_bbox = (0, 0, width / 2, height)
            left = page.crop(left_bbox).extract_text()

            # 오른쪽 영역 crop
            right_bbox = (width / 2, 0, width, height)
            right = page.crop(right_bbox).extract_text()

            # 왼쪽 → 오른쪽 순으로 붙이기
            extracted_text += (left or "") + "\n\n" + (right or "") + "\n\n"

    return extracted_text
