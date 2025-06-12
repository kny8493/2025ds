# pages/2_👩‍🏫_교사별_시간표.py
import streamlit as st
import pandas as pd

st.set_page_config(layout="wide", page_title="교사별 시간표")

st.title("👩‍🏫 교사별 시간표")

if 'teacher_schedule' not in st.session_state:
    st.warning("아직 생성된 시간표가 없습니다. 홈(app.py) 페이지로 돌아가 시간표를 먼저 생성해주세요.")
else:
    teacher_schedule = st.session_state['teacher_schedule']
    vis_manager = st.session_state['vis_manager']
    validation_manager = st.session_state['validation_manager']

    teacher_views = vis_manager.generate_teacher_timetable_view(teacher_schedule)
    teacher_hours = validation_manager.calculate_teacher_hours(teacher_schedule)

    selected_teacher = st.selectbox(
        "확인하고 싶은 교사를 선택하세요:",
        list(teacher_views.keys())
    )

    if selected_teacher:
        st.subheader(f"👨‍🏫 {selected_teacher} 시간표 (주간 담당 시수: {teacher_hours[selected_teacher]}시간)")
        
        # 색상 적용하여 표시
        styled_df = teacher_views[selected_teacher].T.style.apply(vis_manager.color_subjects, axis=None)
        st.dataframe(styled_df, height=300, use_container_width=True)