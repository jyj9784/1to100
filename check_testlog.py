# check_testlog.py

import os
import re

TARGET_FOLDER = "./data/testlog"
BAD_PATTERNS = [
    r"현존재쌤",    # 반복 텍스트 패턴
    r"\(cid:127\)", # 깨진 문자 코드
    r"[\[\(]\s*[\]\)]", # 빈 괄호 "()", "[]" 등
    r"([가-힣])\1{2,}", # 한글 2자 이상 반복 (ex: 현현존존)
]


def check_file(filepath):
    issues = []
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        for pattern in BAD_PATTERNS:
            matches = list(re.finditer(pattern, content))
            for match in matches:
                issues.append((match.start(), match.group()))
    return issues


def main():
    print(f"[INFO] 테스트 로그 폴더 검사 시작: {TARGET_FOLDER}")
    files = [f for f in os.listdir(TARGET_FOLDER) if f.endswith(".txt")]

    for file in files:
        path = os.path.join(TARGET_FOLDER, file)
        issues = check_file(path)

        if issues:
            print(f"\n[WARNING] 문제 발견: {file}")
            for pos, text in issues:
                print(f" - 위치 {pos}: \"{text}\"")
        else:
            print(f"[OK] 이상 없음: {file}")

    print("\n✅ 검사 완료!")


if __name__ == "__main__":
    main()
