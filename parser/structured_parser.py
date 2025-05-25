import re
import json
from typing import List, Tuple
from model.question import Question, Metadata
from model.passage import Passage


def classify_question_type(text: str) -> str:
    text = text.replace("\n", " ")
    if re.search(r">\s*정답", text):
        return "answer"
    if re.search(r"\(\s{0,3}\)|\[O/X\]", text):
        return "ox"
    if re.search(r"_{2,}|빈칸|들어갈 말", text):
        return "blank"
    if re.search(r"①.*?②.*?③.*?④.*?⑤", text, re.DOTALL):
        return "multiple_choice"
    if re.search(r"서술하시오|설명하시오|쓰시오|30자|50자", text):
        return "subjective"
    if re.search(r"보기|㉠|조건|자료", text):
        return "conditional"
    if re.search(r"ㄱ|ㄴ|ㄷ", text):
        return "composite"
    return "etc"


def extract_choices(block_lines: List[str]) -> List[str]:
    text = " ".join(block_lines)
    # ① ~ ⑤ 로 시작하는 보기 항목을 모두 추출
    pattern = r"(①[^②③④⑤]+|②[^①③④⑤]+|③[^①②④⑤]+|④[^①②③⑤]+|⑤[^①②③④]+)"
    matches = re.findall(pattern, text)
    return [m.strip() for m in matches]


def parse_passage_and_questions(text: str) -> Tuple[Passage, List[Question]]:
    lines = text.splitlines()
    passage_lines = []
    question_blocks = []
    current_block = []
    is_question_section = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # 지문과 문제 구분 조건
        if not is_question_section and re.search(r"(문제|보기|다음|정답|①|②|③|④|⑤)", stripped):
            is_question_section = True

        if is_question_section:
            # 새로운 문제 번호 인식 패턴 강화
            if re.match(r"^\d+\.\s*", stripped):
                if current_block:
                    question_blocks.append(current_block)
                current_block = [stripped]
            else:
                current_block.append(stripped)
        else:
            passage_lines.append(stripped)

    if current_block:
        question_blocks.append(current_block)

    passage = Passage("\n".join(passage_lines).strip())
    questions: List[Question] = []

    for block in question_blocks:
        if not block:
            continue

        full_text = " ".join(block)
        q_type = classify_question_type(full_text)
        metadata = Metadata(type=q_type, difficulty="중", points=None)

        choices = extract_choices(block)

        # 보기 있는 경우: 보기 앞까지를 stem으로 간주
        stem = []
        for line in block:
            if re.match(r"[①②③④⑤]", line.strip()):
                break
            stem.append(line.strip())

        stem_only = " ".join(stem)

        question = Question(
            stem=stem_only,
            choices=choices if choices else None,
            answer=None,
            explanation=None,
            conditions=None,
            metadata=metadata
        )

        if q_type == "subjective":
            question.choices = None

        questions.append(question)

    return passage, questions
