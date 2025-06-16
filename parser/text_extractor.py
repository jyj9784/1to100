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


def extract_question_images(pdf_path: str, out_dir: str):
    """문항 번호 기준으로 영역을 잘라 이미지로 저장한다."""
    import os
    import re

    os.makedirs(out_dir, exist_ok=True)

    pattern = re.compile(r"^(?:\(\d+\)|\d+\s*[.)])")

    results = []

    with fitz.open(pdf_path) as doc:
        q_index = 1
        for page_number, page in enumerate(doc, start=1):
            page_dict = page.get_text("dict")
            region = None

            for block in page_dict.get("blocks", []):
                if block.get("type") != 0:
                    continue

                text = "".join(
                    span["text"]
                    for line in block.get("lines", [])
                    for span in line.get("spans", [])
                ).strip()

                if not text:
                    continue

                if pattern.match(text):
                    if region:
                        pix = page.get_pixmap(clip=fitz.Rect(*region))
                        file_path = os.path.join(out_dir, f"question_{q_index}.png")
                        pix.save(file_path)
                        text_region = page.get_text("text", clip=fitz.Rect(*region))
                        results.append({
                            "index": q_index,
                            "page": page_number,
                            "bbox": region,
                            "text": text_region.strip(),
                            "path": file_path,
                        })
                        q_index += 1
                    region = list(block["bbox"])
                elif region:
                    b = block["bbox"]
                    region[0] = min(region[0], b[0])
                    region[1] = min(region[1], b[1])
                    region[2] = max(region[2], b[2])
                    region[3] = max(region[3], b[3])

            if region:
                pix = page.get_pixmap(clip=fitz.Rect(*region))
                file_path = os.path.join(out_dir, f"question_{q_index}.png")
                pix.save(file_path)
                text_region = page.get_text("text", clip=fitz.Rect(*region))
                results.append({
                    "index": q_index,
                    "page": page_number,
                    "bbox": region,
                    "text": text_region.strip(),
                    "path": file_path,
                })
                q_index += 1

    return results
