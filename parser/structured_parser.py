import re
import fitz  # PyMuPDF
import os
import json
from typing import List, Tuple, Optional, Dict
from model.question import Question, Metadata
from model.passage import Passage

# --- 헬퍼 함수 정의 ---

def save_region_as_image(page: fitz.Page, bbox: fitz.Rect, output_dir: str, filename: str) -> str:
    """페이지의 특정 영역(bbox)을 이미지 파일로 저장하고 경로를 반환합니다."""
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    pix = page.get_pixmap(clip=bbox, matrix=fitz.Matrix(2, 2))  # 2x 해상도
    pix.save(output_path)
    return output_path

def get_content_blocks_with_coords(pdf_path: str) -> List[Dict]:
    """
    PDF에서 머리말/꼬리말을 제외한 본문 영역의 텍스트 블록과 좌표를 추출합니다.
    2단 레이아웃을 고려하여 각 블록의 열 정보를 포함합니다.

    Args:
        pdf_path (str): PDF 파일 경로.

    Returns:
        List[Dict]: 각 블록의 텍스트, BBox, 페이지 번호, 열 정보를 담은 딕셔너리 리스트.
    """
    doc = fitz.open(pdf_path)
    all_blocks = []

    for page_num, page in enumerate(doc):
        width, height = page.rect.width, page.rect.height
        top_margin = height * 0.08
        bottom_margin = height * 0.92

        # 페이지의 모든 텍스트 블록 추출
        page_blocks = page.get_text("dict")["blocks"]

        for block in page_blocks:
            if block["type"] == 0:  # 텍스트 블록인 경우
                bbox = fitz.Rect(block["bbox"])
                # 블록이 본문 영역 내에 있는지 확인
                if bbox.y0 >= top_margin and bbox.y1 <= bottom_margin:
                    col = "left" if bbox.x1 <= width / 2 else "right"
                    text = "".join([span["text"] for line in block["lines"] for span in line["spans"]])
                    all_blocks.append({
                        "text": text.strip(),
                        "bbox": [bbox.x0, bbox.y0, bbox.x1, bbox.y1],
                        "page": page_num,
                        "col": col
                    })
    doc.close()
    # 블록들을 y좌표, x좌표 순으로 정렬하여 읽는 순서 보장
    all_blocks.sort(key=lambda b: (b['page'], b['bbox'][1], b['bbox'][0]))
    return all_blocks

def extract_choices(text: str) -> List[str]:
    """
    문제 본문 텍스트에서 객관식 선택지(①, ②, ③, ④, ⑤)를 추출합니다.

    Args:
        text (str): 선택지를 포함하고 있는 문제의 전체 텍스트.

    Returns:
        List[str]: 추출된 선택지 문자열의 리스트.
    """
    normalized_text = text.replace('\n', ' ')
    pattern = r"(①.*?)(?=②|③|④|⑤|$)|(②.*?)(?=①|③|④|⑤|$)|(③.*?)(?=①|②|④|⑤|$)|(④.*?)(?=①|②|③|⑤|$)|(⑤.*?)(?=①|②|③|④|$)"
    matches = re.findall(pattern, normalized_text)
    choices = [item for tpl in matches for item in tpl if item]
    return [c.strip() for c in choices]

def classify_question_type(text: str) -> str:
    """
    문제 텍스트의 내용을 기반으로 문제 유형을 분류합니다.
    (e.g., multiple_choice, conditional, subjective)

    Args:
        text (str): 문제의 전체 텍스트.

    Returns:
        str: 분류된 문제 유형.
    """
    if "<보기>" in text:
        return "conditional"
    if "①" in text and "②" in text:
        return "multiple_choice"
    if any(keyword in text for keyword in ["서술하시오", "설명하시오", "쓰시오"]):
        return "subjective"
    return "etc"

def is_question_start(text: str) -> bool:
    """
    해당 텍스트 줄이 문제의 시작인지 (e.g., "1.", "2)") 판별합니다.

    Args:
        text (str): 확인할 텍스트 한 줄.

    Returns:
        bool: 문제의 시작이면 True, 아니면 False.
    """
    return bool(re.match(r"^\d{1,2}\s*[.)]", text))

def should_skip_line(text: str) -> bool:
    """
    파싱 과정에서 무시해야 할 불필요한 줄인지 판별합니다.
    (e.g., 페이지 번호, 시험지 제목, 저작권 문구 등)

    Args:
        text (str): 확인할 텍스트 한 줄.

    Returns:
        bool: 무시해야 할 줄이면 True, 아니면 False.
    """
    skip_patterns = [
        r"^\d{4}학년도 대학수학능력시험 문제지$",
        r"^제\d+\s*교시$",
        r"^홀수형$",
        r"^짝수형$",
        r"^\d+\s*/\s*\d+$",
        r"이 문제지에 관한 저작권은",
        r"확인 사항",
        r"자신이 선택한 과목인지 확인하시오"
    ]
    return any(re.search(p, text) for p in skip_patterns)

def is_passage_start_enhanced(text: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    해당 텍스트 줄이 지문의 시작인지 판별합니다.
    (e.g., "[1~3] 다음 글을 읽고 물음에 답하시오.")

    Args:
        text (str): 확인할 텍스트 한 줄.

    Returns:
        Tuple[bool, Optional[str], Optional[str]]: 
        지문 시작 여부, 문제 범위(e.g., "1~3"), 지시문(e.g., "다음 글을...") 튜플.
    """
    pattern = r'^\s*\[(\d+)[~∼～-](\d+)\]\s*(.*)'
    match = re.match(pattern, text)
    if match:
        question_range = f"{match.group(1)}~{match.group(2)}"
        instruction = match.group(0)
        return True, question_range, instruction
    return False, None, None

def get_question_number(text: str) -> Optional[int]:
    """
    텍스트 줄에서 문제 번호를 추출합니다.

    Args:
        text (str): 문제 번호를 포함한 텍스트 한 줄.

    Returns:
        Optional[int]: 추출된 문제 번호. 없으면 0을 반환.
    """
    match = re.match(r"^(\d+)", text.strip())
    if match:
        return int(match.group(1))
    return 0

def create_question_from_block(block_lines: List[str], passage_id: str, question_number: int) -> Optional[Question]:
    """
    수집된 문제 블록(텍스트 줄 리스트)으로부터 Question 객체를 생성합니다.

    Args:
        block_lines (List[str]): 하나의 문제를 구성하는 텍스트 줄들의 리스트.
        passage_id (str): 이 문제가 속한 지문의 ID.
        question_number (int): 문제 번호.

    Returns:
        Optional[Question]: 생성된 Question 객체. 내용이 없으면 None.
    """
    if not block_lines:
        return None
    
    full_text = "\n".join(block_lines)
    q_type = classify_question_type(full_text)
    metadata = Metadata(type=q_type, difficulty="중", points=None)
    choices = extract_choices(full_text)
    
    # 문제 본문(stem) 추출: 전체 텍스트에서 선택지 부분을 제외한 나머지
    stem = full_text
    match = re.search(r"①|②|③|④|⑤", stem)
    if match:
        stem = stem[:match.start()].strip()
    
    # 문제 본문에서 문제 번호 텍스트(e.g., "1.") 제거
    stem = re.sub(r"^\d+\s*[.)]\s*", "", stem).strip()

    return Question(
        stem=stem,
        choices=choices if choices else None,
        answer=None,  # 현재 정답 추출 로직은 구현되지 않음
        metadata=metadata,
        passage_id=passage_id,
        question_number=question_number
    )

# --- 메인 파싱 함수 ---

def parse_all_passages_and_questions(text: str) -> Tuple[List[Passage], List[Question]]:
    """
    PDF에서 추출된 전체 텍스트를 분석하여 모든 지문과 문제를 파싱합니다.
    상태(지문, 문제)를 추적하며 텍스트를 한 줄씩 읽어 지문과 문제를 구분합니다.
    이 함수는 텍스트 파싱에만 집중하며, 이미지 추출은 별도로 처리됩니다.

    Args:
        text (str): PDF에서 추출된 전체 텍스트.

    Returns:
        Tuple[List[Passage], List[Question]]: 추출된 모든 Passage 객체 리스트와 Question 객체 리스트.
    """
    lines = text.splitlines()
    passages = []
    questions = []
    current_passage_content = []
    current_question_block = []
    passage_counter = 0
    current_question_number = 0
    current_passage_id = None
    in_passage = False
    in_question = False

    for line in lines:
        stripped = line.strip()
        if not stripped or should_skip_line(stripped):
            continue

        is_passage, q_range, instruction = is_passage_start_enhanced(stripped)
        
        if is_passage:
            # 이전 문제 블록이 있었다면 질문으로 저장
            if current_question_block:
                question = create_question_from_block(current_question_block, current_passage_id, current_question_number)
                if question:
                    questions.append(question)
                current_question_block = []

            # 이전 지문이 있었다면 내용 저장
            if current_passage_content and passages:
                passages[-1].content = "\n".join(current_passage_content).strip()

            # 새 지문 시작
            passage_counter += 1
            current_passage_id = f"passage_{passage_counter}"
            passage = Passage(content="", passage_id=current_passage_id, question_range=q_range, instruction=instruction)
            passages.append(passage)
            current_passage_content = [instruction]
            in_passage = True
            in_question = False
            continue

        if is_question_start(stripped):
            # 이전 문제 블록 저장
            if current_question_block:
                question = create_question_from_block(current_question_block, current_passage_id, current_question_number)
                if question:
                    questions.append(question)
            
            # 현재 문제 번호 업데이트
            current_question_number = get_question_number(stripped)
            
            # 지문 내용이 있었다면 최종 저장
            if current_passage_content and passages:
                passages[-1].content = "\n".join(current_passage_content).strip()
                current_passage_content = []

            # 새 문제 시작
            current_question_block = [stripped]
            in_passage = False
            in_question = True
            continue

        # 현재 상태에 따라 내용 추가
        if in_question:
            current_question_block.append(stripped)
        elif in_passage:
            current_passage_content.append(stripped)

    # 마지막 블록 처리
    if current_question_block:
        question = create_question_from_block(current_question_block, current_passage_id, current_question_number)
        if question:
            questions.append(question)
    if current_passage_content and passages:
        passages[-1].content = "\n".join(current_passage_content).strip()

    return passages, questions

def extract_question_image(pdf_path: str, question: Question, output_dir: str) -> Optional[str]:
    """
    주어진 Question 객체의 텍스트를 PDF에서 찾아 해당 영역의 이미지를 추출합니다.
    문제 번호 시작부터 5번 선택지 끝까지를 영역으로 정합니다.
    2단 레이아웃을 고려하여 해당 열 내에서만 이미지를 추출합니다.

    Args:
        pdf_path (str): 원본 PDF 파일 경로.
        question (Question): 이미지 추출 대상 Question 객체.
        output_dir (str): 이미지를 저장할 기본 출력 디렉토리.

    Returns:
        Optional[str]: 추출된 이미지 파일 경로. 실패 시 None.
    """
    doc = fitz.open(pdf_path)
    image_output_dir = os.path.join(output_dir, "images")
    os.makedirs(image_output_dir, exist_ok=True)

    all_blocks = get_content_blocks_with_coords(pdf_path)

    start_block_found = False
    question_blocks = []
    target_page = None
    target_col = None

    for i, block in enumerate(all_blocks):
        block_text = block["text"]
        block_page = block["page"]
        block_col = block["col"]

        # Find the starting block of the question
        # Check if the block text starts with the question number and contains part of the stem
        # Using a more flexible check for stem as it might be split across blocks
        if not start_block_found:
            # Ensure question.stem is not empty before trying to split
            stem_first_line = question.stem.splitlines()[0].strip() if question.stem else ""
            if str(question.question_number) in block_text and stem_first_line in block_text:
                start_block_found = True
                target_page = block_page
                target_col = block_col
                question_blocks.append(block)
                continue
        
        # Once the start block is found, collect subsequent blocks that belong to the same question
        if start_block_found:
            # Stop if it's a new page or a different column
            if block_page != target_page or block_col != target_col:
                break
            
            # Stop if it's a new question or a passage start
            if is_question_start(block_text) and get_question_number(block_text) != question.question_number:
                break
            if is_passage_start_enhanced(block_text)[0]:
                break
            
            question_blocks.append(block)

    if not question_blocks:
        doc.close()
        return None

    # Calculate the combined bounding box for all collected question blocks
    min_x = float('inf')
    min_y = float('inf')
    max_x = float('-inf')
    max_y = float('-inf')

    for block in question_blocks:
        bbox = fitz.Rect(block["bbox"])
        min_x = min(min_x, bbox.x0)
        min_y = min(min_y, bbox.y0)
        max_x = max(max_x, bbox.x1)
        max_y = max(max_y, bbox.y1)

    combined_bbox = fitz.Rect(min_x, min_y, max_x, max_y)

    # Add padding
    padding = 10
    combined_bbox.x0 = max(0, combined_bbox.x0 - padding)
    combined_bbox.y0 = max(0, combined_bbox.y0 - padding)
    combined_bbox.x1 = min(doc[target_page].rect.width, combined_bbox.x1 + padding)
    combined_bbox.y1 = min(doc[target_page].rect.height, combined_bbox.y1 + padding)

    img_filename = f"question_{question.passage_id}_{question.question_number}.png"
    image_path = save_region_as_image(doc[target_page], combined_bbox, image_output_dir, img_filename)
    doc.close()
    return image_path

def extract_passage_image(pdf_path: str, passage: Passage, output_dir: str) -> Optional[str]:
    """
    주어진 Passage 객체의 텍스트를 PDF에서 찾아 해당 영역의 이미지를 추출합니다.
    지문 시작부터 끝까지를 영역으로 정합니다.

    Args:
        pdf_path (str): 원본 PDF 파일 경로.
        passage (Passage): 이미지 추출 대상 Passage 객체.
        output_dir (str): 이미지를 저장할 기본 출력 디렉토리.

    Returns:
        Optional[str]: 추출된 이미지 파일 경로. 실패 시 None.
    """
    doc = fitz.open(pdf_path)
    image_output_dir = os.path.join(output_dir, "images")
    os.makedirs(image_output_dir, exist_ok=True)

    all_blocks = get_content_blocks_with_coords(pdf_path)

    start_block_found = False
    passage_blocks = []
    target_page = None
    target_col = None

    # Find the starting block of the passage
    search_start_text = passage.instruction.splitlines()[0].strip() if passage.instruction else passage.content.splitlines()[0].strip()
    if not search_start_text:
        doc.close()
        return None

    for i, block in enumerate(all_blocks):
        block_text = block["text"]
        block_page = block["page"]
        block_col = block["col"]

        if not start_block_found:
            if search_start_text in block_text:
                start_block_found = True
                target_page = block_page
                target_col = block_col
                passage_blocks.append(block)
                continue
        
        if start_block_found:
            # Stop if it's a new page or a different column
            if block_page != target_page or block_col != target_col:
                break
            
            # Stop if it's a new question or a new passage start
            if is_question_start(block_text):
                break
            if is_passage_start_enhanced(block_text)[0] and block_text != search_start_text:
                break
            
            passage_blocks.append(block)

    if not passage_blocks:
        doc.close()
        return None

    # Calculate the combined bounding box for all collected passage blocks
    min_x = float('inf')
    min_y = float('inf')
    max_x = float('-inf')
    max_y = float('-inf')

    for block in passage_blocks:
        bbox = fitz.Rect(block["bbox"])
        min_x = min(min_x, bbox.x0)
        min_y = min(min_y, bbox.y0)
        max_x = max(max_x, bbox.x1)
        max_y = max(max_y, bbox.y1)

    combined_bbox = fitz.Rect(min_x, min_y, max_x, max_y)

    # Add padding
    padding = 10
    combined_bbox.x0 = max(0, combined_bbox.x0 - padding)
    combined_bbox.y0 = max(0, combined_bbox.y0 - padding)
    combined_bbox.x1 = min(doc[target_page].rect.width, combined_bbox.x1 + padding)
    combined_bbox.y1 = min(doc[target_page].rect.height, combined_bbox.y1 + padding)

    img_filename = f"passage_{passage.passage_id}.png"
    image_path = save_region_as_image(doc[target_page], combined_bbox, image_output_dir, img_filename)
    doc.close()
    return image_path