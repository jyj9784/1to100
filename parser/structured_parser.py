import re
import json
from typing import List, Tuple
from model.question import Question, Metadata
from model.passage import Passage


def is_question_start(text: str) -> bool:
    """질문 번호 패턴 인식"""
    pattern = r"^(?:\(\d+\)|\d+\s*[.)])"
    return bool(re.match(pattern, text))


def should_skip_line(text: str) -> bool:
    """문제지 하단 부가 문구 등 무시"""
    skip_patterns = [
        r"이 문제지에 관한 저작권", r"^\d+\s*(?:홀수형|짝수형)?$",
    ]
    return any(re.search(p, text) for p in skip_patterns)


def is_passage_intro(text: str) -> bool:
    """'다음'으로 시작하고 '중'이 앞부분에 없는 문장인지 확인"""
    pattern = r"^(?:\[[^\]]+\]\s*)?다음\s*"
    return bool(re.match(pattern, text)) and "중" not in text[:5]


def extract_answer(block_lines: List[str]) -> Tuple[List[str], str | None]:
    """블록에서 정답 표기를 찾아 제거 후 반환"""
    answer_pattern = re.compile(r"정답[:：]?\s*([①-⑤OX])")
    answer = None
    cleaned = []
    for line in block_lines:
        m = answer_pattern.search(line)
        if m:
            answer = m.group(1)
            line = answer_pattern.sub("", line).strip()
            if line:
                cleaned.append(line)
        else:
            cleaned.append(line)
    return cleaned, answer


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
    pattern = r"(①[^②③④⑤]+|②[^①③④⑤]+|③[^①②④⑤]+|④[^①②③⑤]+|⑤[^①②③④]+)"
    matches = re.findall(pattern, text)
    return [m.strip() for m in matches]


def parse_passage_and_questions(text: str) -> Tuple[Passage, List[Question]]:
    lines = text.splitlines()
    passage_lines: List[str] = []
    question_blocks: List[List[str]] = []
    current_block: List[str] = []
    is_question_section = False

    for line in lines:
        stripped = line.strip()
        if not stripped or should_skip_line(stripped):
            continue

        if is_question_section and is_passage_intro(stripped):
            if current_block:
                question_blocks.append(current_block)
                current_block = []
            current_block.append(stripped)
            continue

        if not is_question_section and re.search(r"(문제|보기|다음|정답|①|②|③|④|⑤)", stripped):
            is_question_section = True

        if is_question_section:
            if is_question_start(stripped):
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

        block, answer = extract_answer(block)
        choices = extract_choices(block)

        stem = []
        for line in block:
            if re.match(r"[①②③④⑤]", line.strip()):
                break
            stem.append(line.strip())

        stem_only = " ".join(stem)

        question = Question(
            stem=stem_only,
            choices=choices if choices else None,
            answer=answer,
            explanation=None,
            conditions=None,
            metadata=metadata
        )

        if q_type == "subjective":
            question.choices = None

        questions.append(question)

    return passage, questions
