import argparse
import os
from parser.structured_parser import parse_passage_and_questions
from parser.text_extractor import extract_text_from_pdf
from export.json_exporter import export_to_ilobag_json

def save_test_log(text: str, filename: str):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)

def main():
    parser = argparse.ArgumentParser(description="PDF 국어 문제지 → 구조화 JSON 변환")
    parser.add_argument("--input", required=True, help="입력 PDF 경로")
    parser.add_argument("--output", required=True, help="출력 JSON 파일 경로")
    parser.add_argument("--title", default="문제지", help="문제지 제목")
    parser.add_argument("--logdir", default="./data/testlog", help="중간 로그 저장 폴더")
    args = parser.parse_args()

    print(f"[INFO] 입력 파일: {args.input}")
    print(f"[INFO] 출력 파일: {args.output}")
    print(f"[INFO] 문제지 제목: {args.title}")
    print(f"[INFO] 로그 폴더: {args.logdir}")

    # 1. PDF → 텍스트 변환
    text = extract_text_from_pdf(args.input)
    save_test_log(text, os.path.join(args.logdir, "extracted_text.txt"))

    # 2. 텍스트 → Passage + Questions 파싱
    passage, questions = parse_passage_and_questions(text)
    save_test_log(passage.content, os.path.join(args.logdir, "passage.txt"))

    questions_summary = "\n\n".join(
        f"Q{i+1}: [{q.metadata.type}] {q.stem[:50]}..." for i, q in enumerate(questions)
    )
    save_test_log(questions_summary, os.path.join(args.logdir, "questions_summary.txt"))

    questions_full = "\n\n".join(
        f"Q{i+1}:\nStem: {q.stem}\nChoices: {q.choices_text}\n" for i, q in enumerate(questions)
    )
    save_test_log(questions_full, os.path.join(args.logdir, "questions_full.txt"))

    # 3. 최종 JSON 저장
    export_to_ilobag_json(args.title, passage, questions, args.output)

if __name__ == "__main__":
    main()
