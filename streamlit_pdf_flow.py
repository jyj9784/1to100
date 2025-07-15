import streamlit as st
import io
import json
import os
from tempfile import NamedTemporaryFile
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa
from pathlib import Path
from parser.structured_parser import parse_all_passages_and_questions, extract_question_image, extract_passage_image, extract_choices_image
from parser.text_extractor import extract_text_from_pdf

st.set_page_config(layout="wide")

st.title("📚 수능국어 지문-문제 통합 추출기 (이미지 포함)")
st.caption("PDF를 업로드하면 지문과 문제를 자동으로 분리하고, 각 영역을 이미지로 함께 보여줍니다.")

pdf_file = st.file_uploader("PDF 파일 업로드", type="pdf")
title = st.text_input("문제집 제목", "수능국어 문제집")

if pdf_file and st.button("🔍 지문-문제 및 이미지 추출하기"):
    with st.spinner("PDF 분석 및 이미지 추출 중... 잠시만 기다려주세요."):
        tmp = NamedTemporaryFile(delete=False, suffix=".pdf")
        tmp.write(pdf_file.read())
        tmp.flush()
        
        # 1단계: 텍스트 파싱
        raw_text = extract_text_from_pdf(tmp.name)
        passages, questions = parse_all_passages_and_questions(raw_text)

        # 2단계: 문제 및 선택지 이미지 추출 및 연결
        output_dir = os.path.join("data", "output", title)
        for q in questions:
            q.image_path = extract_question_image(tmp.name, q, output_dir)
            q.choices_image_path = extract_choices_image(tmp.name, q, output_dir)
        
        # 3단계: 지문 이미지 추출 및 연결
        for p in passages:
            p.image_paths = extract_passage_image(tmp.name, p, output_dir)

        sets = []
        for i, p in enumerate(passages):
            set_data = {
                "set_number": i + 1,
                "passage": p.to_dict(),
                "questions": [q.to_dict() for q in questions if q.passage_id == p.passage_id]
            }
            sets.append(set_data)
        
        st.session_state.extracted_data = sets
        st.session_state.title = title
        
        st.success(f"✅ {len(passages)}개의 지문과 {len(questions)}개의 문제를 추출했습니다!")

if "extracted_data" in st.session_state:
    with st.sidebar:
        st.header("📊 통계")
        total_passages = len(st.session_state.extracted_data)
        total_questions = sum(len(s['questions']) for s in st.session_state.extracted_data)
        st.metric("지문 수", total_passages)
        st.metric("전체 문제 수", total_questions)

    st.header("📝 추출된 내용 편집")
    
    data = st.session_state.extracted_data
    
    for i, set_data in enumerate(data):
        passage_info = set_data['passage']
        expander_title = f"📖 지문 {passage_info.get('question_range') or set_data['set_number']}"
        with st.expander(expander_title, expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📄 추출된 텍스트")
                set_data['passage']['content'] = st.text_area(
                    "지문 내용",
                    value=passage_info['content'],
                    height=300,
                    key=f"passage_{i}"
                )
            with col2:
                st.subheader("🖼️ 지문 이미지")
                if passage_info.get('image_paths'):
                    for img_path in passage_info['image_paths']:
                        if os.path.exists(img_path):
                            st.image(img_path, use_container_width=True)
                        else:
                            st.warning(f"이미지 파일을 찾을 수 없습니다: {img_path}")
                else:
                    st.warning("지문 이미지를 찾을 수 없습니다.")
            
            st.markdown("<hr>", unsafe_allow_html=True)
            st.subheader("❓ 문제")
            
            for q_idx, q in enumerate(set_data['questions']):
                st.markdown(f"**문제 {q['question_number']}**")
                
                # 문제 본문 (텍스트 + 이미지)
                st.subheader("문제 본문")
                q_stem_col1, q_stem_col2 = st.columns(2)
                with q_stem_col1:
                    q['stem'] = st.text_area(
                        f"문제 {q['question_number']} 내용",
                        value=q['stem'],
                        height=250,
                        key=f"q_stem_{i}_{q_idx}"
                    )
                with q_stem_col2:
                    if q.get('image_path') and os.path.exists(q['image_path']):
                        st.image(q['image_path'], use_container_width=True)
                    else:
                        st.warning("문제 이미지를 찾을 수 없습니다.")
                
                # 선택지 (텍스트 + 이미지)
                if q['choices']:
                    st.subheader("선택지")
                    q_choices_col1, q_choices_col2 = st.columns(2)
                    with q_choices_col1:
                        for c_idx, choice in enumerate(q['choices']):
                            q['choices'][c_idx] = st.text_input(
                                f"선택지 {c_idx + 1}",
                                value=choice,
                                key=f"choice_{i}_{q_idx}_{c_idx}"
                            )
                    with q_choices_col2:
                        if q.get('choices_image_path') and os.path.exists(q['choices_image_path']):
                            st.image(q['choices_image_path'], use_container_width=True)
                        else:
                            st.warning("선택지 이미지를 찾을 수 없습니다.")
                st.markdown("<br>", unsafe_allow_html=True)

    if st.button("💾 변경사항 저장 (JSON)"):
        output_path = os.path.join("data", "output", st.session_state.title, f"edited_{st.session_state.title}.json")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        st.success(f"저장 완료: {output_path}")