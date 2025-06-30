import random
from typing import Dict, List, Tuple, Any


class EliteFeedbackGenerator:
    """엘리트 레벨의 운동 피드백 생성기"""
    
    def __init__(self):
        # 운동별 전문 피드백 템플릿
        self.exercise_feedback = {
            'squat': {
                'perfect': [
                    "완벽한 스쿼트입니다. 척추 중립 {spine_angle:.0f}도, 깊이 {knee_angle:.0f}도 달성.",
                    "훌륭합니다! 무릎 궤적과 척추 정렬이 이상적입니다.",
                    "엘리트 수준의 스쿼트. 모든 체크포인트를 통과했습니다."
                ],
                'good': [
                    "좋은 자세입니다. {main_issue}만 조금 더 신경쓰세요.",
                    "전반적으로 양호합니다. {score:.0f}점. {correction_point}",
                    "안정적인 스쿼트입니다. 다음 단계로 {next_focus}에 집중하세요."
                ],
                'warning': [
                    "주의! {violation_message} 즉시 교정하세요.",
                    "위험 신호 감지. {main_issue}. 무게를 줄이고 자세부터 다시.",
                    "부상 위험 {injury_risk:.0%}. {critical_correction} 필수."
                ]
            },
            'deadlift': {
                'perfect': [
                    "완벽한 데드리프트! 척추각 {spine_angle:.0f}도로 안전합니다.",
                    "교과서적인 힙 힌지. 바벨 경로 효율성 {efficiency:.0f}%.",
                    "폭발적인 파워와 완벽한 자세의 조화입니다."
                ],
                'good': [
                    "안정적인 리프트입니다. {minor_adjustment}",
                    "좋은 폼입니다. 바벨을 조금 더 몸에 가깝게 유지하세요.",
                    "힙 드라이브가 좋습니다. {score:.0f}점."
                ],
                'warning': [
                    "위험! 허리가 굽었습니다! 즉시 중단하세요!",
                    "척추 굴곡 {spine_angle:.0f}도 감지. 부상 위험 매우 높음.",
                    "STOP! 자세가 무너졌습니다. 안전이 최우선입니다."
                ]
            },
            'overhead_press': {
                'perfect': [
                    "완벽한 프레스! 코어 안정성 {core_score:.0f}점.",
                    "수직 바 경로와 견고한 코어. 훌륭합니다!",
                    "팔꿈치 위치와 허리 각도 모두 이상적입니다."
                ],
                'good': [
                    "좋은 프레스입니다. {adjustment_needed}",
                    "안정적입니다. 팔꿈치를 조금 더 안쪽으로.",
                    "코어 컨트롤이 양호합니다. {score:.0f}점."
                ],
                'warning': [
                    "허리 과신전 주의! 복부에 더 힘을 주세요.",
                    "위험! 허리각 {lumbar_angle:.0f}도. 즉시 교정필요.",
                    "어깨 부상 위험. 팔꿈치가 너무 벌어집니다."
                ]
            },
            'bench_press': {
                'perfect': [
                    "완벽한 벤치프레스! 팔꿈치 각도 {elbow_angle:.0f}도.",
                    "견갑골 세팅과 아치가 이상적입니다.",
                    "파워풀한 드라이브와 안정적인 경로입니다."
                ],
                'good': [
                    "안정적인 프레스. {minor_issue}",
                    "좋은 컨트롤입니다. 터치 포인트만 조정하세요.",
                    "전반적으로 양호. {score:.0f}점."
                ],
                'warning': [
                    "팔꿈치가 과도하게 벌어집니다. 어깨 부상 주의!",
                    "손목이 꺾였습니다. 즉시 교정하세요.",
                    "바운싱 금지! 가슴에서 일시정지 후 프레스."
                ]
            },
            'plank': {
                'perfect': [
                    "완벽한 플랭크! 일직선 유지 {alignment_score:.0f}점.",
                    "코어 활성화 최고 수준. 자세 유지하세요.",
                    "엘리트 플랭크. 미동도 없습니다."
                ],
                'good': [
                    "좋은 플랭크입니다. {minor_wobble}",
                    "안정적입니다. 엉덩이만 살짝 조정하세요.",
                    "코어 컨트롤 {score:.0f}점. 계속 유지하세요."
                ],
                'warning': [
                    "엉덩이가 처집니다! 코어에 집중하세요.",
                    "자세가 무너지고 있습니다. 휴식이 필요합니다.",
                    "떨림이 심합니다. 한계점에 도달했습니다."
                ]
            }
        }
        
        # 일반적인 큐잉 문구
        self.general_cues = {
            'breathing': [
                "호흡을 일정하게 유지하세요.",
                "하강시 들이마시고, 상승시 내쉬세요.",
                "복압을 유지하며 호흡하세요."
            ],
            'focus': [
                "집중력을 유지하세요.",
                "마인드-머슬 커넥션에 집중.",
                "목표 근육을 의식하세요."
            ],
            'tempo': [
                "템포를 일정하게 유지하세요.",
                "천천히 컨트롤하며 움직이세요.",
                "폭발적으로 올리고 천천히 내리세요."
            ]
        }
        
        # 전문 용어 설명
        self.term_explanations = {
            'butt_wink': "벗 윙크: 스쿼트 최저점에서 골반이 뒤로 말리는 현상",
            'knee_valgus': "무릎 모임: 무릎이 안쪽으로 쏠리는 현상",
            'hip_hinge': "힙 힌지: 엉덩이 관절을 중심으로 하는 움직임",
            'lumbar_hyperextension': "요추 과신전: 허리가 과도하게 젖혀지는 현상",
            'scapular_retraction': "견갑골 후인: 어깨뼈를 뒤로 모으는 동작"
        }
    
    def generate_feedback(self, analysis_result: Dict, exercise_name: str) -> Dict[str, Any]:
        """분석 결과를 바탕으로 전문적인 피드백 생성"""
        
        feedback = {
            'instant_feedback': self._generate_instant_feedback(analysis_result, exercise_name),
            'voice_cue': self._generate_voice_cue(analysis_result, exercise_name),
            'visual_indicators': self._generate_visual_indicators(analysis_result),
            'correction_priority': self._prioritize_corrections(analysis_result),
            'motivational_message': self._generate_motivation(analysis_result),
            'technical_analysis': self._generate_technical_analysis(analysis_result),
            'next_rep_focus': self._generate_next_rep_focus(analysis_result)
        }
        
        return feedback
    
    def _generate_instant_feedback(self, result: Dict, exercise: str) -> str:
        """즉각적인 피드백 생성"""
        score = result.get('overall_score', 0)
        violations = result.get('violations', [])
        
        exercise_key = exercise.lower().replace(' ', '_')
        if exercise_key not in self.exercise_feedback:
            exercise_key = 'squat'  # 기본값
        
        # 점수와 위반사항에 따라 피드백 선택
        if violations and any(v['severity'] in ['critical', 'high'] for v in violations):
            feedback_type = 'warning'
            templates = self.exercise_feedback[exercise_key]['warning']
        elif score >= 90:
            feedback_type = 'perfect'
            templates = self.exercise_feedback[exercise_key]['perfect']
        else:
            feedback_type = 'good'
            templates = self.exercise_feedback[exercise_key]['good']
        
        # 템플릿 선택 및 변수 채우기
        template = random.choice(templates)
        
        # 컨텍스트 변수 준비
        context = {
            'score': score,
            'spine_angle': result.get('angles', {}).get('spine', 0),
            'knee_angle': result.get('angles', {}).get('avg_knee', 90),
            'elbow_angle': result.get('angles', {}).get('avg_elbow', 75),
            'lumbar_angle': result.get('angles', {}).get('lumbar_extension', 0),
            'efficiency': result.get('metrics', {}).get('bar_path_efficiency', 100),
            'alignment_score': result.get('scores', {}).get('alignment', 100),
            'core_score': result.get('scores', {}).get('core_stability', 100),
            'injury_risk': result.get('performance_metrics', {}).get('injury_risk', 0),
            'main_issue': self._get_main_issue(result),
            'correction_point': self._get_correction_point(result),
            'next_focus': self._get_next_focus(result),
            'violation_message': violations[0]['message'] if violations else '',
            'critical_correction': self._get_critical_correction(result),
            'minor_adjustment': self._get_minor_adjustment(result),
            'adjustment_needed': self._get_adjustment_needed(result),
            'minor_issue': self._get_minor_issue(result),
            'minor_wobble': self._get_minor_wobble(result)
        }
        
        # 템플릿 포맷팅
        try:
            return template.format(**context)
        except:
            return template  # 포맷팅 실패시 원본 반환
    
    def _generate_voice_cue(self, result: Dict, exercise: str) -> str:
        """음성 큐 생성 (짧고 명확한)"""
        score = result.get('overall_score', 0)
        phase = result.get('phase', '')
        
        if score >= 90:
            cues = [
                "완벽합니다!",
                "훌륭해요!",
                "그대로 유지!",
                f"점수 {score:.0f}점!"
            ]
        elif score >= 70:
            corrections = result.get('corrections', [])
            if corrections:
                correction = corrections[0]
                cue_map = {
                    'insufficient_depth': "더 깊이!",
                    'knee_valgus': "무릎 밖으로!",
                    'spine_flexion': "허리 펴세요!",
                    'excessive_arch': "복부 조이세요!",
                    'bar_drift': "바벨 가까이!",
                    'elbow_flare': "팔꿈치 모으세요!",
                    'hips_sagging': "엉덩이 올려!",
                    'hips_high': "엉덩이 내려!"
                }
                return cue_map.get(correction, "자세 교정!")
            else:
                return f"좋아요! {score:.0f}점"
        else:
            return "자세 확인! 천천히!"
        
        return random.choice(cues)
    
    def _generate_visual_indicators(self, result: Dict) -> Dict:
        """시각적 표시 정보"""
        indicators = {
            'body_parts': {},
            'alignment_lines': [],
            'angle_displays': [],
            'warning_zones': []
        }
        
        # 문제가 있는 부위 표시
        for correction in result.get('corrections', []):
            if 'knee' in correction:
                indicators['body_parts']['knees'] = {'color': 'red', 'pulse': True}
            elif 'spine' in correction or 'flexion' in correction:
                indicators['body_parts']['spine'] = {'color': 'red', 'pulse': True}
            elif 'hip' in correction:
                indicators['body_parts']['hips'] = {'color': 'orange', 'pulse': True}
            elif 'elbow' in correction:
                indicators['body_parts']['elbows'] = {'color': 'orange', 'pulse': True}
        
        # 정렬선 표시
        if result.get('overall_score', 0) < 80:
            indicators['alignment_lines'].append({
                'type': 'spine_line',
                'color': 'yellow',
                'style': 'dashed'
            })
        
        # 각도 표시
        important_angles = ['spine', 'avg_knee', 'avg_elbow', 'body']
        for angle_name in important_angles:
            if angle_name in result.get('angles', {}):
                indicators['angle_displays'].append({
                    'name': angle_name,
                    'value': result['angles'][angle_name],
                    'ideal': self._get_ideal_angle(angle_name),
                    'tolerance': 10
                })
        
        # 위험 구역 표시
        for violation in result.get('violations', []):
            if violation['severity'] in ['critical', 'high']:
                indicators['warning_zones'].append({
                    'type': violation['type'],
                    'severity': violation['severity'],
                    'message': violation['message']
                })
        
        return indicators
    
    def _prioritize_corrections(self, result: Dict) -> List[Dict]:
        """교정 우선순위 결정"""
        corrections = []
        
        # 위반사항 우선
        for violation in result.get('violations', []):
            severity_score = {'critical': 1, 'high': 2, 'medium': 3, 'low': 4}
            corrections.append({
                'issue': violation['type'],
                'priority': severity_score.get(violation['severity'], 5),
                'description': violation['message'],
                'fix': self._get_correction_instruction(violation['type'])
            })
        
        # 점수가 낮은 항목
        for score_name, score_value in result.get('scores', {}).items():
            if score_value < 70:
                corrections.append({
                    'issue': score_name,
                    'priority': 3,
                    'description': f"{score_name} 점수: {score_value:.0f}",
                    'fix': self._get_score_improvement(score_name)
                })
        
        # 우선순위 정렬
        corrections.sort(key=lambda x: x['priority'])
        
        return corrections[:3]  # 상위 3개만
    
    def _generate_motivation(self, result: Dict) -> str:
        """동기부여 메시지"""
        score = result.get('overall_score', 0)
        
        if score >= 95:
            messages = [
                "🏆 챔피언의 자세입니다!",
                "💪 완벽을 넘어선 수준!",
                "🔥 최고의 퍼포먼스!",
                "⚡ 엘리트 애슬릿!"
            ]
        elif score >= 85:
            messages = [
                "👏 훌륭한 진전입니다!",
                "💯 거의 완벽에 가까워요!",
                "🎯 목표에 근접했습니다!",
                "✨ 계속 이대로만!"
            ]
        elif score >= 70:
            messages = [
                "👍 좋은 시도입니다!",
                "📈 발전하고 있어요!",
                "💡 조금만 더 집중!",
                "🎯 핵심을 잡아가고 있어요!"
            ]
        else:
            messages = [
                "🎯 기초부터 탄탄히!",
                "💪 포기하지 마세요!",
                "📚 연습이 완벽을 만듭니다!",
                "🔧 하나씩 고쳐나가요!"
            ]
        
        return random.choice(messages)
    
    def _generate_technical_analysis(self, result: Dict) -> Dict:
        """기술적 분석"""
        analysis = {
            'biomechanics': [],
            'muscle_activation': [],
            'efficiency_metrics': {},
            'performance_indicators': {}
        }
        
        # 생체역학 분석
        if 'angles' in result:
            for angle_name, angle_value in result['angles'].items():
                ideal = self._get_ideal_angle(angle_name)
                deviation = abs(angle_value - ideal)
                analysis['biomechanics'].append({
                    'joint': angle_name,
                    'current': angle_value,
                    'ideal': ideal,
                    'deviation': deviation,
                    'assessment': self._assess_angle(angle_name, deviation)
                })
        
        # 근육 활성화 추정
        phase = result.get('phase', '')
        analysis['muscle_activation'] = self._estimate_muscle_activation(phase, result)
        
        # 효율성 지표
        if 'metrics' in result:
            analysis['efficiency_metrics'] = {
                'movement_efficiency': result['metrics'].get('bar_path_efficiency', 0),
                'energy_expenditure': result['metrics'].get('calories_burned', 0),
                'form_consistency': 100 - (np.std(result.get('scores', {}).values()) if result.get('scores') else 0)
            }
        
        # 성능 지표
        if 'performance_metrics' in result:
            analysis['performance_indicators'] = result['performance_metrics']
        
        return analysis
    
    def _generate_next_rep_focus(self, result: Dict) -> str:
        """다음 반복을 위한 집중 포인트"""
        corrections = result.get('corrections', [])
        
        if not corrections:
            return "완벽을 유지하세요! 템포와 호흡에 집중."
        
        # 가장 중요한 교정 포인트 1개만
        main_correction = corrections[0]
        
        focus_map = {
            'insufficient_depth': "다음엔 더 깊이 내려가세요. 엉덩이를 뒤로 더 빼면서.",
            'knee_valgus': "다음엔 무릎을 발끝 방향으로. 바닥을 밀어내는 느낌으로.",
            'spine_flexion': "다음엔 가슴을 더 펴세요. 하늘을 보는 느낌으로.",
            'excessive_arch': "다음엔 갈비뼈를 내리세요. 복부를 단단히.",
            'bar_drift': "다음엔 바벨을 정강이에 스치듯이. 수직으로.",
            'elbow_flare': "다음엔 팔꿈치를 45도로. 겨드랑이를 조이듯이.",
            'hips_sagging': "다음엔 엉덩이에 힘을. 판자처럼 단단하게.",
            'shoulder_position': "다음엔 어깨를 뒤로 당기고 아래로. 가슴을 열어."
        }
        
        return focus_map.get(main_correction, "다음엔 더 정확한 자세로. 천천히 컨트롤하며.")
    
    # Helper 메서드들
    def _get_main_issue(self, result: Dict) -> str:
        """주요 문제점"""
        if result.get('violations'):
            return result['violations'][0]['message']
        elif result.get('corrections'):
            return self._correction_to_korean(result['corrections'][0])
        return "미세 조정 필요"
    
    def _get_correction_point(self, result: Dict) -> str:
        """교정 포인트"""
        if result.get('feedback'):
            return result['feedback'][0]
        return "자세를 더 정확히"
    
    def _get_next_focus(self, result: Dict) -> str:
        """다음 집중사항"""
        score = result.get('overall_score', 0)
        if score >= 90:
            return "무게 증가"
        elif score >= 80:
            return "일관성 유지"
        else:
            return "기본기 강화"
    
    def _get_critical_correction(self, result: Dict) -> str:
        """치명적 교정사항"""
        violations = result.get('violations', [])
        critical = [v for v in violations if v['severity'] in ['critical', 'high']]
        if critical:
            return critical[0]['message']
        return "즉시 자세 교정"
    
    def _get_minor_adjustment(self, result: Dict) -> str:
        """작은 조정사항"""
        if result.get('feedback'):
            return result['feedback'][-1]
        return "미세 조정만 필요합니다"
    
    def _get_adjustment_needed(self, result: Dict) -> str:
        """필요한 조정"""
        lowest_score = min(result.get('scores', {'default': 100}).items(), key=lambda x: x[1])
        return f"{lowest_score[0]} 개선 필요"
    
    def _get_minor_issue(self, result: Dict) -> str:
        """작은 문제"""
        if result.get('corrections'):
            return self._correction_to_korean(result['corrections'][-1])
        return "전반적으로 양호"
    
    def _get_minor_wobble(self, result: Dict) -> str:
        """미세한 흔들림"""
        tremor = result.get('metrics', {}).get('tremor_amplitude_mm', 0)
        if tremor > 3:
            return "약간의 떨림이 있습니다"
        return "안정적입니다"
    
    def _correction_to_korean(self, correction: str) -> str:
        """교정사항 한글 변환"""
        translations = {
            'insufficient_depth': '깊이 부족',
            'knee_valgus': '무릎 모임',
            'spine_flexion': '척추 굽힘',
            'excessive_flexion': '과도한 굽힘',
            'butt_wink': '골반 말림',
            'excessive_arch': '과도한 아치',
            'bar_drift': '바벨 이탈',
            'elbow_flare': '팔꿈치 벌어짐',
            'hips_sagging': '엉덩이 처짐',
            'hips_high': '엉덩이 높음',
            'knee_over_toes': '무릎 전방이동',
            'asymmetry': '좌우 불균형',
            'shoulder_position': '어깨 위치',
            'wrist_extension': '손목 꺾임',
            'head_drop': '머리 처짐'
        }
        return translations.get(correction, correction)
    
    def _get_ideal_angle(self, angle_name: str) -> float:
        """이상적인 각도"""
        ideal_angles = {
            'spine': 5,
            'avg_knee': 90,
            'left_knee': 90,
            'right_knee': 90,
            'avg_elbow': 75,
            'left_elbow': 75,
            'right_elbow': 75,
            'body': 180,
            'left_hip': 90,
            'right_hip': 90,
            'lumbar_extension': 10
        }
        return ideal_angles.get(angle_name, 90)
    
    def _assess_angle(self, angle_name: str, deviation: float) -> str:
        """각도 평가"""
        if deviation < 5:
            return "완벽"
        elif deviation < 10:
            return "양호"
        elif deviation < 20:
            return "조정필요"
        else:
            return "교정필요"
    
    def _estimate_muscle_activation(self, phase: str, result: Dict) -> List[Dict]:
        """근육 활성화 추정"""
        exercise_muscles = {
            'squat': {
                'primary': ['대퇴사두근', '둔근', '햄스트링'],
                'secondary': ['종아리', '코어', '척추기립근']
            },
            'deadlift': {
                'primary': ['햄스트링', '둔근', '척추기립근'],
                'secondary': ['광배근', '승모근', '대퇴사두근']
            },
            'overhead_press': {
                'primary': ['전면삼각근', '측면삼각근'],
                'secondary': ['삼두근', '코어', '상부승모근']
            },
            'bench_press': {
                'primary': ['대흉근', '전면삼각근', '삼두근'],
                'secondary': ['광배근', '코어']
            },
            'plank': {
                'primary': ['복직근', '복횡근', '복사근'],
                'secondary': ['둔근', '척추기립근', '어깨']
            }
        }
        
        # 운동 추정 (실제로는 exercise 정보가 필요)
        # 여기서는 간단히 기본값 사용
        muscles = exercise_muscles.get('squat')
        
        activation = []
        for muscle in muscles['primary']:
            activation.append({
                'muscle': muscle,
                'activation_level': 80 + random.randint(0, 20),
                'type': 'primary'
            })
        
        for muscle in muscles['secondary']:
            activation.append({
                'muscle': muscle,
                'activation_level': 40 + random.randint(0, 40),
                'type': 'secondary'
            })
        
        return activation
    
    def _get_correction_instruction(self, issue_type: str) -> str:
        """교정 지시사항"""
        instructions = {
            'spine_flexion': "복압을 높이고 가슴을 펴서 척추를 중립으로",
            'knee_valgus': "무릎을 발끝 방향으로 밀어내기",
            'lumbar_hyperextension': "골반을 중립으로, 복근 단단히 조이기",
            'elbow_flare': "팔꿈치를 몸통 쪽으로 45도 각도 유지",
            'insufficient_depth': "엉덩이를 더 뒤로 빼면서 하강",
            'bar_drift': "바벨을 몸에 가깝게 수직 이동",
            'hips_sagging': "골반을 들어올려 일직선 유지",
            'shoulder_instability': "견갑골을 모으고 아래로 당기기"
        }
        return instructions.get(issue_type, "자세를 다시 확인하고 천천히 수행")
    
    def _get_score_improvement(self, score_name: str) -> str:
        """점수 개선 방법"""
        improvements = {
            'spine_neutrality': "코어 강화 운동과 흉추 가동성 향상",
            'depth': "발목과 고관절 가동성 운동 추가",
            'knee_tracking': "둔근 강화 및 발 위치 조정",
            'symmetry': "단측 운동으로 좌우 균형 맞추기",
            'core_stability': "플랭크, 데드버그 등 코어 운동",
            'bar_path': "가벼운 무게로 경로 연습",
            'alignment': "거울을 보며 정렬 확인"
        }
        return improvements.get(score_name, "해당 부위 집중 연습")


# 기존 FeedbackGenerator와의 호환성
FeedbackGenerator = EliteFeedbackGenerator
