# parser/structured_parser.py (개선된 리팩토링 버전)
import re
from typing import List, Tuple
from model.question import Question, Metadata
from model.passage import Passage


def classify_question_type(text: str) -> str:
    text = text.replace("\n", " ")
    if re.search(r"\(\s{0,3}\)|\[O/X\]", text):
        return "ox"
    if re.search(r"_{2,}|빈칸|들어갈 말", text):
        return "blank"
    if re.search(r"①|②|③|④|⑤", text):
        return "multiple_choice"
    if re.search(r"서술하시오|설명하시오|쓰시오|30자|50자", text):
        return "subjective"
    if re.search(r"보기|㉠|조건|자료", text):
        return "conditional"
    if re.search(r"ㄱ|ㄴ|ㄷ", text):
        return "composite"
    return "etc"


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

        if not is_question_section and re.search(r"(문제|둘째 걸음|셋째 걸음|넷째 걸음|다음 글을 읽고|퀴즈 정답과 해설)", stripped):
            is_question_section = True
            continue

        if is_question_section:
            # 문제 번호 감지: 번호로 시작하고 마침표나 괄호 포함
            if re.match(r"^\d+[\).]?", stripped):
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

        # stem 추출: 번호 제거 + 전체 본문 병합
        stem_raw = " ".join(block)
        stem = re.sub(r"^\d+[\).]\s*", "", stem_raw).strip()

        if len(stem) < 2:
            continue  # 빈 문제 제거

        # 선택지 추출
        choices = [l for l in block if re.search(r"①|②|③|④|⑤", l)]
        choices_text = "\n".join(choices) if choices else None

        metadata = Metadata(type=q_type, difficulty="중", points=None)

        question = Question(
            stem=stem,
            choices_text=choices_text,
            answer=None,
            explanation=None,
            conditions=None,
            metadata=metadata
        )
        questions.append(question)

    return passage, questions