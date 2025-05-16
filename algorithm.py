import pandas as pd
import random
from collections import defaultdict

# -----------------------------
# 데이터 처리 모듈
# -----------------------------
class DataManager:
    """데이터 처리를 담당하는 클래스"""
    
    @staticmethod
    def generate_lesson_blocks(teachers):
        """교사 정보로부터 수업 블록 생성"""
        blocks = []
        for teacher, info in teachers.items():
            for item in info["subjects"]:
                for class_num in item["classes"]:
                    group = item["group"].get(str(class_num)) or item["group"].get(class_num)
                    blocks.append({
                        "teacher": teacher,
                        "subject": item["subject"],
                        "grade": item["grade"],
                        "class": class_num,
                        "group": group,
                        "hours": item["hours"],
                        "required": item["required"]
                    })
        return blocks
    
    @staticmethod
    def group_lesson_blocks(blocks):
        """수업 블록을 그룹화"""
        grouped = defaultdict(lambda: {
            "teacher": None, "subject": None, "grade": None,
            "group": None, "hours": None, "required": None, "classes": []
        })
        for b in blocks:
            key = (b['teacher'], b['subject'], b['grade'], b['group'])
            if not grouped[key]['classes']:
                grouped[key].update({k: b[k] for k in ('teacher', 'subject', 'grade', 'group', 'hours', 'required')})
            grouped[key]['classes'].append(b['class'])
        return list(grouped.values())
    
    @staticmethod
    def get_choice_groups(grouped_blocks):
        """일반 선택 그룹 블록 추출"""
        choice_groups = defaultdict(list)
        for b in grouped_blocks:
            if b['group'] == '선택':
                choice_groups[b['subject']].append(b)
        return choice_groups
    
    @staticmethod
    def get_selection_group_blocks(grouped_blocks, selection_groups, grade=2):
        """학년별 선택 그룹(A, B, C 등) 블록 추출"""
        if grade not in selection_groups:
            return {}
        
        result = {}
        for group_name, subjects in selection_groups[grade].items():
            group_blocks = []
            for b in grouped_blocks:
                if b['grade'] == grade and b['subject'] in subjects:
                    group_blocks.append(b)
            if group_blocks:
                result[group_name] = group_blocks
        
        return result

# -----------------------------
# 시간표 배치 모듈
# -----------------------------
class ScheduleManager:
    """시간표 배치를 담당하는 클래스"""
    
    def __init__(self, settings, fixed_slots):
        self.settings = settings
        self.fixed_slots = fixed_slots
        
    def initialize_timetable(self):
        """빈 시간표와 교사 일정 초기화"""
        timetable = defaultdict(lambda: pd.DataFrame(
            [["" for _ in range(7)] for _ in range(len(self.settings['days']))],
            index=self.settings['days'],
            columns=[f"{i+1}교시" for i in range(7)]
        ))
        
        teacher_schedule = defaultdict(lambda: {
            day: ["" for _ in range(7)] for day in self.settings['days']
        })
        
        # 고정 슬롯 적용
        for (grade, cls, day, period, label) in self.fixed_slots:
            key = (grade, cls)
            day_idx = self.settings['days'].index(day)
            period_idx = period - 1
            if key in timetable:
                timetable[key].iat[day_idx, period_idx] = label
                
        return timetable, teacher_schedule
    
    def find_common_available_slots(self, blocks, timetable, teacher_schedule):
        """블록들에 대해 공통으로 가능한 시간대 찾기"""
        possible_slots = []
        for day in self.settings['days']:
            # 월/수/금은 6교시, 화/목은 7교시
            max_period = self.settings['periods_per_day_by_day'][day]
            # 월/수/금은 7교시 배정 금지 조건 추가
            if day in ['월', '수', '금']:
                max_period = min(max_period, 6)
    
            for period in range(max_period):
                slot_ok = True
                for b in blocks:
                    for cls in b['classes']:
                        # fixed_slots: (grade, cls, day, period+1, text)
                        if any((b['grade'] == f[0] and cls == f[1] and day == f[2] and (period+1) == f[3]) 
                              for f in self.fixed_slots):
                            slot_ok = False
                            break
                        if teacher_schedule[b['teacher']][day][period] != "":
                            slot_ok = False
                            break
                        key = (b['grade'], cls)
                        if timetable[key].iat[self.settings['days'].index(day), period] != "":
                            slot_ok = False
                            break
                        
                        # 교사의 연속 수업 시간 제한 확인
                        consecutive_count = 0
                        if period > 0:
                            # 이전 시간 확인
                            for p in range(period-1, -1, -1):
                                if teacher_schedule[b['teacher']][day][p] != "":
                                    consecutive_count += 1
                                else:
                                    break
                        
                        # 다음 시간들 확인
                        next_count = 0
                        if period < max_period - 1:
                            for p in range(period+1, max_period):
                                if teacher_schedule[b['teacher']][day][p] != "":
                                    next_count += 1
                                else:
                                    break
                        
                        # 연속 수업 제한 확인
                        if consecutive_count + next_count + 1 > self.settings['max_consecutive_teaching_hours']:
                            slot_ok = False
                            break
                            
                    if not slot_ok:
                        break
                if slot_ok:
                    possible_slots.append((day, period))
        return possible_slots
    
    def assign_selection_group_blocks(self, selection_group_blocks, timetable, teacher_schedule):
        """학년별 선택 그룹 배치"""
        failed_blocks = []
        
        for group_name, all_blocks in selection_group_blocks.items():
            if not all_blocks:
                continue
                
            subject_blocks = {}  # 과목별로 블록 분류
            for block in all_blocks:
                subject = block['subject']
                if subject not in subject_blocks:
                    subject_blocks[subject] = []
                subject_blocks[subject].append(block)
            
            # 그룹 내 첫 번째 과목의 시수 사용
            first_subject = list(subject_blocks.keys())[0]
            total_hours = subject_blocks[first_subject][0]['hours']
            
            placed_times = 0
            attempts = 0
            max_attempts = 100
            
            while placed_times < total_hours and attempts < max_attempts:
                attempts += 1
                # 모든 과목이 동시에 배치 가능한 시간 찾기
                all_possible_slots = []
                
                for subject, blocks in subject_blocks.items():
                    possible_slots = self.find_common_available_slots(blocks, timetable, teacher_schedule)
                    if not possible_slots:
                        print(f"⚠️ 시도 {attempts}: 선택그룹 과목 배치 실패: {subject}, 그룹 {group_name}")
                        for block in blocks:
                            failed_blocks.append(block)
                        all_possible_slots = []
                        break
                    if not all_possible_slots:
                        all_possible_slots = possible_slots
                    else:
                        # 두 리스트의 교집합 찾기
                        all_possible_slots = [slot for slot in all_possible_slots if slot in possible_slots]
                
                if not all_possible_slots:
                    if attempts >= max_attempts:
                        print(f"⚠️ 최대 시도 횟수 도달: 선택그룹 {group_name} 배치 실패")
                        break
                    continue
                
                # 랜덤 슬롯 선택
                day, period = random.choice(all_possible_slots)
                
                # 모든 과목 및 학급에 동시에 배치
                for subject, blocks in subject_blocks.items():
                    for block in blocks:
                        for cls in block['classes']:
                            teacher_schedule[block['teacher']][day][period] = f"{subject} ({block['grade']}-{cls})"
                            key = (block['grade'], cls)
                            timetable[key].iat[self.settings['days'].index(day), period] = group_name
                
                placed_times += 1
        
        return failed_blocks
    
    def assign_choice_group_blocks(self, choice_group_blocks, timetable, teacher_schedule):
        """일반 선택 그룹 블록 배치"""
        failed_blocks = []
        for subject, blocks in choice_group_blocks.items():
            placed_times = 0
            total_hours = blocks[0].get('hours', 0)
            if total_hours <= 0:
                print(f"⚠️ 잘못된 시수: {subject} 시수={total_hours}")
                continue
    
            attempts = 0
            max_attempts = 100
            
            while placed_times < total_hours and attempts < max_attempts:
                attempts += 1
                possible_slots = self.find_common_available_slots(blocks, timetable, teacher_schedule)
                if not possible_slots:
                    if attempts >= max_attempts:
                        print(f"⚠️ 최대 시도 횟수 도달: 선택교과 그룹 배치 실패: {subject}")
                        for b in blocks:
                            for cls in b['classes']:
                                failed_blocks.append({
                                    "teacher": b['teacher'],
                                    "subject": b['subject'],
                                    "grade": b['grade'],
                                    "class": cls,
                                    "label": f"{b['subject']} ({b['grade']}-{cls})",
                                    "required": b['required']
                                })
                        break
                    continue
    
                day, period = random.choice(possible_slots)  # 랜덤 배치
    
                for b in blocks:
                    for cls in b['classes']:
                        teacher_schedule[b['teacher']][day][period] = f"{b['subject']} ({b['grade']}-{cls})"
                        key = (b['grade'], cls)
                        timetable[key].iat[self.settings['days'].index(day), period] = b['subject']
    
                placed_times += 1
        
        return failed_blocks
    
    def assign_individual_blocks(self, blocks, timetable, teacher_schedule):
        """개별 블록 배치"""
        # 필수 과목과 선택 과목으로 분리
        required_blocks = []
        optional_blocks = []
        
        for block in blocks:
            for class_num in block['classes']:
                for _ in range(block['hours']):
                    block_info = {
                        "teacher": block['teacher'],
                        "subject": block['subject'],
                        "grade": block['grade'],
                        "class": class_num,
                        "label": f"{block['subject']} ({block['grade']}-{class_num})",
                        "required": block['required']
                    }
                    if block['required']:
                        required_blocks.append(block_info)
                    else:
                        optional_blocks.append(block_info)
        
        # 필수 과목 먼저 배치
        random.shuffle(required_blocks)
        all_blocks = required_blocks + optional_blocks
        failed_blocks = []
        
        for b in all_blocks:
            placed = False
            attempts = 0
            max_attempts = 50
    
            while not placed and attempts < max_attempts:
                attempts += 1
                possible_slots = []  # 매 시도마다 초기화
    
                for day in self.settings['days']:
                    max_period = self.settings['periods_per_day_by_day'][day]
                    if day in ['월', '수', '금']:
                        max_period = min(max_period, 6)
                    for period in range(max_period):
                        if (b['grade'], b['class'], day, period + 1) in [(fs[0], fs[1], fs[2], fs[3]) for fs in self.fixed_slots]:
                            continue
                        if teacher_schedule[b['teacher']][day][period] != "":
                            continue
                        key = (b['grade'], b['class'])
                        if timetable[key].iat[self.settings['days'].index(day), period] != "":
                            continue
                            
                        # 연속 수업 시간 제한 확인
                        consecutive_count = 0
                        if period > 0:
                            for p in range(period-1, -1, -1):
                                if teacher_schedule[b['teacher']][day][p] != "":
                                    consecutive_count += 1
                                else:
                                    break
                        
                        next_count = 0
                        if period < max_period - 1:
                            for p in range(period+1, max_period):
                                if teacher_schedule[b['teacher']][day][p] != "":
                                    next_count += 1
                                else:
                                    break
                        
                        if consecutive_count + next_count + 1 > self.settings['max_consecutive_teaching_hours']:
                            continue
                        
                        # 하루에 같은 과목이 2교시 이상 안되게 체크
                        day_subjects = [timetable[(b['grade'], b['class'])].iat[self.settings['days'].index(day), p] 
                                      for p in range(len(timetable[(b['grade'], b['class'])].columns))]
                        if day_subjects.count(b['subject']) >= 2:
                            continue
                        
                        possible_slots.append((day, period))
    
                # 가능한 시간대 중 랜덤 선택
                if possible_slots:
                    day, period = random.choice(possible_slots)
                    teacher_schedule[b['teacher']][day][period] = b['label']
                    timetable[(b['grade'], b['class'])].iat[self.settings['days'].index(day), period] = b['subject']
                    placed = True
                    break
            
            if not placed:
                failed_blocks.append(b)
                print(f"⚠️ 배치 실패: {b}")
        
        return failed_blocks
    
    def fill_empty_slots(self, timetable, teacher_schedule, failed_blocks):
        """빈 교시에 배치하지 못한 블록 재시도"""
        if not failed_blocks:
            return []
        
        # 빈 교시 찾기
        empty_slots = []
        for (grade, cls), df in timetable.items():
            for day_idx, day in enumerate(self.settings['days']):
                max_period = self.settings['periods_per_day_by_day'][day]
                if day in ['월', '수', '금']:
                    max_period = min(max_period, 6)
                
                for period in range(max_period):
                    if df.iat[day_idx, period] == "":
                        # fixed_slots 확인
                        if not any((grade == f[0] and cls == f[1] and day == f[2] and (period+1) == f[3]) 
                                  for f in self.fixed_slots):
                            empty_slots.append((grade, cls, day, period))
        
        # 실패한 블록을 빈 교시에 다시 배치 시도
        still_failed = []
        for block in failed_blocks:
            placed = False
            valid_empty_slots = []
            
            for grade, cls, day, period in empty_slots:
                if block['grade'] == grade and block['class'] == cls:
                    # 교사 스케줄 확인
                    if teacher_schedule[block['teacher']][day][period] != "":
                        continue
                    
                    # 연속 수업 제한 확인
                    consecutive_count = 0
                    if period > 0:
                        for p in range(period-1, -1, -1):
                            if teacher_schedule[block['teacher']][day][p] != "":
                                consecutive_count += 1
                            else:
                                break
                    
                    next_count = 0
                    max_period = self.settings['periods_per_day_by_day'][day]
                    if period < max_period - 1:
                        for p in range(period+1, max_period):
                            if teacher_schedule[block['teacher']][day][p] != "":
                                next_count += 1
                            else:
                                break
                    
                    if consecutive_count + next_count + 1 > self.settings['max_consecutive_teaching_hours']:
                        continue
                    
                    # 하루에 같은 과목이 2교시 이상 안되게 체크
                    day_subjects = [timetable[(grade, cls)].iat[self.settings['days'].index(day), p] 
                                   for p in range(len(timetable[(grade, cls)].columns))]
                    if day_subjects.count(block['subject']) >= 2:
                        continue
                    
                    valid_empty_slots.append((day, period))
            
            # 가능한 빈 슬롯이 있으면 배치
            if valid_empty_slots:
                day, period = random.choice(valid_empty_slots)
                teacher_schedule[block['teacher']][day][period] = block['label']
                timetable[(block['grade'], block['class'])].iat[self.settings['days'].index(day), period] = block['subject']
                
                # 사용한 빈 슬롯 제거
                empty_slots.remove((block['grade'], block['class'], day, period))
                placed = True
            
            if not placed:
                still_failed.append(block)
        
        return still_failed
    
    def fill_empty_slots_with_study(self, timetable):
        """시간표의 빈 교시를 '자습'으로 채움"""
        for (grade, cls), df in timetable.items():
            for day_idx, day in enumerate(self.settings['days']):
                max_period = self.settings['periods_per_day_by_day'][day]
                # 금요일 5, 6교시는 창체로 이미 채워져 있음
                if day == "금" and grade in self.settings["grades"]:
                    max_check = min(max_period, 5)
                else:
                    max_check = max_period
                    
                for period in range(max_check):
                    # 빈 교시라면 '자습'으로 채움
                    if df.iat[day_idx, period] == "":
                        df.iat[day_idx, period] = "자습"
        return timetable
    
    def fill_fixed_slots_in_timetable(self, timetable):
        """Fixed slots 적용"""
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
    """시간표 검증을 담당하는 클래스"""
    
    def __init__(self, settings):
        self.settings = settings
    
    def check_subject_hours_completed(self, timetable, teachers, selection_groups):
        """각 교과목이 필요한 시수만큼 정확히 배치되었는지 확인"""
        subject_hours_required = {}
        subject_hours_assigned = {}
        
        # 교사 정보에서 필요한 시수 정보 수집
        for teacher, info in teachers.items():
            for subject_info in info["subjects"]:
                subject = subject_info["subject"]
                grade = subject_info["grade"]
                classes = subject_info["classes"]
                hours = subject_info["hours"]
                
                for cls in classes:
                    key = (subject, grade, cls)
                    subject_hours_required[key] = hours
                    subject_hours_assigned[key] = 0
        
        # 시간표에서 실제 배치된 시수 집계
        for (grade, cls), df in timetable.items():
            for day in self.settings['days']:
                for period in range(len(df.columns)):
                    subject = df.iat[self.settings['days'].index(day), period]
                    if subject and subject != "창체" and subject != "자습":
                        # 선택A, 선택B, 선택C 시간 확인
                        if subject in ["선택A", "선택B", "선택C", "선택D"]:
                            for group_subject in selection_groups.get(grade, {}).get(subject, []):
                                key = (group_subject, grade, cls)
                                if key in subject_hours_required:
                                    subject_hours_assigned[key] = subject_hours_assigned.get(key, 0) + 1
                        else:
                            key = (subject, grade, cls)
                            subject_hours_assigned[key] = subject_hours_assigned.get(key, 0) + 1
        
        # 검증 결과
        missing_hours = {}
        for key, required in subject_hours_required.items():
            subject, grade, cls = key
            assigned = subject_hours_assigned.get(key, 0)
            if assigned < required:
                missing_hours[key] = (required, assigned)
        
        return missing_hours
    
    def check_consecutive_teaching_limit(self, teacher_schedule, max_consecutive=3):
        """교사별 연속 수업 시간이 제한을 초과하는지 확인"""
        for teacher, schedule in teacher_schedule.items():
            for day in schedule:
                consecutive_count = 0
                max_consecutive_for_day = 0
                
                for period_value in schedule[day]:
                    if period_value != "":
                        consecutive_count += 1
                        max_consecutive_for_day = max(max_consecutive_for_day, consecutive_count)
                    else:
                        consecutive_count = 0
                
                if max_consecutive_for_day > max_consecutive:
                    return False
        
        return True
    
    def check_daily_subject_limit(self, timetable, max_per_day=2):
        """하루에 같은 과목이 최대 횟수를 초과하는지 확인"""
        for key, df in timetable.items():
            for day in df.index:
                day_subjects = df.loc[day].values
                subject_counts = {}
                for subj in day_subjects:
                    if subj != "" and subj != "창체" and subj != "자습":
                        subject_counts[subj] = subject_counts.get(subj, 0) + 1
                for count in subject_counts.values():
                    if count > max_per_day:
                        return False
        return True
    
    def analyze_consecutive_teaching(self, teacher_schedule):
        """교사별 연속 수업 시간 분석"""
        result = {}
        for teacher, schedule in teacher_schedule.items():
            max_consecutive = 0
            for day in schedule:
                consecutive_count = 0
                max_for_day = 0
                
                for period_value in schedule[day]:
                    if period_value != "":
                        consecutive_count += 1
                        max_for_day = max(max_for_day, consecutive_count)
                    else:
                        consecutive_count = 0
                
                max_consecutive = max(max_consecutive, max_for_day)
            
            result[teacher] = max_consecutive
        
        return result
    
    def calculate_teacher_hours(self, teacher_schedule):
        """교사별 실제 수업 시수를 계산"""
        teacher_hours = {}
        for teacher, schedule in teacher_schedule.items():
            hours = 0
            for day in schedule:
                for period_value in schedule[day]:
                    if period_value != "":
                        hours += 1
            teacher_hours[teacher] = hours
        return teacher_hours

# -----------------------------
# 시간표 생성 매니저
# -----------------------------
class TimetableManager:
    """전체 시간표 생성 과정을 관리하는 클래스"""
    
    def __init__(self, settings, teachers, subjects, selection_groups, fixed_slots):
        self.settings = settings
        self.teachers = teachers
        self.subjects = subjects
        self.selection_groups = selection_groups
        self.fixed_slots = fixed_slots
        
        self.data_manager = DataManager()
        self.schedule_manager = ScheduleManager(settings, fixed_slots)
        self.validation_manager = ValidationManager(settings)
    
    def create_timetable(self, max_trials=100):
        """시간표 생성 실행"""
        trial = 0
        best_result = None
        best_missing = float('inf')
        
        while trial < max_trials:
            # 시간표 초기화
            timetable, teacher_schedule = self.schedule_manager.initialize_timetable()
            
            # 블록 생성 및 그룹화
            blocks = self.data_manager.generate_lesson_blocks(self.teachers)
            grouped_blocks = self.data_manager.group_lesson_blocks(blocks)
            
            # 선택 그룹 블록 추출
            selection_group_blocks = self.data_manager.get_selection_group_blocks(
                grouped_blocks, self.selection_groups, grade=2)
            
            # 일반 선택 그룹 블록 추출
            choice_group_blocks = self.data_manager.get_choice_groups(grouped_blocks)
            
            # 개별 블록 추출
            individual_blocks = [b for b in grouped_blocks 
                               if b['group'] != '선택' 
                               and not any(b['subject'] in subjects 
                                         for subjects in self.selection_groups.get(b['grade'], {}).values())]
            
            # 1. 선택 그룹 배치
            selection_failed_blocks = self.schedule_manager.assign_selection_group_blocks(
                selection_group_blocks, timetable, teacher_schedule)
            
            # 2. 일반 선택 그룹 배치
            choice_failed_blocks = self.schedule_manager.assign_choice_group_blocks(
                choice_group_blocks, timetable, teacher_schedule)
            
            # 3. 개별 블록 배치
            individual_failed_blocks = self.schedule_manager.assign_individual_blocks(
                individual_blocks, timetable, teacher_schedule)
            
            # 4. 실패한 블록 재시도
            all_failed_blocks = selection_failed_blocks + choice_failed_blocks + individual_failed_blocks
            if all_failed_blocks:
                still_failed = self.schedule_manager.fill_empty_slots(
                    timetable, teacher_schedule, all_failed_blocks)
                if still_failed:
                    print(f"⚠️ 여전히 배치 실패한 블록: {len(still_failed)}개")
            
            # 5. 검증
            missing_hours = self.validation_manager.check_subject_hours_completed(
                timetable, self.teachers, self.selection_groups)
            
            consecutive_ok = self.validation_manager.check_consecutive_teaching_limit(
                teacher_schedule, max_consecutive=self.settings['max_consecutive_teaching_hours'])
            
            daily_limit_ok = self.validation_manager.check_daily_subject_limit(timetable)
            
            # 최선의 결과 갱신
            if len(missing_hours) < best_missing:
                best_missing = len(missing_hours)
                best_result = (timetable.copy(), teacher_schedule.copy())
                print(f"✓ 현재까지 최선의 결과: 부족 시수 {best_missing}개 (시도 {trial+1})")
            
            # 모든 조건 만족 시 종료
            if not missing_hours and consecutive_ok and daily_limit_ok:
                self.schedule_manager.fill_fixed_slots_in_timetable(timetable)
                print(f"✅ 조건 만족, 배치 성공 (시도 횟수: {trial+1})")
                return timetable, teacher_schedule
            
            # 실패 원인 출력
            if missing_hours:
                print(f"❌ 시수 부족 (시도 {trial+1}/{max_trials})")
            if not daily_limit_ok:
                print(f"❌ 하루 과목 제한 초과 (시도 {trial+1}/{max_trials})")
            if not consecutive_ok:
                print(f"❌ 연속 수업 제한 초과 (시도 {trial+1}/{max_trials})")
            
            trial += 1
        
        # 최대 시도 횟수 도달 시 최선의 결과 반환
        if best_result:
            timetable, teacher_schedule = best_result
            self.schedule_manager.fill_fixed_slots_in_timetable(timetable)
            if best_missing > 0:
                print(f"❌ 조건을 만족하는 배치에 실패했습니다. 가장 좋은 결과 반환 (부족 시수: {best_missing}개)")
            else:
                print("✅ 모든 과목이 필요한 시수만큼 정확히 배치되었습니다.")
            return timetable, teacher_schedule
        else:
            self.schedule_manager.fill_fixed_slots_in_timetable(timetable)
            return timetable, teacher_schedule
    
    def post_process_timetable(self, timetable, fill_empty=True):
        """시간표 후처리"""
        if fill_empty:
            timetable = self.schedule_manager.fill_empty_slots_with_study(timetable)
        return timetable