# pages/3_📊_분석_정보.py
import streamlit as st
import pandas as pd

st.set_page_config(layout="wide", page_title="시간표 분석 정보")

st.title("📊 시간표 분석 정보")

# 세션 상태에 필요한 데이터가 있는지 먼저 확인
if 'timetable' not in st.session_state:
    st.warning("아직 생성된 시간표가 없습니다. 홈(app.py) 페이지로 돌아가 시간표를 먼저 생성해주세요.")
else:
    # 세션에서 분석에 필요한 모든 데이터와 객체를 가져옴
    validation_manager = st.session_state['validation_manager']
    timetable = st.session_state['timetable']
    teacher_schedule = st.session_state['teacher_schedule']
    teachers = st.session_state['teachers']
    selection_groups = st.session_state['selection_groups']

    st.subheader("1. 과목별 시수 충족 여부 검증")
    
    # 시수 완료 검증 및 표시 (가져온 데이터 사용)
    missing_hours = validation_manager.check_subject_hours_completed(
        timetable, teachers, selection_groups)
        
    if not missing_hours:
        st.success("✅ 모든 과목이 필요한 시수만큼 정확히 배치되었습니다.")
    else:
        st.error("⚠️ 일부 과목의 시수가 부족합니다!")
        missing_data = []
        for (subject, grade, cls), (required, assigned) in missing_hours.items():
            missing_data.append({
                "과목": subject, "학년": grade, "반": cls,
                "배정 시수": assigned, "필요 시수": required, "부족 시수": required - assigned
            })
        
        if missing_data:
            st.dataframe(pd.DataFrame(missing_data).sort_values(by="부족 시수", ascending=False), 
                         height=300, use_container_width=True)
    
    st.write("---")

    # 연속 수업 시간 분석 결과 표시
    st.subheader("2. 교사별 연속 수업 시간 분석")
    st.info(f"설정된 교사별 최대 연속 수업 시간은 **{st.session_state['settings']['max_consecutive_teaching_hours']}시간** 입니다.")
    
    consecutive_analysis = validation_manager.analyze_consecutive_teaching(teacher_schedule)
    
    consecutive_df = pd.DataFrame({
        "교사": list(consecutive_analysis.keys()),
        "최대 연속 수업 시간": list(consecutive_analysis.values())
    }).sort_values("최대 연속 수업 시간", ascending=False)
    
    st.dataframe(consecutive_df, height=400, use_container_width=True)