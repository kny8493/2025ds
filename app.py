# app.py
import streamlit as st
import pandas as pd
from algorithm import TimetableManager, ValidationManager
from ui import VisualizationManager

# --- 데이터 처리 함수 ---
# process_excel_data 함수를 아래 코드로 교체해주세요.
# app.py 파일의 process_excel_data 함수를 아래 코드로 전체 교체하세요.

# app.py 파일의 process_excel_data 함수를 아래 코드로 전체 교체하세요.

# app.py 파일의 process_excel_data 함수를 아래 코드로 전체 교체하세요.

def process_excel_data(uploaded_file):
    """
    업로드된 엑셀 파일을 읽고 필요한 파이썬 데이터 구조로 변환합니다.
    (각 시트의 주요 컬럼이 비어있으면 읽기를 중단하는 기능 추가)
    """
    try:
        # 1. header=None 옵션으로 헤더 없이 순수 데이터만 먼저 읽어옵니다.
        all_sheets_raw = pd.read_excel(uploaded_file, sheet_name=None, header=None)

        # 2. 읽어온 각 시트를 순회하며 헤더를 수동으로 설정합니다.
        all_sheets = {}
        for sheet_name, df_raw in all_sheets_raw.items():
            # 빈 시트일 경우 건너뛰기
            if df_raw.empty:
                continue
            new_header = df_raw.iloc[0]
            df_new = df_raw[1:]
            df_new.columns = new_header
            all_sheets[sheet_name] = df_new.reset_index(drop=True)
        
        # 3. 정리된 데이터를 사용하여 이전과 동일한 로직을 수행합니다.
        df_settings = all_sheets.get('기본 설정')
        df_subjects = all_sheets.get('과목 정보')
        df_teachers = all_sheets.get('교사 및 배정')
        df_selection = all_sheets.get('선택과목 그룹')
        df_fixed = all_sheets.get('고정 시간표')
        
        settings, subjects, teachers, selection_groups, fixed_slots = {}, {}, {}, {}, set()

        # '기본 설정' 시트 처리
        if df_settings is not None:
            for _, row in df_settings.iterrows():
                # [수정] '설정 항목'이 비어있으면 데이터 끝으로 간주하고 중단
                key_val = row['설정 항목']
                if pd.isna(key_val) or str(key_val).strip() == '':
                    break
                
                key, value = key_val, row['설정 값']
                if key in ['운영 요일', '선택 그룹 이름']: settings[key] = str(value).split(',')
                elif key in ['요일별 교시 수', '학년별 학급 수']: settings[key] = {item.split(':')[0]: int(item.split(':')[1]) for item in str(value).split(',')}
                elif key == '최대 연속 수업 제한': settings[key] = int(value)
                else: settings[key] = value

        # '과목 정보' 시트 처리
        if df_subjects is not None:
            for _, row in df_subjects.iterrows():
                # [수정] '과목명'이 비어있으면 데이터 끝으로 간주하고 중단
                key_val = row['과목명']
                if pd.isna(key_val) or str(key_val).strip() == '':
                    break
                subjects[key_val] = {"hours": int(row['주간 시수']), "type": row['수업 유형'], "required": bool(row['필수 여부'])}

        # '고정 시간표' 시트 처리
        if df_fixed is not None:
            for _, row in df_fixed.iterrows():
                # [수정] '학년'이 비어있으면 데이터 끝으로 간주하고 중단
                key_val = row['학년']
                if pd.isna(key_val) or str(key_val).strip() == '':
                    break
                fixed_slots.add((int(key_val), row['요일'], int(row['교시']), row['활동명']))
            
        # '선택과목 그룹' 시트 처리
        if df_selection is not None:
            for _, row in df_selection.iterrows():
                # [수정] '학년'이 비어있으면 데이터 끝으로 간주하고 중단
                key_val = row['학년']
                if pd.isna(key_val) or str(key_val).strip() == '':
                    break
                grade, group_name, subject_name = int(key_val), row['선택 그룹명'], row['포함 과목명']
                if grade not in selection_groups: selection_groups[grade] = {}
                if group_name not in selection_groups[grade]: selection_groups[grade][group_name] = []
                selection_groups[grade][group_name].append(subject_name)

        # '교사 및 배정' 시트 처리
        if df_teachers is not None:
            for _, row in df_teachers.iterrows():
                # [수정] '교사명'이 비어있으면 데이터 끝으로 간주하고 중단
                key_val = row['교사명']
                if pd.isna(key_val) or str(key_val).strip() == '':
                    break
                teacher_name, subject_name = key_val, row['담당 과목명']
                if teacher_name not in teachers: teachers[teacher_name] = {"max": int(row['주간 최대 시수']), "subjects": []}
                classes_list = [int(c) for c in str(row['대상 반(들)']).split(',')]
                assignment = {"subject": subject_name, "grade": int(row['담당 학년']), "classes": classes_list, "hours": subjects[subject_name]['hours'], "required": subjects[subject_name]['required'], "group": {str(c): row['수업 그룹'] for c in classes_list}}
                teachers[teacher_name]['subjects'].append(assignment)
        
        return settings, subjects, teachers, selection_groups, list(fixed_slots)

    except Exception as e:
        st.error(f"엑셀 파일 처리 중 오류가 발생했습니다: {e}")
        st.error("엑셀 파일의 시트 이름과 내용이 올바른지 다시 확인해주세요.")
        return None
    
        
# --- 페이지 기본 설정 ---
st.set_page_config(
    page_title="시간표 자동 제작",
    page_icon="🏫",
    layout="wide"
)

# --- 메인 UI ---
st.title("🏫 고등학교 시간표 자동 제작")
st.markdown("""
이 프로그램은 설정된 데이터를 기반으로 최적의 시간표를 생성합니다.
아래에서 엑셀 파일을 업로드한 후, 시간표 생성을 진행하세요.
""")
st.write("---")

# --- 1단계: 엑셀 파일 업로드 ---
st.header("1. 데이터 파일 업로드")
uploaded_file = st.file_uploader(
    "시간표 설정이 담긴 엑셀 파일을 업로드하세요.",
    type=["xlsx"]
)

# 파일이 업로드 되면, 데이터를 처리하고 세션에 저장
if uploaded_file:
    with st.spinner("엑셀 파일을 읽고 데이터를 설정하는 중입니다..."):
        processed_data = process_excel_data(uploaded_file)
    
    if processed_data:
        st.success("✅ 엑셀 파일 로드 및 데이터 설정 완료!")
        # 처리된 데이터를 세션 상태에 저장
        st.session_state['data_loaded'] = True
        st.session_state['settings'] = processed_data[0]
        st.session_state['subjects'] = processed_data[1]
        st.session_state['teachers'] = processed_data[2]
        st.session_state['selection_groups'] = processed_data[3]
        st.session_state['fixed_slots'] = processed_data[4]

st.write("---")

# --- 2단계: 시간표 생성 ---
st.header("2. 시간표 생성 실행")

# 데이터가 로드되었을 때만 시간표 생성 버튼을 활성화
if st.session_state.get('data_loaded', False):
    if st.button("🚀 시간표 생성하기", use_container_width=True, type="primary"):
        with st.spinner("알고리즘 실행 중... 최적의 시간표를 찾고 있습니다. (약 1분 소요)"):
            # 세션에서 데이터 가져오기
            settings = st.session_state['settings']
            subjects = st.session_state['subjects']
            teachers = st.session_state['teachers']
            selection_groups = st.session_state['selection_groups']
            fixed_slots = st.session_state['fixed_slots']

            # 매니저 클래스 인스턴스화
            timetable_manager = TimetableManager(settings, teachers, subjects, selection_groups, fixed_slots)
            validation_manager = ValidationManager(settings)
            vis_manager = VisualizationManager(settings)
            
            # 시간표 생성 및 후처리
            timetable, teacher_schedule = timetable_manager.create_timetable()
            timetable = timetable_manager.post_process_timetable(timetable, fill_empty=True)
            
            # 다른 페이지에서 사용할 수 있도록 모든 결과를 세션에 저장
            st.session_state['timetable_generated'] = True
            st.session_state['timetable'] = timetable
            st.session_state['teacher_schedule'] = teacher_schedule
            st.session_state['validation_manager'] = validation_manager
            st.session_state['vis_manager'] = vis_manager
            
        st.success("✅ 시간표 생성 완료! 왼쪽 메뉴에서 결과를 확인하세요.")
        st.balloons()
else:
    st.info("먼저 엑셀 파일을 업로드해주세요. 파일이 업로드되면 시간표 생성 버튼이 나타납니다.")