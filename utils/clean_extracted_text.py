import argparse
import re

def clean_text(text: str) -> str:
    text = text.replace('\x0c', '').replace('\x01', '')  # 페이지 구분자, 특수문자 제거
    text = re.sub(r'\(cid:[0-9]+\)', '', text)  # (cid:xxx) 패턴 제거
    text = re.sub(r'([가-힣])\1+', r'\1', text)  # 한글 반복 제거 (현현존존 → 현존)
    text = re.sub(r'([^\s])\n([^\s])', r'\1 \2', text)   # 단어 사이 줄바꿈 제거
    text = re.sub(r'\n{2,}', '\n\n', text)               # 2줄 이상 연속 줄바꿈은 2줄로 통일
    return text.strip()

def main():
    parser = argparse.ArgumentParser(description="Extracted Text Cleaner")
    parser.add_argument('--input', required=True, help="Input text file path")
    parser.add_argument('--output', required=True, help="Output cleaned text file path")
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        text = f.read()

    cleaned = clean_text(text)

    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(cleaned)

    print(f"[INFO] 정리 완료: {args.output}")

if __name__ == "__main__":
    main()
