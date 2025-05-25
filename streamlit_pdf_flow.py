import streamlit as st
import json
import io
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from pathlib import Path

# PDF 렌더링용 함수 (메모리 기반 처리)


def render_pdf(data):
    base_dir = Path(__file__).resolve().parent
    env = Environment(loader=FileSystemLoader(base_dir))
    template = env.get_template("template.html")
    html_out = template.render(**data)

    pdf_io = io.BytesIO()
    HTML(string=html_out).write_pdf(target=pdf_io)
    pdf_io.seek(0)
    return pdf_io, html_out


st.title("📘 문제지 생성기: 복사 붙여넣기 기반")

title = st.text_input("문제지 제목", "문제지")
paragraph_text = st.text_area("1️⃣ 지문 입력", height=200)
question_text = st.text_area("2️⃣ 문제 입력 (질문 + 선택지를 그대로 붙여넣기)", height=400)

if st.button("📄 PDF 미리보기 및 다운로드"):
    data = {
        "title": title,
        "paragraphs": [paragraph_text],
        "questions": [
            {"question": block.strip()} for block in question_text.strip().split("\n\n") if block.strip()
        ],
        "oxQuestions": []
    }

    pdf_io, html_preview = render_pdf(data)

    st.subheader("🖼 PDF 미리보기 (HTML)")
    st.components.v1.html(html_preview, height=1000, scrolling=True)

    st.download_button(
        "📥 PDF 다운로드",
        data=pdf_io,
        file_name=f"{title}.pdf",
        mime="application/pdf"
    )
