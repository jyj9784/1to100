import streamlit as st
import io
from tempfile import NamedTemporaryFile
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa
from pathlib import Path
from parser.text_extractor import extract_text_from_pdf, extract_question_images
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

if pdf_file:
    import base64
    b64 = base64.b64encode(pdf_file.getvalue()).decode("utf-8")
    st.subheader("📑 업로드한 PDF 미리보기")
    st.components.v1.html(
        f'<embed src="data:application/pdf;base64,{b64}" width="700" height="500" type="application/pdf">',
        height=500,
    )
    pdf_file.seek(0)
title = st.text_input("문제지 제목", "문제지")

if pdf_file and st.button("1️⃣ 텍스트 추출 및 파싱"):
    tmp = NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.write(pdf_file.read())
    tmp.flush()

    raw_text = extract_text_from_pdf(tmp.name)
    img_results = extract_question_images(tmp.name, "./data/question_images")
    passage, questions = parse_passage_and_questions(raw_text)
    st.info("문항 이미지는 ./data/question_images 폴더에 저장됩니다.")
    st.json(img_results)

    img_map = {res["number"]: res["path"] for res in img_results if res.get("number")}

    st.session_state.parsed_data = {
        "title": title,
        "paragraphs": [passage.content],
        "questions": [
            {
                "number": q.number,
                "question": q.stem,
                "choices": q.choices or [],
                "answer": q.answer or "",
                "image": img_map.get(q.number)
            }
            for q in questions if q.metadata.type == "multiple_choice"
        ],
        "oxQuestions": [
            {
                "number": q.number,
                "question": q.stem,
                "answer": q.answer or "",
                "image": img_map.get(q.number)
            }
            for q in questions if q.metadata.type == "ox"
        ]
    }
    st.success("✅ 파싱 완료! 아래에서 수정하고 PDF를 생성하세요.")
    st.json(st.session_state.parsed_data)

if "parsed_data" in st.session_state:
    data = st.session_state.parsed_data

    st.subheader("📘 지문")
    data["paragraphs"][0] = st.text_area(
        "지문 내용", value=data["paragraphs"][0], height=150)

    st.subheader("📗 객관식 문제")
    for i, q in enumerate(data["questions"]):
        q["question"] = st.text_input(
            f"{i+1}. 질문", value=q["question"], key=f"q_{i}")
        if q.get("image"):
            st.image(q["image"], caption=f"문항 이미지 {q['number']}")
        for j, choice in enumerate(q["choices"]):
            q["choices"][j] = st.text_input(
                f" - 선택지 {j+1}", value=choice, key=f"q_{i}_c_{j}")

    st.subheader("📙 OX 문제")
    for i, ox in enumerate(data["oxQuestions"]):
        ox["question"] = st.text_input(
            f"OX {i+1}. 질문", value=ox["question"], key=f"ox_{i}")
        if ox.get("image"):
            st.image(ox["image"], caption=f"OX 이미지 {ox['number']}")

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
