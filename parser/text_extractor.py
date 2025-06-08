import fitz  # PyMuPDF


def extract_text_and_images(pdf_path: str):
    """PDF에서 텍스트와 이미지 좌표를 추출한다."""
    extracted_text = ""
    images = []

    with fitz.open(pdf_path) as doc:
        for page_number, page in enumerate(doc, start=1):
            width, height = page.rect.width, page.rect.height
            top_margin = 60
            bottom_margin = 70

            # 좌우 분할하여 텍스트 추출
            left_rect = fitz.Rect(0, top_margin, width / 2, height - bottom_margin)
            right_rect = fitz.Rect(width / 2, top_margin, width, height - bottom_margin)

            left = page.get_text("text", clip=left_rect)
            right = page.get_text("text", clip=right_rect)

            extracted_text += (left or "") + "\n\n" + (right or "") + "\n\n"

            # 이미지 좌표 기록
            page_dict = page.get_text("dict")
            for block in page_dict.get("blocks", []):
                if block.get("type") == 1:  # image block
                    images.append({
                        "page": page_number,
                        "bbox": block["bbox"],
                    })

    return extracted_text, images


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


def extract_question_images(pdf_path: str, dpi: int = 200):
    """문제 번호를 감지해 각 구간을 이미지로 추출한다."""
    from parser.structured_parser import is_question_start
    import base64

    results = []

    with fitz.open(pdf_path) as doc:
        for page_number, page in enumerate(doc, start=1):
            page_dict = page.get_text("dict")
            spans = []
            for block in page_dict.get("blocks", []):
                if block.get("type") == 0:
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            spans.append(span)

            question_indices = []
            for span in spans:
                text = span.get("text", "").strip()
                if is_question_start(text):
                    question_indices.append((span["bbox"], text))

            if not question_indices:
                pix = page.get_pixmap(dpi=dpi)
                img_b64 = base64.b64encode(pix.tobytes()).decode()
                results.append({"page": page_number, "image": img_b64})
                continue

            # 각 문제 영역 잘라내기
            for idx, (bbox, label) in enumerate(question_indices):
                y0 = bbox[1]
                y1 = (
                    question_indices[idx + 1][0][1]
                    if idx + 1 < len(question_indices)
                    else page.rect.height
                )
                rect = fitz.Rect(0, y0, page.rect.width, y1)
                pix = page.get_pixmap(clip=rect, dpi=dpi)
                img_b64 = base64.b64encode(pix.tobytes()).decode()
                results.append({"page": page_number, "label": label, "image": img_b64})

    return results
