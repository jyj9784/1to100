import argparse
import os
import json
from parser.structured_parser import parse_passage_and_questions
from parser.text_extractor import extract_text_from_pdf


def save_test_log(text: str, filename: str):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)


def save_by_type(questions, logdir):
    def serialize(q):
        return {
            "stem": q.stem,
            "choices": q.choices,
            "answer": q.answer,
            "explanation": q.explanation,
            "conditions": q.conditions,
            "metadata": q.metadata.__dict__
        }

    type_map = {}
    for q in questions:
        type_map.setdefault(q.metadata.type, []).append(q)

    for q_type, qlist in type_map.items():
        out_path = os.path.join(logdir, f"questions_{q_type}.json")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump([serialize(q) for q in qlist],
                      f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="PDF 국어 문제지 → 구조화 JSON 변환")
    parser.add_argument("--input", required=True, help="입력 PDF 경로")
    parser.add_argument("--output", help="출력 JSON 파일 경로 (생략 시 stdout)")
    parser.add_argument("--title", default="문제지", help="문제지 제목")
    parser.add_argument(
        "--logdir", default="./data/testlog", help="중간 로그 저장 폴더")
    args = parser.parse_args()

    # 로그
    print(f"[INFO] 입력 파일: {args.input}")
    print(f"[INFO] 제목: {args.title}")
    print(f"[INFO] 로그 폴더: {args.logdir}")
    if args.output:
        print(f"[INFO] 출력 파일: {args.output}")
    else:
        print("[INFO] 미리보기 모드 (stdout)")

    # 텍스트 추출 및 로그 저장
    text = extract_text_from_pdf(args.input)
    save_test_log(text, os.path.join(args.logdir, "extracted_text.txt"))
    passage, questions = parse_passage_and_questions(text)
    save_test_log(passage.content, os.path.join(args.logdir, "passage.txt"))

    # 질문 요약 로그
    qs = []
    for i, q in enumerate(questions):
        choices_str = ", ".join(q.choices) if q.choices else '없음'
        qs.append({
            'stem': q.stem,
            'choices': choices_str,
        })
    save_test_log(json.dumps(qs, ensure_ascii=False, indent=2),
                  os.path.join(args.logdir, "questions_log.json"))

    save_by_type(questions, args.logdir)

    # JSON 데이터 생성
    data = {
        "set_title": args.title,
        "passages": [passage.to_dict()],
        "questions": [q.to_dict() for q in questions]
    }

    if args.output:
        out = args.output
        if os.path.isdir(out):
            os.makedirs(out, exist_ok=True)
            out = os.path.join(out, f"{args.title}.json")
        else:
            os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[INFO] 저장됨: {out}")
    else:
        # stdout에 출력
        print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
