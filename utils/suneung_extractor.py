"""
수능 국어 PDF 추출 통합 유틸리티
기존 코드와 새로운 복수 지문 기능을 통합
"""

import os
import json
from typing import List, Dict, Tuple
from parser.text_extractor import extract_text_from_pdf, extract_question_images
from parser.structured_parser import parse_all_passages_and_questions
from model.passage import Passage
from model.question import Question

class SuneungExtractor:
    """수능 국어 PDF 추출 통합 클래스"""
    
    def __init__(self, output_base_dir: str = "./extracted_content"):
        self.output_base_dir = output_base_dir
        
    def extract_from_pdf(self, pdf_path: str, title: str = "수능국어") -> Dict:
        """
        PDF에서 지문과 문제를 추출하는 메인 함수
        
        Args:
            pdf_path: PDF 파일 경로
            title: 문제지 제목
            
        Returns:
            추출 결과 딕셔너리
        """
        print(f"📄 PDF 분석 시작: {pdf_path}")
        
        # 출력 디렉터리 설정
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        output_dir = os.path.join(self.output_base_dir, safe_title)
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. 텍스트 추출
        print("📝 텍스트 추출 중...")
        raw_text = extract_text_from_pdf(pdf_path)
        self._save_raw_text(raw_text, output_dir)
        
        # 2. 이미지 추출
        print("🖼️ 문항 이미지 추출 중...")
        img_dir = os.path.join(output_dir, "question_images")
        img_results = extract_question_images(pdf_path, img_dir)
        
        # 3. 구조화 파싱
        print("🔍 지문 및 문제 파싱 중...")
        passages, questions = parse_all_passages_and_questions(raw_text)
        
        # 4. 결과 저장
        result = self._create_result_dict(title, passages, questions, img_results, output_dir)
        self._save_all_results(result, output_dir)
        
        print(f"✅ 추출 완료!")
        print(f"📁 출력 디렉터리: {output_dir}")
        print(f"📄 지문 수: {len(passages)}")
        print(f"❓ 문제 수: {len(questions)}")
        
        return result
    
    def _save_raw_text(self, text: str, output_dir: str):
        """원본 텍스트 저장"""
        text_path = os.path.join(output_dir, "raw_extracted_text.txt")
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(text)
    
    def _create_result_dict(self, title: str, passages: List[Passage], 
                           questions: List[Question], img_results: List[Dict], 
                           output_dir: str) -> Dict:
        """결과 딕셔너리 생성"""
        return {
            "metadata": {
                "title": title,
                "total_passages": len(passages),
                "total_questions": len(questions),
                "output_directory": output_dir
            },
            "passages": [p.to_dict() for p in passages],
            "questions": [q.to_dict() for q in questions],
            "question_images": img_results,
            "statistics": self._calculate_statistics(passages, questions)
        }
    
    def _calculate_statistics(self, passages: List[Passage], questions: List[Question]) -> Dict:
        """통계 정보 계산"""
        stats = {
            "passage_stats": [],
            "question_types": {},
            "questions_per_passage": {}
        }
        
        # 지문별 통계
        for passage in passages:
            stats["passage_stats"].append({
                "id": passage.passage_id,
                "question_range": passage.question_range,
                "word_count": len(passage.content),
                "char_count": len(passage.content)
            })
        
        # 문제 유형별 통계
        for question in questions:
            q_type = question.metadata.type
            stats["question_types"][q_type] = stats["question_types"].get(q_type, 0) + 1
            
            # 지문별 문제 수
            p_id = question.passage_id or "unknown"
            stats["questions_per_passage"][p_id] = stats["questions_per_passage"].get(p_id, 0) + 1
        
        return stats
    
    def _save_all_results(self, result: Dict, output_dir: str):
        """모든 결과 파일 저장"""
        # 1. 통합 JSON 저장
        json_path = os.path.join(output_dir, "extraction_results.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        # 2. 지문별 개별 파일 저장
        passages_dir = os.path.join(output_dir, "passages")
        os.makedirs(passages_dir, exist_ok=True)
        
        for passage_data in result["passages"]:
            filename = f"{passage_data['id']}_{passage_data['question_range'] or 'unknown'}.txt"
            filepath = os.path.join(passages_dir, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"지문 ID: {passage_data['id']}\n")
                f.write(f"문제 범위: {passage_data['question_range']}\n")
                f.write(f"지시문: {passage_data['instruction']}\n")
                f.write("-" * 50 + "\n")
                f.write(passage_data['content'])
        
        # 3. 문제별 개별 파일 저장
        questions_dir = os.path.join(output_dir, "questions")
        os.makedirs(questions_dir, exist_ok=True)
        
        for question_data in result["questions"]:
            q_num = question_data['question_number'] or "unknown"
            filename = f"question_{q_num}_{question_data['passage_id']}.txt"
            filepath = os.path.join(questions_dir, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"문제 번호: {question_data['question_number']}\n")
                f.write(f"연관 지문: {question_data['passage_id']}\n")
                f.write(f"문제 유형: {question_data['metadata']['type']}\n")
                f.write("-" * 50 + "\n")
                f.write(question_data['stem'])
                
                if question_data['choices']:
                    f.write("\n\n선택지:\n")
                    for i, choice in enumerate(question_data['choices']):
                        f.write(f"{i+1}. {choice}\n")
                
                if question_data['answer']:
                    f.write(f"\n정답: {question_data['answer']}")
        
        # 4. 요약 보고서 저장
        summary_path = os.path.join(output_dir, "summary_report.txt")
        summary = self._generate_summary_report(result)
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(summary)
    
    def _generate_summary_report(self, result: Dict) -> str:
        """요약 보고서 생성"""
        lines = []
        lines.append("=" * 60)
        lines.append("수능 국어 지문/문제 추출 결과 보고서")
        lines.append("=" * 60)
        lines.append(f"문제지 제목: {result['metadata']['title']}")
        lines.append(f"총 지문 수: {result['metadata']['total_passages']}")
        lines.append(f"총 문제 수: {result['metadata']['total_questions']}")
        lines.append(f"출력 디렉터리: {result['metadata']['output_directory']}")
        lines.append("")
        
        lines.append("📄 지문 목록:")
        lines.append("-" * 40)
        for passage in result['passages']:
            lines.append(f"• {passage['id']} ({passage['question_range']})")
            lines.append(f"  지시문: {passage['instruction'][:50]}...")
            lines.append(f"  글자 수: {len(passage['content'])}자")
            lines.append("")
        
        lines.append("❓ 문제 목록:")
        lines.append("-" * 40)
        for question in result['questions']:
            lines.append(f"• 문제 {question['question_number']} ({question['passage_id']})")
            lines.append(f"  유형: {question['metadata']['type']}")
            content_preview = question['stem'][:80].replace('\n', ' ')
            lines.append(f"  내용: {content_preview}...")
            lines.append("")
        
        lines.append("📊 통계:")
        lines.append("-" * 40)
        stats = result['statistics']
        
        lines.append("문제 유형별 분포:")
        for q_type, count in stats['question_types'].items():
            lines.append(f"  - {q_type}: {count}개")
        
        lines.append("\n지문별 문제 수:")
        for p_id, count in stats['questions_per_passage'].items():
            lines.append(f"  - {p_id}: {count}개")
        
        return "\n".join(lines)

# 편의 함수들
def quick_extract(pdf_path: str, title: str = None, output_dir: str = None) -> Dict:
    """빠른 추출 함수"""
    if title is None:
        title = os.path.splitext(os.path.basename(pdf_path))[0]
    
    extractor = SuneungExtractor(output_dir or "./extracted_content")
    return extractor.extract_from_pdf(pdf_path, title)

def extract_with_streamlit_compatibility(pdf_path: str) -> Tuple[List[Passage], List[Question], List[Dict]]:
    """Streamlit 앱과의 호환성을 위한 함수"""
    # 텍스트 추출
    raw_text = extract_text_from_pdf(pdf_path)
    
    # 이미지 추출
    img_results = extract_question_images(pdf_path, "./data/question_images")
    
    # 파싱
    passages, questions = parse_all_passages_and_questions(raw_text)
    
    return passages, questions, img_results

# 사용 예제
if __name__ == "__main__":
    # 방법 1: 간단한 사용
    result = quick_extract("sample_suneung.pdf", "2024년 수능 국어")
    
    # 방법 2: 세부 제어
    extractor = SuneungExtractor("./my_output")
    result = extractor.extract_from_pdf("sample_suneung.pdf", "수능 국어 기출")
    
    print("추출 완료!")