import fitz  # PyMuPDF
import json


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


def save_question_text(image_path: str, text: str) -> str:
    """문항 텍스트를 파일로 저장하고 경로를 반환한다."""
    import os

    text_path = os.path.splitext(image_path)[0] + ".txt"
    with open(text_path, "w", encoding="utf-8") as f:
        f.write(text)
    return text_path


def extract_question_images(pdf_path: str, out_dir: str):
    """문항 번호 기준으로 영역을 잘라 이미지로 저장하고 메타데이터를 반환한다."""
    import os
    import re

    log_path = os.path.join(out_dir, "ocr_results.json")
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            return json.load(f)

    os.makedirs(out_dir, exist_ok=True)

    # 문제 번호 패턴 (1, (1), 1번, 제1문 등 다양한 표기 인식)
    pattern = re.compile(r"(?:제)?\(?\s*\d+\s*\)?\s*(?:번|문)?\s*[.)]?")

    # 자를 때 약간의 여백을 주기 위한 마진 값
    margin = 5
    # 큰 빈 공간이 나오면 새로운 문항으로 판단하기 위한 임계값
    gap_threshold = 40

    results = []

    def finalize_region(page, region, page_number, q_index):
        out_path = os.path.join(out_dir, f"question_{q_index}.png")
        r = [
            max(0, region[0] - margin),
            max(0, region[1] - margin),
            min(page.rect.width, region[2] + margin),
            min(page.rect.height, region[3] + margin),
        ]
        pix = page.get_pixmap(clip=fitz.Rect(*r))
        pix.save(out_path)

        text_region = page.get_text("text", clip=fitz.Rect(*r)).strip()
        text_path = save_question_text(out_path, text_region)

        num_match = pattern.search(text_region)

        number = num_match.group(0) if num_match else ""
        number = re.sub(r"\D", "", number)
        sentences = re.split(r"[.!?]|\n", text_region)
        last_sentence = ""
        for s in reversed(sentences):
            s = s.strip()
            if s:
                last_sentence = s
                break

        results.append({
            "page": page_number,
            "bbox": r,
            "path": out_path,
            "text_path": text_path,
            "number": number,
            "last_sentence": last_sentence,
        })

    with fitz.open(pdf_path) as doc:
        q_index = 1
        for page_number, page in enumerate(doc, start=1):
            page_dict = page.get_text("dict")
            blocks = sorted(
                page_dict.get("blocks", []),
                key=lambda b: (b.get("bbox", [0, 0])[1], b.get("bbox", [0, 0])[0]),
            )

            region = None
            prev_bottom = 0

            for block in blocks:
                if block.get("type") != 0:
                    continue

                text = "".join(
                    span["text"]
                    for line in block.get("lines", [])
                    for span in line.get("spans", [])
                ).strip()

                if not text:
                    continue

                b = block["bbox"]

                if pattern.search(text):
                    if region:
                        finalize_region(page, region, page_number, q_index)
                        q_index += 1
                    region = list(b)
                elif region:
                    if b[1] - prev_bottom > gap_threshold:
                        finalize_region(page, region, page_number, q_index)
                        q_index += 1
                        region = list(b)
                    else:
                        region[0] = min(region[0], b[0])
                        region[1] = min(region[1], b[1])
                        region[2] = max(region[2], b[2])
                        region[3] = max(region[3], b[3])

                prev_bottom = b[3]

            if region:
                finalize_region(page, region, page_number, q_index)
                q_index += 1

    # 로그 파일 저장
    log_path = os.path.join(out_dir, "ocr_results.json")
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    return results
