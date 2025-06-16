# 설치 방법

```bash
pip install -r requirements.txt
```

## 실행

```bash
streamlit run streamlit_pdf_flow.py
```

실행 후 웹 브라우저가 열립니다.

---

## 사용 흐름

1. **PDF 업로드**
2. **텍스트 추출 및 파싱** 버튼을 눌러 JSON 구조 확인
3. 화면에서 지문과 문제 내용을 자유롭게 수정
4. **PDF 생성 및 다운로드** 버튼을 눌러 편집한 결과를 PDF로 저장

파싱 과정에서는 PyMuPDF를 이용해 텍스트를 추출합니다. 추출된 내용은 문제별로 구조화되어 JSON 형식으로 표시됩니다.


##연결확인
0616연결확인