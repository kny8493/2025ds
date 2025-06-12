import streamlit as st
import pandas as pd

# 데이터 처리 로직을 별도의 함수로 분리하여 코드를 깔끔하게 관리합니다.
def process_excel_data(uploaded_file):
    """
    업로드된 엑셀 파일을 읽고 파이썬 데이터 구조로 변환합니다.
    """
    try:
        # 업로드된 파일 객체를 바로 pandas로 읽을 수 있습니다.
        all_sheets = pd.read_excel(uploaded_file, sheet_name=None)

        # 각 시트 이름을 키로 사용하여 DataFrame에 접근
        df_settings = all_sheets['기본 설정']
        df_subjects = all_sheets['과목 정보']
        df_teachers = all_sheets['교사 및 배정']
        df_selection = all_sheets['선택과목 그룹']
        df_fixed = all_sheets['고정 시간표']
        
        # --- 데이터 형식 변환 ---

        # [기본 설정] 변환
        settings = {}
        for _, row in df_settings.iterrows():
            key, value = row['설정 항목'], row['설정 값']
            if key in ['운영 요일', '선택 그룹 이름']:
                settings[key] = str(value).split(',')
            elif key in ['요일별 교시 수', '학년별 학급 수']:
                settings[key] = {item.split(':')[0]: int(item.split(':')[1]) for item in str(value).split(',')}
            elif key == '최대 연속 수업 제한':
                settings[key] = int(value)
            else:
                settings[key] = value

        # [과목 정보] 변환
        subjects = {}
        for _, row in df_subjects.iterrows():
            subjects[row['과목명']] = {
                "hours": int(row['주간 시수']),
                "type": row['수업 유형'],
                "required": bool(row['필수 여부'])
            }

        # [고정 시간표] 변환
        fixed_slots = set()
        for _, row in df_fixed.iterrows():
            fixed_slots.add((int(row['학년']), row['요일'], int(row['교시']), row['활동명']))
            
        # [선택과목 그룹] 변환
        selection_groups = {}
        for _, row in df_selection.iterrows():
            grade = int(row['학년'])
            group_name = row['선택 그룹명']
            subject_name = row['포함 과목명']
            
            if grade not in selection_groups:
                selection_groups[grade] = {}
            if group_name not in selection_groups[grade]:
                selection_groups[grade][group_name] = []
            selection_groups[grade][group_name].append(subject_name)

        # [교사 및 배정] 변환
        teachers = {}
        for _, row in df_teachers.iterrows():
            teacher_name = row['교사명']
            subject_name = row['담당 과목명']
            
            if teacher_name not in teachers:
                teachers[teacher_name] = {"max": int(row['주간 최대 시수']), "subjects": []}
            
            classes_list = [int(c) for c in str(row['대상 반(들)']).split(',')]
            
            assignment = {
                "subject": subject_name,
                "grade": int(row['담당 학년']),
                "classes": classes_list,
                "hours": subjects[subject_name]['hours'],
                "required": subjects[subject_name]['required'],
                "group": {str(c): row['수업 그룹'] for c in classes_list}
            }
            teachers[teacher_name]['subjects'].append(assignment)
        
        # set은 json으로 바로 변환이 안되므로 list로 변경
        return settings, subjects, teachers, selection_groups, list(fixed_slots)

    except Exception as e:
        st.error(f"파일 처리 중 오류가 발생했습니다: {e}")
        return None

# --- Streamlit UI 구성 ---

st.set_page_config(page_title="시간표 데이터 변환기", layout="wide")

st.title("🏫 학교 시간표 데이터 변환기")
st.write("---")
st.write("시간표 편성을 위해 작성된 엑셀 파일을 업로드하면, 파이썬 프로그램이 사용할 수 있는 데이터 형식으로 변환해주는 도구입니다.")

# 1. 파일 업로드 위젯
uploaded_file = st.file_uploader(
    "여기에 엑셀 파일을 끌어다 놓거나 클릭하여 업로드하세요.",
    type=["xlsx"]
)

# 2. 파일이 업로드 되면 데이터 처리 및 결과 표시
if uploaded_file is not None:
    st.success(f"✔️ '{uploaded_file.name}' 파일이 성공적으로 업로드되었습니다.")
    
    with st.spinner("엑셀 파일을 읽고 데이터를 처리하는 중입니다... 잠시만 기다려주세요."):
        processed_data = process_excel_data(uploaded_file)

    if processed_data:
        st.balloons()
        st.header("🎉 데이터 변환 결과")
        
        settings, subjects, teachers, selection_groups, fixed_slots = processed_data
        
        # 탭을 사용하여 결과 보기
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["기본 설정", "과목 정보", "교사 및 배정", "선택과목 그룹", "고정 시간표"])

        with tab1:
            st.subheader("⚙️ 기본 설정 (Settings)")
            st.json(settings)

        with tab2:
            st.subheader("📚 과목 정보 (Subjects)")
            st.json(subjects)

        with tab3:
            st.subheader("👩‍🏫 교사 및 배정 (Teachers)")
            st.write(f"총 {len(teachers)}명의 교사 데이터가 처리되었습니다.")
            
            # 교사 선택 드롭다운
            teacher_to_show = st.selectbox("확인할 교사를 선택하세요:", options=list(teachers.keys()))
            if teacher_to_show:
                st.json(teachers[teacher_to_show])

        with tab4:
            st.subheader("🎨 선택과목 그룹 (Selection Groups)")
            st.json(selection_groups)

        with tab5:
            st.subheader("🗓️ 고정 시간표 (Fixed Slots)")
            st.json(fixed_slots)