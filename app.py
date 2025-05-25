import streamlit as st
import json
from tempfile import NamedTemporaryFile
from parser.text_extractor import extract_text_from_pdf
from parser.structured_parser import parse_passage_and_questions
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from pathlib import Path


def render_pdf(data):
    base_dir = Path(__file__).resolve().parent
    env = Environment(loader=FileSystemLoader(base_dir))
    template = env.get_template("template.html")
    html_out = template.render(**data)

    tmp_pdf = NamedTemporaryFile(delete=False, suffix=".pdf")
    HTML(string=html_out).write_pdf(tmp_pdf.name)
    return tmp_pdf.name


st.title("문제지 PDF 자동 추출 및 수정")

pdf_file = st.file_uploader("PDF 업로드", type="pdf")
title = st.text_input("문제지 제목", "산수유문제")

if pdf_file and st.button("1️⃣ 텍스트 추출 및 파싱"):
    tmp = NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.write(pdf_file.read())
    tmp.flush()

    raw_text = extract_text_from_pdf(tmp.name)
    passage, questions = parse_passage_and_questions(raw_text)

    st.session_state.parsed_data = {
        "title": title,
        "paragraphs": [passage.content],
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
        pdf_path = render_pdf(data)
        with open(pdf_path, "rb") as f:
            st.download_button(
                "📥 PDF 다운로드", f, file_name=f"{data['title']}.pdf", mime="application/pdf")
