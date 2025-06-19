import fitz  # PyMuPDF
import json


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    PDF에서 좌우 텍스트만 추출한다. (이미지 좌표는 추출하지 않음)

    :param pdf_path: PDF 파일 경로
    :return: 전체 텍스트 문자열
    """
    extracted_text = ""

    with fitz.open(pdf_path) as doc:
        for page in doc:
            width, height = page.rect.width, page.rect.height
            top_margin = 60
            bottom_margin = 70

            # 좌우 영역 분할
            left_rect = fitz.Rect(0, top_margin, width / 2, height - bottom_margin)
            right_rect = fitz.Rect(width / 2, top_margin, width, height - bottom_margin)

            # 각 영역에서 텍스트 추출
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


def extract_question_images(
    pdf_path: str,
    out_dir: str,
    top_margin: int = 60,
    bottom_margin: int = 70,
):
    """문항 번호 기준으로 영역을 잘라 이미지로 저장하고 메타데이터를 반환한다.

    :param pdf_path: PDF 파일 경로
    :param out_dir: 결과 이미지를 저장할 폴더 경로
    :param top_margin: 페이지 상단 여백
    :param bottom_margin: 페이지 하단 여백
    """
    import os
    import re

    log_path = os.path.join(out_dir, "ocr_results.json")
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            return json.load(f)

    os.makedirs(out_dir, exist_ok=True)

    pattern = re.compile(r"^(?:\(\d+\)|\d+\s*[.)])")

    results = []

    with fitz.open(pdf_path) as doc:
        q_index = 1
        for page_number, page in enumerate(doc, start=1):
            width, height = page.rect.width, page.rect.height
            clip_page = fitz.Rect(0, top_margin, width, height - bottom_margin)
            page_dict = page.get_text("dict", clip=clip_page)
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
                        out_path = os.path.join(out_dir, f"question_{q_index}.png")
                        clip_rect = fitz.Rect(
                            region[0],
                            max(region[1], top_margin),
                            region[2],
                            min(region[3], height - bottom_margin),
                        )
                        pix = page.get_pixmap(clip=clip_rect)
                        pix.save(out_path)

                        text_region = page.get_text("text", clip=clip_rect).strip()
                        text_path = save_question_text(out_path, text_region)

                        num_match = pattern.match(text_region)

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
                            "bbox": [clip_rect.x0, clip_rect.y0, clip_rect.x1, clip_rect.y1],
                            "path": out_path,
                            "text_path": text_path,
                            "number": number,
                            "last_sentence": last_sentence,
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
                out_path = os.path.join(out_dir, f"question_{q_index}.png")
                clip_rect = fitz.Rect(
                    region[0],
                    max(region[1], top_margin),
                    region[2],
                    min(region[3], height - bottom_margin),
                )
                pix = page.get_pixmap(clip=clip_rect)
                pix.save(out_path)
                text_region = page.get_text("text", clip=clip_rect).strip()
                text_path = save_question_text(out_path, text_region)

                num_match = pattern.match(text_region)

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
                    "bbox": [clip_rect.x0, clip_rect.y0, clip_rect.x1, clip_rect.y1],
                    "path": out_path,
                    "text_path": text_path,
                    "number": number,
                    "last_sentence": last_sentence,
                })
                q_index += 1

    # 로그 파일 저장
    log_path = os.path.join(out_dir, "ocr_results.json")
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    return results
