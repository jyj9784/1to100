import streamlit as st
import io
from tempfile import NamedTemporaryFile
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa
from pathlib import Path
from parser.text_extractor import extract_pdf_data
from parser.structured_parser import parse_passage_and_questions

# PDF 렌더링용 함수 (메모리 기반 처리)


def render_pdf(data):
    base_dir = Path(__file__).resolve().parent
    env = Environment(loader=FileSystemLoader(base_dir))
    template = env.get_template("template.html")
    html_out = template.render(**data)

    pdf_io = io.BytesIO()
    pisa.CreatePDF(html_out, dest=pdf_io)
    pdf_io.seek(0)
    return pdf_io, html_out


st.title("PDF 업로드 → JSON 편집 → PDF 출력")

pdf_file = st.file_uploader("PDF 업로드", type="pdf")
title = st.text_input("문제지 제목", "문제지")

if pdf_file and st.button("1️⃣ 텍스트 추출 및 파싱"):
    tmp = NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.write(pdf_file.read())
    tmp.flush()

    result = extract_pdf_data(tmp.name, "./data/question_images")
    raw_text = result["text"]
    img_results = result["images"]
    passages = result["passages"]
    # 첫 번째 지문 기준으로 파싱
    passage, questions = parse_passage_and_questions(raw_text)
    st.info("문항 이미지는 ./data/question_images 폴더에 저장됩니다.")
    st.json(img_results)
    st.session_state.img_results = img_results
    st.session_state.questions = questions

    st.session_state.parsed_data = {
        "title": title,
        "paragraphs": [passages[0] if passages else passage.content],
        "questions": [
            {"question": q.stem, "choices": q.choices or [], "answer": q.answer or ""}
            for q in questions if q.metadata.type == "multiple_choice"
        ],
        "oxQuestions": [
            {"question": q.stem, "answer": q.answer or ""}
            for q in questions if q.metadata.type == "ox"
        ]
    }
    st.success("✅ 파싱 완료! 아래에서 수정하고 PDF를 생성하세요.")
    st.json(st.session_state.parsed_data)

    if "img_results" in st.session_state and "questions" in st.session_state:
        st.subheader("🖼 문항 이미지 매칭")
        for r in st.session_state.img_results:
            num = int(r.get("number", 0)) if str(r.get("number", "")).isdigit() else None
            if num and num <= len(st.session_state.questions):
                qtext = st.session_state.questions[num-1].stem
            else:
                qtext = "매칭 실패"
            st.image(r["path"], width=250)
            st.write(f"{num if num else '?'}번: {qtext}")
            st.write(f"마지막 줄: {r['last_sentence']}")
            st.markdown("---")

if "parsed_data" in st.session_state:
    data = st.session_state.parsed_data

    st.subheader("📘 지문")
    data["paragraphs"][0] = st.text_area(
        "지문 내용", value=data["paragraphs"][0], height=150)

    st.subheader("📗 객관식 문제")
    for i, q in enumerate(data["questions"]):
        q["question"] = st.text_input(
            f"{i+1}. 질문", value=q["question"], key=f"q_{i}")
        for j, choice in enumerate(q["choices"]):
            q["choices"][j] = st.text_input(
                f" - 선택지 {j+1}", value=choice, key=f"q_{i}_c_{j}")

    st.subheader("📙 OX 문제")
    for i, ox in enumerate(data["oxQuestions"]):
        ox["question"] = st.text_input(
            f"OX {i+1}. 질문", value=ox["question"], key=f"ox_{i}")

    if st.button("📄 PDF 생성 및 다운로드"):
        pdf_io, html_preview = render_pdf(data)
        st.subheader("🖼 PDF 미리보기 (HTML)")
        st.components.v1.html(html_preview, height=1000, scrolling=True)
        st.download_button(
            "📥 PDF 다운로드",
            data=pdf_io,
            file_name=f"{data['title']}.pdf",
            mime="application/pdf"
        )
