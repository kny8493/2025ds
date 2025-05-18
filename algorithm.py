import pandas as pd
import random
import heapq  # 우선순위 큐를 위한 모듈
from collections import defaultdict

# -----------------------------
# 데이터 처리 모듈
# -----------------------------
class DataManager:
    """
    데이터 처리를 담당하는 클래스
    입력된 교사/과목 정보를 시간표 생성에 적합한 형태로 변환합니다.
    """
    
    @staticmethod
    def generate_lesson_blocks(teachers):
        """
        교사 정보로부터 수업 블록 생성
        
        각 교사가 담당하는 과목, 학년, 반, 시수 등의 정보를 개별 수업 블록으로 변환합니다.
        예: "김 교사가 1학년 2반에서 영어를 주 3시간 가르친다"를 하나의 블록으로 생성
        
        Args:
            teachers: 교사 정보 딕셔너리 {교사명: {정보}}
            
        Returns:
            수업 블록 리스트
        """
        blocks = []  # 결과를 저장할 빈 리스트
        
        # 각 교사에 대해 처리
        for teacher, info in teachers.items():
            # 교사가 담당하는 각 과목 정보 처리
            for subject_info in info["subjects"]:
                # 해당 과목을 수강하는 각 반에 대해 처리
                for class_num in subject_info["classes"]:
                    # 해당 반의 그룹 정보 가져오기 (문자열 또는 숫자 형태로 저장된 키 처리)
                    group = subject_info["group"].get(str(class_num)) or subject_info["group"].get(class_num)
                    
                    # 새로운 수업 블록 생성 및 추가
                    blocks.append({
                        "teacher": teacher,              # 담당 교사명
                        "subject": subject_info["subject"], # 과목명
                        "grade": subject_info["grade"],    # 학년
                        "class": class_num,              # 반
                        "group": group,                  # 그룹 (예: 일반/선택/선택A)
                        "hours": subject_info["hours"],    # 주당 수업 시수
                        "required": subject_info["required"] # 필수 과목 여부
                    })
        
        return blocks
    
    @staticmethod
    def group_lesson_blocks(blocks):
        """
        수업 블록을 그룹화
        
        유사한 특성(동일 교사, 과목, 학년, 그룹)을 가진 블록들을 모아서 효율적으로 관리합니다.
        예: "김 교사의 1학년 영어 수업들"을 하나의 그룹으로 묶음
        
        Args:
            blocks: 수업 블록 리스트
            
        Returns:
            그룹화된 수업 블록 리스트
        """
        # 기본값이 설정된 딕셔너리 생성
        grouped = defaultdict(lambda: {
            "teacher": None, "subject": None, "grade": None,
            "group": None, "hours": None, "required": None, "classes": []
        })
        
        # 각 블록을 그룹화
        for block in blocks:
            # 교사, 과목, 학년, 그룹을 키로 사용하여 동일한 블록 그룹화
            key = (block['teacher'], block['subject'], block['grade'], block['group'])
            
            # 처음 나오는 그룹이면 기본 정보 설정
            if not grouped[key]['classes']:
                grouped[key].update({
                    'teacher': block['teacher'],
                    'subject': block['subject'],
                    'grade': block['grade'],
                    'group': block['group'],
                    'hours': block['hours'],
                    'required': block['required']
                })
            
            # 반 목록에 현재 블록의 반 추가
            grouped[key]['classes'].append(block['class'])
        
        return list(grouped.values())
    
    @staticmethod
    def get_choice_groups(grouped_blocks):
        """
        일반 선택 그룹 블록 추출
        
        '선택' 그룹으로 지정된 과목 블록들을 추출합니다.
        예: 학생들이 선택할 수 있는 제2외국어 과목 등
        
        Args:
            grouped_blocks: 그룹화된 수업 블록 리스트
            
        Returns:
            과목별 선택 그룹 딕셔너리
        """
        choice_groups = defaultdict(list)  # 결과를 저장할 딕셔너리
        
        # 그룹화된 블록 중 '선택' 그룹인 것만 추출
        for block in grouped_blocks:
            if block['group'] == '선택':
                choice_groups[block['subject']].append(block)
        
        return choice_groups
    
    @staticmethod
    def get_selection_group_blocks(grouped_blocks, selection_groups, grade=2):
        """
        학년별 특별 선택 그룹(A, B, C 등) 블록 추출
        
        특정 학년의 선택 그룹(선택A, 선택B 등)에 해당하는 블록들을 추출합니다.
        이는 같은 시간대에 여러 과목이 동시에 진행되는 형태입니다.
        
        Args:
            grouped_blocks: 그룹화된 수업 블록 리스트
            selection_groups: 선택 그룹 정보 딕셔너리
            grade: 학년 (기본값: 2학년)
            
        Returns:
            선택 그룹별 블록 딕셔너리
        """
        # 해당 학년의 선택 그룹이 없으면 빈 딕셔너리 반환
        if grade not in selection_groups:
            return {}
        
        result = {}  # 결과를 저장할 딕셔너리
        
        # 해당 학년의 각 선택 그룹(A, B, C 등)에 대해 처리
        for group_name, subjects in selection_groups[grade].items():
            group_blocks = []  # 현재 그룹의 블록들을 저장할 리스트
            
            # 그룹화된 블록 중 현재 학년 및 선택 그룹에 해당하는 과목 찾기
            for block in grouped_blocks:
                if block['grade'] == grade and block['subject'] in subjects:
                    group_blocks.append(block)
            
            # 그룹 블록이 있으면 결과에 추가
            if group_blocks:
                result[group_name] = group_blocks
        
        return result

# -----------------------------
# 시간표 배치 모듈 (우선순위 큐 활용)
# -----------------------------
class ScheduleManager:
    """
    시간표 배치를 담당하는 클래스
    수업 블록을 시간표에 효과적으로 배치하는 알고리즘을 구현합니다.
    시수가 많은 과목을 우선적으로 여러 요일에 분산 배치합니다.
    """
    
    def __init__(self, settings, fixed_slots):
        """
        초기화: 시간표 설정과 고정 시간 정보 저장
        
        Args:
            settings: 시간표 설정 (요일, 교시 수, 제약조건 등)
            fixed_slots: 고정 시간 슬롯 (조회, 종례, 점심시간 등)
        """
        self.settings = settings
        self.fixed_slots = fixed_slots
        
    def initialize_timetable(self):
        """
        빈 시간표와 교사 일정 초기화
        
        모든 학년, 반에 대한 빈 시간표와 모든 교사에 대한 빈 일정을 생성합니다.
        고정 시간 슬롯(조회, 종례, 점심시간 등)은 미리 채워 놓습니다.
        
        Returns:
            tuple: (시간표, 교사 일정)
        """
        # 빈 시간표 생성 - 각 (학년, 반)마다 요일별, 교시별 빈 DataFrame 생성
        timetable = defaultdict(lambda: pd.DataFrame(
            [["" for _ in range(7)] for _ in range(len(self.settings['days']))],
            index=self.settings['days'],
            columns=[f"{i+1}교시" for i in range(7)]
        ))
        
        # 빈 교사 일정 생성 - 각 교사마다 요일별, 교시별 빈 문자열 배열
        teacher_schedule = defaultdict(lambda: {
            day: ["" for _ in range(7)] for day in self.settings['days']
        })
        
        # 고정 슬롯 적용 (조회, 종례, 점심시간 등)
        for (grade, cls, day, period, label) in self.fixed_slots:
            key = (grade, cls)  # (학년, 반)을 키로 사용
            day_idx = self.settings['days'].index(day)  # 요일 인덱스
            period_idx = period - 1  # 교시 인덱스 (1교시는 인덱스 0)
            
            # 해당 (학년, 반)이 시간표에 있으면 해당 위치에 라벨 설정
            if key in timetable:
                timetable[key].iat[day_idx, period_idx] = label
        
        return timetable, teacher_schedule
    
    def find_common_available_slots(self, blocks, timetable, teacher_schedule):
        """
        여러 블록이 동시에 배치될 수 있는 시간대 찾기
        
        여러 수업 블록(같은 과목의 여러 반)이 모두 배치 가능한 공통 시간대를 찾습니다.
        
        Args:
            blocks: 수업 블록 리스트
            timetable: 현재까지의 시간표
            teacher_schedule: 현재까지의 교사 일정
            
        Returns:
            가능한 시간대 리스트 [(요일, 교시), ...]
        """
        possible_slots = []  # 가능한 시간대를 저장할 리스트
        
        # 각 요일에 대해 검사
        for day in self.settings['days']:
            # 요일별 최대 교시 수 가져오기
            max_period = self.settings['periods_per_day_by_day'][day]
            
            # 특정 요일(월/수/금)은 7교시 배정 제한
            if day in ['월', '수', '금']:
                max_period = min(max_period, 6)  # 최대 6교시까지만 허용
            
            # 각 교시에 대해 검사
            for period in range(max_period):
                slot_ok = True  # 현재 시간대가 가능한지 여부
                
                # 각 블록에 대해 가능 여부 확인
                for block in blocks:
                    for cls in block['classes']:  # 블록의 각 반 검사
                        # 1. 고정 시간과 겹치는지 확인 (조회, 종례 등)
                        is_fixed_slot = any((block['grade'] == fixed[0] and cls == fixed[1] and 
                                           day == fixed[2] and (period+1) == fixed[3]) 
                                          for fixed in self.fixed_slots)
                        if is_fixed_slot:
                            slot_ok = False
                            break
                        
                        # 2. 교사가 이미 다른 수업이 있는지 확인
                        if teacher_schedule[block['teacher']][day][period] != "":
                            slot_ok = False
                            break
                        
                        # 3. 해당 반의 시간표에 이미 과목이 배정되어 있는지 확인
                        key = (block['grade'], cls)
                        if timetable[key].iat[self.settings['days'].index(day), period] != "":
                            slot_ok = False
                            break
                        
                        # 4. 교사의 연속 수업 시간 제한 확인
                        # 4-1. 이전 교시들에서 연속된 수업 수 세기
                        consecutive_count = 0
                        for p in range(period-1, -1, -1):
                            if teacher_schedule[block['teacher']][day][p] != "":
                                consecutive_count += 1
                            else:
                                break
                        
                        # 4-2. 다음 교시들에서 연속될 수업 수 세기
                        next_count = 0
                        for p in range(period+1, max_period):
                            if teacher_schedule[block['teacher']][day][p] != "":
                                next_count += 1
                            else:
                                break
                        
                        # 4-3. 이 시간에 수업을 배정하면 교사의 연속 수업 제한을 초과하는지 확인
                        if consecutive_count + next_count + 1 > self.settings['max_consecutive_teaching_hours']:
                            slot_ok = False
                            break
                    
                    # 하나의 블록이라도 배치 불가능하면 검사 중단
                    if not slot_ok:
                        break
                
                # 모든 블록 배치 가능한 시간대면 추가
                if slot_ok:
                    possible_slots.append((day, period))
        
        return possible_slots
    
    def assign_selection_group_blocks(self, selection_group_blocks, timetable, teacher_schedule):
        """
        특별 선택 그룹(선택A, 선택B 등) 블록 배치
        
        같은 시간대에 여러 선택 과목이 동시에 진행되는 블록을 배치합니다.
        예: 선택A 시간에 "일본어", "중국어", "프랑스어" 등이 동시에 다른 교실에서 진행
        
        Args:
            selection_group_blocks: 특별 선택 그룹 블록 딕셔너리
            timetable: 시간표
            teacher_schedule: 교사 일정
            
        Returns:
            배치 실패한 블록 리스트
        """
        failed_blocks = []  # 배치 실패한 블록을 저장할 리스트
        
        # 특별 선택 그룹을 시수가 많은 순으로 정렬
        sorted_groups = []
        for group_name, all_blocks in selection_group_blocks.items():
            if all_blocks:
                # 그룹 내 첫 번째 과목의 시수 기준으로 정렬
                first_subject = all_blocks[0]['subject']
                hours = all_blocks[0]['hours']
                sorted_groups.append((-hours, group_name))  # 음수로 저장하여 높은 시수부터 처리
        
        # 시수 기준으로 정렬
        heapq.heapify(sorted_groups)
        
        # 시수가 많은 그룹부터 처리
        while sorted_groups:
            _, group_name = heapq.heappop(sorted_groups)
            all_blocks = selection_group_blocks[group_name]
            
            # 과목별로 블록 분류
            subject_blocks = {}
            for block in all_blocks:
                subject = block['subject']
                if subject not in subject_blocks:
                    subject_blocks[subject] = []
                subject_blocks[subject].append(block)
            
            # 그룹 내 첫 번째 과목의 시수 사용 (모든 과목이 같은 시수를 가진다고 가정)
            first_subject = list(subject_blocks.keys())[0]
            total_hours = subject_blocks[first_subject][0]['hours']
            
            # 필요한 시수만큼 배치 시도
            placed_times = 0
            attempts = 0
            max_attempts = 100
            
            # 시수별로 가능한 요일에 분산 배치하기 위한 요일 관리
            used_days = set()  # 이미 사용한 요일
            available_days = list(self.settings['days'])  # 사용 가능한 요일 목록
            
            while placed_times < total_hours and attempts < max_attempts:
                attempts += 1
                
                # 모든 과목이 동시에 배치 가능한 시간대 찾기
                all_possible_slots = []
                all_subjects_possible = True
                
                # 각 과목별로 가능한 시간대 찾기
                for subject, blocks in subject_blocks.items():
                    possible_slots = self.find_common_available_slots(blocks, timetable, teacher_schedule)
                    
                    # 가능한 시간대가 없는 과목이 있으면 실패
                    if not possible_slots:
                        print(f"⚠️ 시도 {attempts}: '{subject}' 과목의 선택그룹 '{group_name}' 배치 불가")
                        for block in blocks:
                            failed_blocks.append(block)
                        all_subjects_possible = False
                        break
                    
                    # 첫 과목이면 그대로 사용, 아니면 교집합 구하기
                    if not all_possible_slots:
                        all_possible_slots = possible_slots
                    else:
                        all_possible_slots = [slot for slot in all_possible_slots if slot in possible_slots]
                
                # 공통 가능 시간대가 없으면 다시 시도
                if not all_subjects_possible or not all_possible_slots:
                    if attempts >= max_attempts:
                        print(f"⚠️ 최대 시도 횟수 도달: 선택그룹 '{group_name}' 배치 실패")
                        break
                    continue
                
                # 아직 사용하지 않은 요일 우선 선택하여 분산 배치
                preferred_slots = []
                for slot in all_possible_slots:
                    day, period = slot
                    if day not in used_days:
                        preferred_slots.append(slot)
                
                # 선호하는 슬롯이 없으면 모든 슬롯 사용
                if not preferred_slots:
                    preferred_slots = all_possible_slots
                
                # 가능한 시간대 중 선호하는 시간대에서 랜덤 선택
                day, period = random.choice(preferred_slots)
                used_days.add(day)  # 사용한 요일 기록
                
                # 모든 과목 및 반을 동시에 배치 (같은 시간대에 여러 과목 진행)
                for subject, blocks in subject_blocks.items():
                    for block in blocks:
                        for cls in block['classes']:
                            # 교사 일정에 과목 추가
                            teacher_schedule[block['teacher']][day][period] = f"{subject} ({block['grade']}-{cls})"
                            
                            # 반 시간표에 그룹명 추가 (예: '선택A')
                            key = (block['grade'], cls)
                            timetable[key].iat[self.settings['days'].index(day), period] = group_name
                
                # 배치 성공 카운트 증가
                placed_times += 1
                
                # 모든 요일을 한 번씩 사용했으면 초기화 (다음 사이클을 위해)
                if len(used_days) == len(available_days):
                    used_days.clear()
        
        return failed_blocks
    
    def assign_choice_group_blocks(self, choice_group_blocks, timetable, teacher_schedule):
        """
        일반 선택 그룹 블록 배치
        
        일반적인 선택 과목을 시간표에 배치합니다.
        시수가 많은 과목부터 우선적으로 다양한 요일에 분산 배치합니다.
        
        Args:
            choice_group_blocks: 일반 선택 그룹 블록 딕셔너리
            timetable: 시간표
            teacher_schedule: 교사 일정
            
        Returns:
            배치 실패한 블록 리스트
        """
        failed_blocks = []  # 배치 실패한 블록을 저장할 리스트
        
        # 일반 선택 그룹을 시수가 많은 순으로 정렬
        sorted_subjects = []
        for subject, blocks in choice_group_blocks.items():
            hours = blocks[0].get('hours', 0)
            if hours > 0:
                sorted_subjects.append((-hours, subject))  # 음수로 저장하여 높은 시수부터 처리
        
        # 우선순위 큐로 변환
        heapq.heapify(sorted_subjects)
        
        # 시수가 많은 과목부터 처리
        while sorted_subjects:
            _, subject = heapq.heappop(sorted_subjects)
            blocks = choice_group_blocks[subject]
            
            # 시수 정보 확인
            total_hours = blocks[0].get('hours', 0)
            placed_times = 0
            
            # 필요한 시수만큼 배치 시도
            attempts = 0
            max_attempts = 100
            
            # 요일별 배치 관리를 위한 변수
            used_days = set()  # 이미 사용한 요일
            available_days = list(self.settings['days'])  # 사용 가능한 요일 목록
            
            while placed_times < total_hours and attempts < max_attempts:
                attempts += 1
                
                # 가능한 시간대 찾기
                possible_slots = self.find_common_available_slots(blocks, timetable, teacher_schedule)
                
                # 가능한 시간대가 없으면 다시 시도 또는 실패 처리
                if not possible_slots:
                    if attempts >= max_attempts:
                        print(f"⚠️ 최대 시도 횟수 도달: '{subject}' 선택 과목 배치 실패")
                        # 실패 목록에 추가
                        for block in blocks:
                            for cls in block['classes']:
                                failed_blocks.append({
                                    "teacher": block['teacher'],
                                    "subject": block['subject'],
                                    "grade": block['grade'],
                                    "class": cls,
                                    "label": f"{block['subject']} ({block['grade']}-{cls})",
                                    "required": block['required']
                                })
                        break
                    continue
                
                # 아직 사용하지 않은 요일 우선 선택하여 분산 배치
                preferred_slots = []
                for slot in possible_slots:
                    day, period = slot
                    if day not in used_days:
                        preferred_slots.append(slot)
                
                # 선호하는 슬롯이 없으면 모든 슬롯 사용
                if not preferred_slots:
                    preferred_slots = possible_slots
                
                # 가능한 시간대 중 선호하는 시간대에서 랜덤 선택
                day, period = random.choice(preferred_slots)
                used_days.add(day)  # 사용한 요일 기록
                
                # 모든 반에 과목 배치
                for block in blocks:
                    for cls in block['classes']:
                        # 교사 일정에 과목 추가
                        teacher_schedule[block['teacher']][day][period] = f"{block['subject']} ({block['grade']}-{cls})"
                        
                        # 반 시간표에 과목명 추가
                        key = (block['grade'], cls)
                        timetable[key].iat[self.settings['days'].index(day), period] = block['subject']
                
                # 배치 성공 카운트 증가
                placed_times += 1
                
                # 모든 요일을 한 번씩 사용했으면 초기화 (다음 사이클을 위해)
                if len(used_days) == len(available_days):
                    used_days.clear()
        
        return failed_blocks
    
    def assign_individual_blocks(self, blocks, timetable, teacher_schedule):
        """
        개별 일반 과목 블록 배치
        
        특별 선택이나 일반 선택이 아닌 일반 과목들을 시간표에 배치합니다.
        시수가 많은 과목부터 우선적으로 다양한 요일에 분산 배치합니다.
        
        Args:
            blocks: 일반 과목 블록 리스트
            timetable: 시간표
            teacher_schedule: 교사 일정
            
        Returns:
            배치 실패한 블록 리스트
        """
        # 1. 블록을 과목별로 그룹화하고 시수 정보 수집
        subject_blocks = defaultdict(list)
        
        # 학년, 과목별로 그룹화
        for block in blocks:
            key = (block['grade'], block['subject'])
            subject_blocks[key].append(block)
        
        # 2. 우선순위 큐 생성: (시수, 학년, 과목명)을 키로 정렬
        # 시수 기준으로만 정렬 (필수/선택 여부는 고려하지 않음)
        priority_queue = []
        for (grade, subject), block_list in subject_blocks.items():
            hours = block_list[0]['hours']
            # 시수가 많은 과목이 높은 우선순위
            priority = (-hours, grade, subject)
            heapq.heappush(priority_queue, (priority, (grade, subject)))
        
        # 3. 개별 수업 배치를 위한 변수 초기화
        failed_blocks = []  # 배치 실패한 블록 리스트
        
        # 4. 우선순위 큐에서 과목 꺼내어 처리
        while priority_queue:
            _, (grade, subject) = heapq.heappop(priority_queue)
            current_blocks = subject_blocks[(grade, subject)]
            
            # 특정 과목의 시수
            total_hours = current_blocks[0]['hours']
            
            # 반별 배치 관리
            for block in current_blocks:
                # 현재 블록의 필수 여부 확인 (정보 유지를 위해)
                required = block['required']
                
                for class_num in block['classes']:
                    # 이 과목, 학년, 반의 배치 정보
                    key = (grade, subject, class_num)
                    
                    # 해당 과목의 각 수업 시간을 다른 요일에 배치하기 위한 정보
                    day_assigned = {}  # 요일별 배치된 시간 수
                    available_days = list(self.settings['days'])  # 사용 가능한 요일 목록
                    
                    # 총 배치해야 할 시수
                    for hour_idx in range(total_hours):
                        # 현재 시간을 배치
                        block_info = {
                            "teacher": block['teacher'],
                            "subject": subject,
                            "grade": grade,
                            "class": class_num,
                            "label": f"{subject} ({grade}-{class_num})",
                            "required": required,
                            "hour_index": hour_idx  # 같은 과목의 몇 번째 시간인지
                        }
                        
                        # 시간 배치 시도 - 다른 요일에 분산 배치
                        placed = self._try_place_block_distributed(block_info, timetable, teacher_schedule, day_assigned, available_days)
                        
                        # 배치 실패시 실패 목록에 추가
                        if not placed:
                            failed_blocks.append(block_info)
                            print(f"⚠️ 배치 실패: {subject} ({grade}-{class_num}) 시간 {hour_idx+1}/{total_hours}")
        
        return failed_blocks

    def _try_place_block_distributed(self, block, timetable, teacher_schedule, day_assigned, available_days, max_attempts=50):
        """
        단일 블록을 시간표에 분산 배치 시도
        
        같은 과목이 서로 다른 요일에 배치되도록 분산 배치합니다.
        
        Args:
            block: 배치할 블록 정보
            timetable: 시간표
            teacher_schedule: 교사 일정
            day_assigned: 요일별 이미 배치된 시간 수 {요일: 배치된 시간 수}
            available_days: 배치 가능한 요일 목록
            max_attempts: 최대 시도 횟수
            
        Returns:
            bool: 배치 성공 여부
        """
        attempts = 0
        placed = False
        
        while not placed and attempts < max_attempts:
            attempts += 1
            
            # 1. 모든 요일을 확인하여 가능한 시간대 찾기
            day_slots = defaultdict(list)  # 요일별 가능한 시간대 {요일: [(요일, 교시), ...]}
            
            for day in self.settings['days']:
                # 요일별 최대 교시 수
                max_period = self.settings['periods_per_day_by_day'][day]
                if day in ['월', '수', '금']:  # 특정 요일 7교시 제한
                    max_period = min(max_period, 6)
                
                # 각 교시별 확인
                for period in range(max_period):
                    # 배치 가능 여부 확인
                    if self._is_slot_available(block, day, period, timetable, teacher_schedule):
                        day_slots[day].append((day, period))
            
            # 2. 요일 선택 전략 적용
            # 2-1. 아직 사용하지 않은 요일 우선
            unused_days = [day for day in available_days if day_assigned.get(day, 0) == 0]
            
            # 2-2. 사용하지 않은 요일이 있으면 해당 요일 중에서 선택
            if unused_days and any(day in day_slots for day in unused_days):
                candidate_days = [day for day in unused_days if day in day_slots]
                selected_day = random.choice(candidate_days)
                possible_slots = day_slots[selected_day]
            # 2-3. 모든 요일이 이미 사용되었으면, 가장 적게 사용된 요일 선택
            elif day_slots:
                # 사용 횟수가 적은 요일 우선
                candidate_days = sorted(day_slots.keys(), key=lambda d: day_assigned.get(d, 0))
                selected_day = candidate_days[0]  # 가장 적게 사용된 요일
                possible_slots = day_slots[selected_day]
            else:
                # 가능한 시간대가 없음
                possible_slots = []
            
            # 3. 가능한 시간대가 있으면 랜덤 선택 후 배치
            if possible_slots:
                day, period = random.choice(possible_slots)  # 교시는 랜덤 선택
                
                # 교사 일정 및 시간표에 과목 추가
                teacher_schedule[block['teacher']][day][period] = block['label']
                timetable[(block['grade'], block['class'])].iat[self.settings['days'].index(day), period] = block['subject']
                
                # 해당 요일 사용 카운트 증가
                day_assigned[day] = day_assigned.get(day, 0) + 1
                
                placed = True
                break
        
        return placed
    
    def _is_slot_available(self, block, day, period, timetable, teacher_schedule):
        """
        특정 시간대에 블록 배치 가능 여부 확인
        
        Args:
            block: 배치할 블록 정보
            day: 요일
            period: 교시
            timetable: 시간표
            teacher_schedule: 교사 일정
            
        Returns:
            bool: 배치 가능 여부
        """
        # 1. 고정 시간대 확인
        is_fixed = any((block['grade'] == f[0] and block['class'] == f[1] and 
                      day == f[2] and (period + 1) == f[3]) 
                     for f in self.fixed_slots)
        if is_fixed:
            return False
        
        # 2. 교사 일정 확인
        if teacher_schedule[block['teacher']][day][period] != "":
            return False
        
        # 3. 해당 반 시간표 확인
        key = (block['grade'], block['class'])
        if timetable[key].iat[self.settings['days'].index(day), period] != "":
            return False
        
        # 4. 교사 연속 수업 시간 제한 확인
        max_period = self.settings['periods_per_day_by_day'][day]
        consecutive = self._count_consecutive_classes(teacher_schedule, block['teacher'], day, period, max_period)
        if consecutive > self.settings['max_consecutive_teaching_hours']:
            return False
        
        # 5. 하루에 같은 과목 제한 확인
        day_classes = self._count_same_subject_in_day(timetable, block, day)
        if day_classes >= 1:  # 같은 요일에는 최대 1시간만 배치 (더 엄격하게 제한)
            return False
        
        return True
    
    def _count_consecutive_classes(self, teacher_schedule, teacher, day, period, max_period):
        """
        교사의 연속 수업 시간 계산 헬퍼 함수
        
        Args:
            teacher_schedule: 교사 일정
            teacher: 교사명
            day: 요일
            period: 현재 고려 중인 교시
            max_period: 해당 요일의 최대 교시 수
            
        Returns:
            이 시간에 수업을 배정할 경우의 연속 수업 시간 수
        """
        # 1. 이전 교시들에서 연속된 수업 수 세기
        before_count = 0
        for p in range(period-1, -1, -1):
            if teacher_schedule[teacher][day][p] != "":
                before_count += 1
            else:
                break
        
        # 2. 다음 교시들에서 연속될 수업 수 세기
        after_count = 0
        for p in range(period+1, max_period):
            if teacher_schedule[teacher][day][p] != "":
                after_count += 1
            else:
                break
        
        # 현재 교시를 포함한 총 연속 수업 시간
        return before_count + 1 + after_count
    
    def _count_same_subject_in_day(self, timetable, block, day):
        """
        하루 중 같은 과목 수 계산 헬퍼 함수
        
        Args:
            timetable: 시간표
            block: 현재 블록
            day: 요일
            
        Returns:
            해당 요일에 같은 과목이 등장하는 수
        """
        key = (block['grade'], block['class'])
        day_idx = self.settings['days'].index(day)
        
        # 해당 요일의 모든 교시를 확인하여 같은 과목 수 세기
        count = 0
        for p in range(len(timetable[key].columns)):
            if timetable[key].iat[day_idx, p] == block['subject']:
                count += 1
        
        return count
    
    def fill_empty_slots(self, timetable, teacher_schedule, failed_blocks):
        """
        빈 교시에 배치하지 못한 블록 재시도
        
        시간표에 남아있는 빈 시간과 배치 실패한 블록을 매칭하여 최대한 배치합니다.
        
        Args:
            timetable: 시간표
            teacher_schedule: 교사 일정
            failed_blocks: 배치 실패한 블록 리스트
            
        Returns:
            여전히 배치 실패한 블록 리스트
        """
        if not failed_blocks:
            return []  # 실패한 블록이 없으면 빈 리스트 반환
        
        # 빈 교시 찾기
        empty_slots = []
        for (grade, cls), df in timetable.items():
            for day_idx, day in enumerate(self.settings['days']):
                max_period = self.settings['periods_per_day_by_day'][day]
                if day in ['월', '수', '금']:
                    max_period = min(max_period, 6)  # 월/수/금 7교시 제한
                
                for period in range(max_period):
                    # 빈 교시이고 고정 시간대가 아닌 경우 추가
                    if df.iat[day_idx, period] == "" and not any(
                            (grade == f[0] and cls == f[1] and day == f[2] and (period+1) == f[3]) 
                            for f in self.fixed_slots):
                        empty_slots.append((grade, cls, day, period))
        
        # 실패한 블록을 우선순위별로 정렬 (선택 과목 우선)
        priority_failed = []
        for block in failed_blocks:
            # 필수 과목이 더 낮은 우선순위를 가지도록 함 (1이 선택, 0이 필수)
            priority = (1 if block.get('required', False) else 0, block['grade'], block['subject'])
            priority_failed.append((priority, block))
        
        # 우선순위별로 정렬 - 튜플의 첫 번째 요소(priority)로만 정렬
        priority_failed.sort(key=lambda x: x[0])
        
        # 우선순위 순서대로 재배치 시도
        still_failed = []  # 여전히 배치 실패한 블록 리스트
        
        for _, block in priority_failed:
            placed = False  # 배치 성공 여부
            valid_slots = []  # 이 블록에 적합한 빈 교시 리스트
            
            # 각 빈 교시에 대해 배치 가능 여부 확인
            for grade, cls, day, period in empty_slots:
                # 블록의 학년, 반과 일치하는지 확인
                if block['grade'] == grade and block['class'] == cls:
                    
                    # 교사 일정 확인
                    if teacher_schedule[block['teacher']][day][period] != "":
                        continue
                    
                    # 연속 수업 제한 확인
                    max_period = self.settings['periods_per_day_by_day'][day]
                    consecutive = self._count_consecutive_classes(teacher_schedule, block['teacher'], day, period, max_period)
                    if consecutive > self.settings['max_consecutive_teaching_hours']:
                        continue
                    
                    # 하루에 같은 과목 제한 확인 (재배치 시에는 더 완화된 조건 적용)
                    day_classes = self._count_same_subject_in_day(timetable, block, day)
                    if day_classes >= 2:  # 빈 슬롯 채우기에서는 최대 2시간까지 허용 (완화)
                        continue
                    
                    # 적합한 빈 교시로 추가
                    valid_slots.append((day, period))
            
            # 적합한 빈 교시가 있으면 랜덤 선택 후 배치
            if valid_slots:
                day, period = random.choice(valid_slots)
                
                # 교사 일정 및 시간표에 과목 추가
                teacher_schedule[block['teacher']][day][period] = block.get('label', f"{block['subject']} ({block['grade']}-{block['class']})")
                timetable[(block['grade'], block['class'])].iat[self.settings['days'].index(day), period] = block['subject']
                
                # 사용한 빈 교시 제거
                empty_slots.remove((block['grade'], block['class'], day, period))
                placed = True  # 배치 성공
            
            # 배치 실패한 경우 계속 실패 목록에 유지
            if not placed:
                still_failed.append(block)
        
        return still_failed
    
    def fill_empty_slots_with_study(self, timetable):
        """
        빈 교시를 '자습'으로 채우기
        
        시간표 생성 후 남은 빈 시간을 '자습'으로 채웁니다.
        
        Args:
            timetable: 시간표
            
        Returns:
            자습으로 채워진 시간표
        """
        # 모든 학년, 반의 시간표에 대해 처리
        for (grade, cls), df in timetable.items():
            for day_idx, day in enumerate(self.settings['days']):
                max_period = self.settings['periods_per_day_by_day'][day]
                
                # 금요일의 경우 창체 시간 고려
                if day == "금" and grade in self.settings["grades"]:
                    max_check = min(max_period, 5)  # 금요일은 5교시까지만 확인
                else:
                    max_check = max_period
                
                # 빈 교시를 '자습'으로 채우기
                for period in range(max_check):
                    if df.iat[day_idx, period] == "":
                        df.iat[day_idx, period] = "자습"
        
        return timetable
    
    def fill_fixed_slots_in_timetable(self, timetable):
        """
        고정 시간 슬롯 적용 (조회, 종례, 점심시간 등)
        
        시간표 생성 과정에서 변경되었을 수 있는 고정 시간을 다시 채웁니다.
        
        Args:
            timetable: 시간표
        """
        for (grade, cls, day, period, label) in self.fixed_slots:
            key = (grade, cls)
            if key in timetable:
                day_idx = self.settings['days'].index(day)
                period_idx = period - 1
                timetable[key].iat[day_idx, period_idx] = label

# -----------------------------
# 검증 모듈
# -----------------------------
class ValidationManager:
    """
    시간표 검증을 담당하는 클래스
    생성된 시간표가 제약 조건을 만족하는지 검증합니다.
    """
    
    def __init__(self, settings):
        """
        초기화: 시간표 설정 저장
        
        Args:
            settings: 시간표 설정
        """
        self.settings = settings
    
    def check_subject_hours_completed(self, timetable, teachers, selection_groups):
        """
        각 과목이 필요한 시수만큼 정확히 배치되었는지 확인
        
        Args:
            timetable: 시간표
            teachers: 교사 정보
            selection_groups: 선택 그룹 정보
            
        Returns:
            부족한 시수 정보 딕셔너리 (없으면 빈 딕셔너리)
        """
        # 1. 각 과목별 필요 시수 정보 수집
        required_hours = {}  # (과목, 학년, 반) -> 필요 시수
        assigned_hours = {}  # (과목, 학년, 반) -> 실제 배치된 시수
        
        # 교사 정보에서 필요 시수 추출
        for teacher, info in teachers.items():
            for subject_info in info["subjects"]:
                subject = subject_info["subject"]
                grade = subject_info["grade"]
                classes = subject_info["classes"]
                hours = subject_info["hours"]
                
                for cls in classes:
                    key = (subject, grade, cls)
                    required_hours[key] = hours
                    assigned_hours[key] = 0  # 초기값 0
        
        # 2. 시간표에서 실제 배치된 시수 계산
        for (grade, cls), df in timetable.items():
            for day in self.settings['days']:
                day_idx = self.settings['days'].index(day)
                
                for period in range(len(df.columns)):
                    subject = df.iat[day_idx, period]
                    
                    # 빈 시간이거나 특수 항목(창체, 자습)이면 건너뛰기
                    if not subject or subject in ["창체", "자습"]:
                        continue
                    
                    # 선택A, 선택B 등 특별 선택 그룹인 경우
                    if subject in ["선택A", "선택B", "선택C", "선택D"]:
                        # 그룹 내 모든 해당 과목의 시수 증가
                        for group_subject in selection_groups.get(grade, {}).get(subject, []):
                            key = (group_subject, grade, cls)
                            if key in required_hours:
                                assigned_hours[key] = assigned_hours.get(key, 0) + 1
                    else:
                        # 일반 과목인 경우
                        key = (subject, grade, cls)
                        assigned_hours[key] = assigned_hours.get(key, 0) + 1
        
        # 3. 부족한 시수 찾기
        missing_hours = {}
        for key, required in required_hours.items():
            assigned = assigned_hours.get(key, 0)
            if assigned < required:
                missing_hours[key] = (required, assigned)  # (필요 시수, 실제 시수)
        
        return missing_hours
    
    def check_consecutive_teaching_limit(self, teacher_schedule, max_consecutive=3):
        """
        교사별 연속 수업 시간이 제한을 초과하는지 확인
        
        Args:
            teacher_schedule: 교사 일정
            max_consecutive: 최대 연속 수업 시간 제한 (기본값: 3)
            
        Returns:
            bool: 모든 교사가 제한을 지키면 True, 아니면 False
        """
        for teacher, schedule in teacher_schedule.items():
            for day in schedule:
                # 연속 수업 시간 계산
                consecutive = 0
                max_consecutive_today = 0
                
                for period_value in schedule[day]:
                    if period_value:  # 수업이 있으면
                        consecutive += 1
                        max_consecutive_today = max(max_consecutive_today, consecutive)
                    else:  # 수업이 없으면
                        consecutive = 0  # 연속 카운트 초기화
                
                # 제한 초과 확인
                if max_consecutive_today > max_consecutive:
                    return False  # 제한 초과
        
        return True  # 모든 교사가 제한 내
    
    def check_daily_subject_limit(self, timetable, max_per_day=2):
        """
        하루에 같은 과목이 최대 횟수를 초과하는지 확인
        
        Args:
            timetable: 시간표
            max_per_day: 하루 최대 과목 수 (기본값: 2)
            
        Returns:
            bool: 모든 과목이 제한을 지키면 True, 아니면 False
        """
        for (grade, cls), df in timetable.items():
            for day in df.index:
                # 해당 요일의 각 교시 과목 확인
                subjects = df.loc[day].values
                
                # 과목별 등장 횟수 세기
                subject_counts = {}
                for subject in subjects:
                    # 빈 시간이거나 특수 항목(창체, 자습)이면 건너뛰기
                    if not subject or subject in ["창체", "자습"]:
                        continue
                    
                    subject_counts[subject] = subject_counts.get(subject, 0) + 1
                
                # 제한 초과 확인
                for count in subject_counts.values():
                    if count > max_per_day:
                        return False  # 제한 초과
        
        return True  # 모든 과목이 제한 내
    
    def analyze_consecutive_teaching(self, teacher_schedule):
        """
        교사별 연속 수업 시간 분석
        
        Args:
            teacher_schedule: 교사 일정
            
        Returns:
            교사별 최대 연속 수업 시간 딕셔너리
        """
        result = {}
        
        for teacher, schedule in teacher_schedule.items():
            max_consecutive = 0  # 교사의 최대 연속 수업 시간
            
            for day in schedule:
                # 연속 수업 시간 계산
                consecutive = 0
                max_consecutive_today = 0
                
                for period_value in schedule[day]:
                    if period_value:  # 수업이 있으면
                        consecutive += 1
                        max_consecutive_today = max(max_consecutive_today, consecutive)
                    else:  # 수업이 없으면
                        consecutive = 0  # 연속 카운트 초기화
                
                # 최대 연속 수업 시간 갱신
                max_consecutive = max(max_consecutive, max_consecutive_today)
            
            # 결과 저장
            result[teacher] = max_consecutive
        
        return result
    
    def calculate_teacher_hours(self, teacher_schedule):
        """
        교사별 실제 수업 시수를 계산
        
        Args:
            teacher_schedule: 교사 일정
            
        Returns:
            교사별 총 수업 시수 딕셔너리
        """
        teacher_hours = {}
        
        for teacher, schedule in teacher_schedule.items():
            # 모든 요일, 교시에서 수업이 있는 시간 카운트
            hours = sum(1 for day in schedule 
                        for period_value in schedule[day] 
                        if period_value)
            
            teacher_hours[teacher] = hours
        
        return teacher_hours

# -----------------------------
# 시간표 생성 매니저
# -----------------------------
class TimetableManager:
    """
    전체 시간표 생성 과정을 관리하는 클래스
    데이터 처리, 스케줄 배치, 검증 과정을 조율합니다.
    """
    
    def __init__(self, settings, teachers, subjects, selection_groups, fixed_slots):
        """
        초기화: 시간표 생성에 필요한 정보 저장 및 관리자 클래스 초기화
        
        Args:
            settings: 시간표 설정 (요일, 교시 등)
            teachers: 교사 정보
            subjects: 과목 정보
            selection_groups: 선택 그룹 정보
            fixed_slots: 고정 시간 정보
        """
        # 기본 데이터 저장
        self.settings = settings
        self.teachers = teachers
        self.subjects = subjects
        self.selection_groups = selection_groups
        self.fixed_slots = fixed_slots
        
        # 각 관리자 클래스 초기화
        self.data_manager = DataManager()
        self.schedule_manager = ScheduleManager(settings, fixed_slots)
        self.validation_manager = ValidationManager(settings)
    
    def create_timetable(self, max_trials=100):
        """
        시간표 생성 실행
        
        여러 번 시도하여 가장 좋은 결과를 찾는 알고리즘입니다.
        
        Args:
            max_trials: 최대 시도 횟수 (기본값: 100)
            
        Returns:
            tuple: (완성된 시간표, 교사 일정)
        """
        trial = 0  # 현재 시도 횟수
        best_result = None  # 최선의 결과 저장 변수
        best_missing = float('inf')  # 최선의 결과의 부족 시수 개수
        
        # 최대 시도 횟수까지 반복하며 최선의 결과 찾기
        while trial < max_trials:
            trial += 1  # 시도 횟수 증가
            
            # 1. 시간표 초기화
            timetable, teacher_schedule = self.schedule_manager.initialize_timetable()
            
            # 2. 수업 블록 생성 및 그룹화
            blocks = self.data_manager.generate_lesson_blocks(self.teachers)
            grouped_blocks = self.data_manager.group_lesson_blocks(blocks)
            
            # 3. 블록 분류: 특별 선택 그룹, 일반 선택 그룹, 일반 선택 과목, 필수 과목
            # 3-1. 특별 선택 그룹(선택A, B, C 등) 추출
            selection_group_blocks = self.data_manager.get_selection_group_blocks(
                grouped_blocks, self.selection_groups, grade=2)
            
            # 3-2. 일반 선택 그룹('선택' 그룹) 추출
            choice_group_blocks = self.data_manager.get_choice_groups(grouped_blocks)
            
            # 3-3. 일반 과목을 선택 과목과 필수 과목으로 분리
            # 특별 선택 또는 일반 선택 그룹에 속하지 않은 과목들
            individual_blocks = [b for b in grouped_blocks 
                            if b['group'] != '선택'
                            and not any(b['subject'] in subjects
                                        for subjects in self.selection_groups.get(b['grade'], {}).values())]
            
            # 일반 선택 과목 (required=False)
            optional_blocks = [b for b in individual_blocks if not b['required']]
            
            # 필수 과목 (required=True)
            required_blocks = [b for b in individual_blocks if b['required']]
            
            # 4. 시간표 배치 (우선순위 순서대로: 선택 -> 필수)
            # 4-1. 특별 선택 그룹(선택A, B, C 등) 먼저 배치
            selection_failed = self.schedule_manager.assign_selection_group_blocks(
                selection_group_blocks, timetable, teacher_schedule)
            
            # 4-2. 일반 선택 그룹('선택' 그룹) 배치
            choice_failed = self.schedule_manager.assign_choice_group_blocks(
                choice_group_blocks, timetable, teacher_schedule)
            
            # 4-3. 일반 선택 과목 배치 (필수가 아닌 과목)
            optional_failed = self.schedule_manager.assign_individual_blocks(
                optional_blocks, timetable, teacher_schedule)
            
            # 4-4. 필수 과목 배치 (모든 선택 과목 배치 후)
            required_failed = self.schedule_manager.assign_individual_blocks(
                required_blocks, timetable, teacher_schedule)
            
            # 5. 실패한 블록 재시도 (빈 교시에 배치)
            all_failed = selection_failed + choice_failed + optional_failed + required_failed
            
            if all_failed:
                still_failed = self.schedule_manager.fill_empty_slots(
                    timetable, teacher_schedule, all_failed)
                
                if still_failed:
                    print(f"⚠️ 여전히 배치 실패한 블록: {len(still_failed)}개")
            
            # 6. 시간표 검증
            # 6-1. 과목 시수 확인
            missing_hours = self.validation_manager.check_subject_hours_completed(
                timetable, self.teachers, self.selection_groups)
            
            # 6-2. 연속 수업 제한 확인
            consecutive_ok = self.validation_manager.check_consecutive_teaching_limit(
                teacher_schedule, max_consecutive=self.settings['max_consecutive_teaching_hours'])
            
            # 6-3. 하루 과목 제한 확인
            daily_limit_ok = self.validation_manager.check_daily_subject_limit(timetable)
            
            # 7. 최선의 결과 갱신 (부족 시수가 더 적은 결과 선택)
            if len(missing_hours) < best_missing:
                best_missing = len(missing_hours)
                best_result = (timetable.copy(), teacher_schedule.copy())
                print(f"✓ 현재까지 최선의 결과: 부족 시수 {best_missing}개 (시도 {trial}/{max_trials})")
            
            # 8. 모든 조건 만족 시 종료 (완벽한 시간표 생성)
            if not missing_hours and consecutive_ok and daily_limit_ok:
                # 최종 결과에 고정 시간 적용
                self.schedule_manager.fill_fixed_slots_in_timetable(timetable)
                print(f"✅ 조건 만족, 배치 성공 (시도 횟수: {trial}/{max_trials})")
                return timetable, teacher_schedule
            
            # 9. 실패 원인 출력
            self._print_failure_reasons(missing_hours, daily_limit_ok, consecutive_ok, trial, max_trials)
        
        # 10. 최대 시도 횟수 도달 시 최선의 결과 반환
        if best_result:
            timetable, teacher_schedule = best_result
            self.schedule_manager.fill_fixed_slots_in_timetable(timetable)
            
            if best_missing > 0:
                print(f"❌ 조건을 만족하는 배치에 실패했습니다. 가장 좋은 결과 반환 (부족 시수: {best_missing}개)")
            else:
                print("✅ 모든 과목이 필요한 시수만큼 정확히 배치되었습니다.")
            
            return timetable, teacher_schedule
        else:
            # 모든 시도가 실패한 경우 마지막 시도 결과 반환
            self.schedule_manager.fill_fixed_slots_in_timetable(timetable)
            return timetable, teacher_schedule
    
    def _print_failure_reasons(self, missing_hours, daily_limit_ok, consecutive_ok, trial, max_trials):
        """
        시간표 생성 실패 원인 출력
        
        Args:
            missing_hours: 부족한 시수 정보
            daily_limit_ok: 하루 과목 제한 만족 여부
            consecutive_ok: 연속 수업 제한 만족 여부
            trial: 현재 시도 횟수
            max_trials: 최대 시도 횟수
        """
        if missing_hours:
            print(f"❌ 시수 부족 (시도 {trial}/{max_trials})")
        if not daily_limit_ok:
            print(f"❌ 하루 과목 제한 초과 (시도 {trial}/{max_trials})")
        if not consecutive_ok:
            print(f"❌ 연속 수업 제한 초과 (시도 {trial}/{max_trials})")
    
    def post_process_timetable(self, timetable, fill_empty=True):
        """
        시간표 후처리
        
        시간표 생성 후 빈 교시를 '자습'으로 채우는 등의 후처리를 수행합니다.
        
        Args:
            timetable: 시간표
            fill_empty: 빈 교시를 채울지 여부 (기본값: True)
            
        Returns:
            후처리된 시간표
        """
        if fill_empty:
            # 빈 교시를 '자습'으로 채우기
            timetable = self.schedule_manager.fill_empty_slots_with_study(timetable)
        
        return timetable