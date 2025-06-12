# pages/1_📄_모든_학급_시간표.py
import streamlit as st

st.set_page_config(layout="wide", page_title="전체 학급 시간표")

st.title("📄 모든 학급 시간표")

# st.session_state에 시간표 데이터가 있는지 확인
if 'timetable' not in st.session_state:
    st.warning("아직 생성된 시간표가 없습니다. 홈(app.py) 페이지로 돌아가 시간표를 먼저 생성해주세요.")
else:
    # 세션에서 데이터 불러오기
    timetable = st.session_state['timetable']
    settings = st.session_state['settings']
    vis_manager = st.session_state['vis_manager']

    st.info("학년별 탭을 클릭하여 전체 시간표를 확인하세요.")

    # 학년 선택 탭 생성
    grade_tabs = st.tabs([f"{grade}학년" for grade in settings['grades'].keys()])
    
    for i, grade in enumerate(settings['grades'].keys()):
        with grade_tabs[i]:
            # 각 학년별 모든 학급 시간표 표시
            vis_manager.display_all_class_timetables(
                timetable, grade, settings['grades'][grade])