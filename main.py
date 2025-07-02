import argparse
import os
import json
from parser.structured_parser import parse_all_passages_and_questions
from parser.text_extractor import extract_text_from_pdf

def save_test_log(text: str, filename: str):
    """주어진 텍스트를 지정된 파일에 저장합니다. (디버깅 및 로그용)"""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)

def save_by_type(questions, logdir):
    """파싱된 질문들을 유형별로 분류하여 별도의 JSON 파일로 저장합니다."""
    def serialize(q):
        # Question 객체를 JSON으로 저장 가능한 dict 형태로 변환
        return {
            "stem": q.stem,
            "choices": q.choices,
            "answer": q.answer,
            "explanation": q.explanation,
            "conditions": q.conditions,
            "metadata": q.metadata.__dict__,
            "passage_id": q.passage_id,
            "question_number": q.question_number
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

def save_passages_log(passages, logdir):
    """파싱된 지문들을 각각 별도의 텍스트 파일로 저장합니다."""
    for i, passage in enumerate(passages):
        filename = f"passage_{i+1}_{passage.question_range or 'unknown'}.txt"
        filepath = os.path.join(logdir, filename)
        
        content = f"지문 ID: {passage.passage_id}\n"
        content += f"문제 범위: {passage.question_range}\n"
        content += f"지시문: {passage.instruction}\n"
        content += "-" * 50 + "\n"
        content += passage.content
        
        save_test_log(content, filepath)

def main():
    """
    CLI(명령줄 인터페이스)의 메인 실행 함수입니다.
    입력받은 PDF를 파싱하여 결과를 JSON으로 저장하고, 중간 로그를 남깁니다.
    """
    parser = argparse.ArgumentParser(description="PDF 국어 문제지 -> 구조화 JSON 변환 (복수 지문 지원)")
    parser.add_argument("--input", required=True, help="입력 PDF 경로")
    parser.add_argument("--output", help="출력 JSON 파일 경로 (생략 시 stdout)")
    parser.add_argument("--title", default="수능 국어 문제지", help="문제지 제목")
    parser.add_argument("--logdir", default="./data/testlog", help="중간 로그 저장 폴더")
    args = parser.parse_args()

    print(f"[INFO] 입력 파일: {args.input}")
    print(f"[INFO] 제목: {args.title}")
    print(f"[INFO] 로그 폴더: {args.logdir}")

    # 1. PDF에서 텍스트 추출
    print("[INFO] PDF 텍스트 추출 중...")
    text = extract_text_from_pdf(args.input)
    save_test_log(text, os.path.join(args.logdir, "extracted_text.txt"))
    
    # 2. 텍스트에서 지문과 문제 파싱
    print("[INFO] 지문 및 문제 파싱 중...")
    passages, questions = parse_all_passages_and_questions(text)
    print(f"[INFO] 파싱 완료: 지문 {len(passages)}개, 문제 {len(questions)}개")
    
    # 3. 파싱 결과 로그 저장
    save_passages_log(passages, args.logdir)
    save_by_type(questions, args.logdir)

    # 4. 최종 결과 JSON 데이터 생성
    data = {
        "set_title": args.title,
        "passages": [p.to_dict() for p in passages],
        "questions": [q.to_dict() for q in questions],
        "summary": {
            "total_passages": len(passages),
            "total_questions": len(questions),
            "question_types": {q_type: len(q_list) for q_type, q_list in {q.metadata.type: [] for q in questions}.items()}
        }
    }
    # 문제 유형별 통계 다시 계산
    type_counts = {}
    for q in questions:
        q_type = q.metadata.type
        type_counts[q_type] = type_counts.get(q_type, 0) + 1
    data["summary"]["question_types"] = type_counts

    # 5. 최종 결과물 출력 또는 저장
    if args.output:
        out_path = args.output
        if os.path.isdir(out_path):
            os.makedirs(out_path, exist_ok=True)
            out_path = os.path.join(out_path, f"{args.title}.json")
        else:
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[INFO] 최종 결과 저장됨: {out_path}")
    else:
        # 출력 경로가 없으면 콘솔에 JSON 출력
        print(json.dumps(data, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
