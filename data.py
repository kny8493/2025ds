
# -----------------------------
# 설정 데이터
# -----------------------------
settings = {
    "days": ["월", "화", "수", "목", "금"],
    "periods_per_day_by_day": {"월": 6, "화": 7, "수": 6, "목": 7, "금": 6},
    "grades": {1: 3, 2: 3, 3: 3},
    "max_consecutive_teaching_hours": 4,  # 연속 수업 시간 제한
    "selection_group_names": ["선택A", "선택B", "선택C","선택D"]  # 선택 그룹 이름 추가
}

# -----------------------------
# 과목 데이터 (본반/선택 구분 포함)
# -----------------------------
subjects = {
    "공통국어":      {"hours": 4, "type": "본반", "required": True},
    "공통수학":      {"hours": 4, "type": "본반", "required": True},
    "공통영어":      {"hours": 4, "type": "본반", "required": True},
    "한국사":        {"hours": 3, "type": "본반", "required": True},
    "통합사회":      {"hours": 3, "type": "본반", "required": True},
    "통합과학":      {"hours": 3, "type": "본반", "required": True},
    "과학탐구실험":  {"hours": 1, "type": "본반", "required": True},
    "체육":          {"hours": 2, "type": "본반", "required": True},
    "음악+미술":     {"hours": 3, "type": "본반", "required": True},
    "한문+정보":     {"hours": 2, "type": "본반", "required": True},
    "진로":          {"hours": 1, "type": "본반", "required": True},

    "문학":         {"hours": 4, "type": "본반", "required": True},
    "수학Ⅰ":       {"hours": 4, "type": "본반", "required": True},
    "확률과 통계": {"hours": 2, "type": "본반", "required": True},
    "영어Ⅰ":       {"hours": 4, "type": "본반", "required": True},
    "운동과 건강": {"hours": 2, "type": "본반", "required": True},
    "교양한문":     {"hours": 1, "type": "본반", "required": True},
    "진로":          {"hours": 1, "type": "본반", "required": True},
    
    # 2학년 선택과목 그룹 정보 추가
    "중국어Ⅰ":      {"hours": 3, "type": "선택", "required": True},
    "물리학Ⅰ":      {"hours": 3, "type": "선택", "required": True},
    "화학Ⅰ":        {"hours": 3, "type": "선택", "required": True},
    "생명과학Ⅰ":    {"hours": 3, "type": "선택", "required": True},
    "지구과학Ⅰ":    {"hours": 3, "type": "선택", "required": True},
    "윤리와 사상":   {"hours": 3, "type": "선택", "required": True},
    "한국지리":      {"hours": 3, "type": "선택", "required": True},
    "사회·문화":     {"hours": 3, "type": "선택", "required": True},
    "프로그래밍/Python": {"hours": 3, "type": "선택", "required": True}
}

# -----------------------------
# 교사 데이터
# -----------------------------
teachers = {
    # 국어 교사 분할 예시
    "국어교사1": {
        "max": 15,  # 시수 제한 (18->15)
        "subjects": [
            {"subject": "문학", "grade": 2, "classes": [1, 2], "hours": 4, "required": True,
             "group": {"1": "본반", "2": "본반"}}
        ]
    },
    "국어교사2": {
        "max": 15,  # 시수 제한 (18->15)
        "subjects": [
            {"subject": "문학", "grade": 2, "classes": [3], "hours": 4, "required": True,
             "group": {"3": "본반"}},
            {"subject": "교양한문", "grade": 2, "classes": [1, 2, 3], "hours": 1, "required": True,
             "group": {"1": "본반", "2": "본반", "3": "본반"}},
        ]
    },
    "국어교사3": {
        "max": 15,  # 시수 제한 (18->15)
        "subjects": [
            {"subject": "공통국어", "grade": 1, "classes": [1, 2, 3], "hours": 4, "required": True,
             "group": {"1": "본반", "2": "본반", "3": "본반"}}
        ]
    },

    # 수학 교사 분할
    "수학교사1": {
        "max": 15,  # 시수 제한 (18->15)
        "subjects": [
            {"subject": "공통수학", "grade": 1, "classes": [1, 2], "hours": 4, "required": True,
             "group": {"1": "본반", "2": "본반"}}
        ]
    },
    "수학교사2": {
        "max": 15,  # 시수 제한 (18->15)
        "subjects": [
            {"subject": "공통수학", "grade": 1, "classes": [3], "hours": 4, "required": True,
             "group": {"3": "본반"}},
            {"subject": "수학Ⅰ", "grade": 2, "classes": [1, 2, 3], "hours": 4, "required": True,
             "group": {"1": "본반", "2": "본반", "3": "본반"}}
        ]
    },
    "수학교사3": {
        "max": 15,  # 시수 제한 (18->15)
        "subjects": [
            {"subject": "확률과 통계", "grade": 2, "classes": [1, 2, 3], "hours": 2, "required": True,
             "group": {"1": "본반", "2": "본반", "3": "본반"}}
        ]
    },

    # 영어 교사 분할
    "영어교사1": {
        "max": 15,  # 시수 제한 (18->15)
        "subjects": [
            {"subject": "공통영어", "grade": 1, "classes": [1, 2], "hours": 4, "required": True,
             "group": {"1": "본반", "2": "본반"}}
        ]
    },
    "영어교사2": {
        "max": 15,  # 시수 제한 (18->15)
        "subjects": [
            {"subject": "공통영어", "grade": 1, "classes": [3], "hours": 4, "required": True,
             "group": {"3": "본반"}}
        ]
    },
    "영어교사3": {
        "max": 15,  # 시수 제한 (18->15)
        "subjects": [
            {"subject": "영어Ⅰ", "grade": 2, "classes": [1, 2, 3], "hours": 4, "required": True,
             "group": {"1": "본반", "2": "본반", "3": "본반"}}
        ]
    },

    # 역사 교사
    "역사교사1": {
        "max": 15,  # 시수 제한 (18->15)
        "subjects": [
            {"subject": "한국사", "grade": 1, "classes": [1, 2, 3], "hours": 3, "required": True,
             "group": {"1": "본반", "2": "본반", "3": "본반"}}
        ]
    },

    # 사회 교사
    "사회교사1": {
        "max": 15,  # 시수 제한 (18->15)
        "subjects": [
            {"subject": "통합사회", "grade": 1, "classes": [1, 2, 3], "hours": 3, "required": True,
             "group": {"1": "본반", "2": "본반", "3": "본반"}},
            {"subject": "진로", "grade": 2, "classes": [1, 2, 3], "hours": 1, "required": True,
             "group": {"1": "본반", "2": "본반", "3": "본반"}}
        ]
    },

    # 선택과목 교사들 - 여러 학급을 동시에 담당하므로 정확한 시수 계산은 어려움
    # 2학년 선택과목 담당 교사 - 선택그룹 지정
    "윤리사회교사": {
        "max": 18,  # 시수 제한 유지 (두 과목, 여러 그룹 담당)
        "subjects": [
            {"subject": "윤리와 사상", "grade": 2, "classes": [1, 2, 3], "hours": 3, "required": True,
             "group": {"1": "선택A", "2": "선택A", "3": "선택A"}},
            {"subject": "윤리와 사상", "grade": 2, "classes": [1, 2, 3], "hours": 3, "required": True,
             "group": {"1": "선택D", "2": "선택D", "3": "선택D"}}
        ]
    },
    "사회문화교사": {
        "max": 18,  # 시수 제한 유지 (두 과목, 여러 그룹 담당)
        "subjects": [
            {"subject": "사회·문화", "grade": 2, "classes": [1, 2, 3], "hours": 3, "required": True,
             "group": {"1": "선택C", "2": "선택C", "3": "선택C"}},
            {"subject": "사회·문화", "grade": 2, "classes": [1, 2, 3], "hours": 3, "required": True,
             "group": {"1": "선택D", "2": "선택D", "3": "선택D"}}
        ]
    },
    "지리교사": {
        "max": 15,  # 시수 제한 (18->15)
        "subjects": [
            {"subject": "한국지리", "grade": 2, "classes": [1, 2, 3], "hours": 3, "required": True,
             "group": {"1": "선택B", "2": "선택B", "3": "선택B"}},
            {"subject": "진로", "grade": 1, "classes": [1, 2, 3], "hours": 1, "required": True,
             "group": {"1": "본반", "2": "본반", "3": "본반"}}
        ]
    },
    "물리교사": {
        "max": 15,  # 시수 제한 (18->15)
        "subjects": [
            {"subject": "물리학Ⅰ", "grade": 2, "classes": [1, 2, 3], "hours": 3, "required": True,
             "group": {"1": "선택A", "2": "선택A", "3": "선택A"}}
        ]
    },
    "화학교사": {
        "max": 15,  # 시수 제한 (18->15)
        "subjects": [
            {"subject": "화학Ⅰ", "grade": 2, "classes": [1, 2, 3], "hours": 3, "required": True,
             "group": {"1": "선택B", "2": "선택B", "3": "선택B"}}
        ]
    },
    "생명과학교사": {
        "max": 18,  # 시수 제한 유지 (두 과목, 여러 그룹 담당)
        "subjects": [
            {"subject": "생명과학Ⅰ", "grade": 2, "classes": [1, 2, 3], "hours": 3, "required": True,
             "group": {"1": "선택B", "2": "선택B", "3": "선택B"}},
            {"subject": "생명과학Ⅰ", "grade": 2, "classes": [1, 2, 3], "hours": 3, "required": True,
             "group": {"1": "선택D", "2": "선택D", "3": "선택D"}}
        ]
    },
    "지구과학교사": {
        "max": 15,  # 시수 제한 (18->15)
        "subjects": [
            {"subject": "지구과학Ⅰ", "grade": 2, "classes": [1, 2, 3], "hours": 3, "required": True,
             "group": {"1": "선택C", "2": "선택C", "3": "선택C"}}
        ]
    },
    "외국어교사": {
        "max": 15,  # 시수 제한 (18->15)
        "subjects": [
            {"subject": "중국어Ⅰ", "grade": 2, "classes": [1, 2, 3], "hours": 3, "required": True,
             "group": {"1": "선택A", "2": "선택A", "3": "선택A"}}
        ]
    },
    "정보교사": {
        "max": 15,  # 시수 제한 (18->15)
        "subjects": [
            {"subject": "프로그래밍/Python", "grade": 2, "classes": [1, 2, 3], "hours": 3, "required": True,
             "group": {"1": "선택B", "2": "선택B", "3": "선택B"}},
            {"subject": "한문+정보", "grade": 1, "classes": [1, 2, 3], "hours": 2, "required": True,
             "group": {"1": "본반", "2": "본반", "3": "본반"}}
        ]
    },
    
    # 과학 교사 
    "과학교사1": {
        "max": 15,  # 시수 제한 (18->15)
        "subjects": [
            {"subject": "통합과학", "grade": 1, "classes": [1, 2, 3], "hours": 3, "required": True,
             "group": {"1": "본반", "2": "본반", "3": "본반"}}
        ]
    },
    "과학교사2": {
        "max": 15,  # 시수 제한 (18->15)
        "subjects": [
            {"subject": "과학탐구실험", "grade": 1, "classes": [1, 2, 3], "hours": 1, "required": True,
             "group": {"1": "본반", "2": "본반", "3": "본반"}}
        ]
    },

    # 체육 교사
    "체육교사1": {
        "max": 15,  # 시수 제한 (18->15)
        "subjects": [
            {"subject": "체육", "grade": 1, "classes": [1, 2, 3], "hours": 2, "required": True,
             "group": {"1": "본반", "2": "본반", "3": "본반"}},
            {"subject": "운동과 건강", "grade": 2, "classes": [1, 2, 3], "hours": 2, "required": True,
             "group": {"1": "본반", "2": "본반", "3": "본반"}}
        ]
    },

    # 예술 교사 
    "예술교사1": {
        "max": 15,  # 시수 제한 (18->15)
        "subjects": [
            {"subject": "음악+미술", "grade": 1, "classes": [1, 2, 3], "hours": 3, "required": True,
             "group": {"1": "본반", "2": "본반", "3": "본반"}}
        ]
    },
}
# -----------------------------
# 선택 그룹 정보
# -----------------------------
# 2학년 선택 과목 그룹 정의
selection_groups = {
    2: {  # 2학년
        "선택A": ["윤리와 사상", "물리학Ⅰ", "중국어Ⅰ", "일본어Ⅰ"],  # A그룹 과목들
        "선택B": ["화학Ⅰ", "생명과학Ⅰ", "한국지리", "프로그래밍/Python"],  # B그룹 과목들
        "선택C": ["정치와 법", "사회·문화", "지구과학Ⅰ"],  # C그룹 과목들
        "선택D": ["윤리와 사상", "생명과학Ⅰ", "사회·문화"]  # D그룹 과목들 추가
    }
}


fixed_slots = set()
for grade in settings["grades"]:
    for cls in range(1, settings["grades"][grade] + 1):
        fixed_slots.add((grade, cls, "금", 5, "창체"))
        fixed_slots.add((grade, cls, "금", 6, "창체"))