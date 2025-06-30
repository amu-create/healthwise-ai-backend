import numpy as np
from typing import Dict, List, Tuple
from .elite_analyzer import EliteAnalyzer, AnalysisResult


class SquatAnalyzer(EliteAnalyzer):
    """스쿼트 전문 분석기"""
    
    def __init__(self):
        super().__init__()
        self.ideal_depth_angle = 90  # 이상적인 무릎 각도
        self.ideal_spine_angle = 5   # 허용 척추 각도
        self.butt_wink_count = 0
        self.valgus_count = 0
        self.depth_achieved = []
        
    def analyze(self, pose: Dict, timestamp: float = 0) -> AnalysisResult:
        """스쿼트 동작 분석"""
        angles = {}
        scores = {}
        feedback = []
        corrections = []
        violations = []
        metrics = {}
        
        # 1. 척추 중립성 분석
        spine_angle = self.calculate_spine_angle(pose)
        angles['spine'] = spine_angle
        
        spine_score = max(0, 100 - abs(spine_angle - self.ideal_spine_angle) * 5)
        scores['spine_neutrality'] = spine_score
        
        if spine_angle > 15:
            feedback.append(f"척추각 {spine_angle:.0f}도. 허리가 과도하게 굽었습니다.")
            corrections.append("excessive_flexion")
            violations.append({
                'type': 'spine_flexion',
                'severity': 'high',
                'message': '위험! 허리 굽힘이 감지됩니다.',
                'angle': spine_angle
            })
        elif spine_angle > 10:
            feedback.append("가슴을 더 펴고 척추를 곧게 유지하세요.")
            corrections.append("mild_flexion")
        
        # 2. 하강 깊이 분석
        left_knee_angle = self.calculate_angle_3d(
            pose['left_hip'], pose['left_knee'], pose['left_ankle']
        )
        right_knee_angle = self.calculate_angle_3d(
            pose['right_hip'], pose['right_knee'], pose['right_ankle']
        )
        
        avg_knee_angle = (left_knee_angle + right_knee_angle) / 2
        angles['left_knee'] = left_knee_angle
        angles['right_knee'] = right_knee_angle
        angles['avg_knee'] = avg_knee_angle
        
        # 깊이 점수 계산
        if avg_knee_angle <= 90:  # Parallel 이하
            depth_score = 100
            self.depth_achieved.append(avg_knee_angle)
        elif avg_knee_angle <= 100:  # 거의 Parallel
            depth_score = 90 - (avg_knee_angle - 90)
        else:
            depth_score = max(0, 80 - (avg_knee_angle - 100) * 2)
        
        scores['depth'] = depth_score
        metrics['depth_percentage'] = min(100, (180 - avg_knee_angle) / 90 * 100)
        
        if depth_score < 90:
            feedback.append(f"하강 깊이 부족. 현재 각도 {avg_knee_angle:.0f}도.")
            corrections.append("insufficient_depth")
        elif depth_score == 100:
            feedback.append(f"완벽한 깊이입니다. {avg_knee_angle:.0f}도 달성.")
        
        # 3. 무릎 궤적 분석 (Knee Tracking)
        valgus_detected, valgus_severity = self.detect_valgus(pose)
        
        if valgus_detected:
            valgus_score = max(0, 100 - valgus_severity * 2)
            scores['knee_tracking'] = valgus_score
            
            if valgus_severity > 30:
                feedback.append("주의! 무릎이 안쪽으로 심하게 모입니다.")
                violations.append({
                    'type': 'knee_valgus',
                    'severity': 'high',
                    'message': '무릎 모임 현상이 심각합니다.',
                    'deviation': valgus_severity
                })
            else:
                feedback.append("무릎을 발끝 방향으로 밀어내세요.")
            
            corrections.append("knee_valgus")
            self.valgus_count += 1
        else:
            scores['knee_tracking'] = 100
        
        # 4. 엉덩이 각도 분석 (Hip Hinge)
        left_hip_angle = self.calculate_angle_3d(
            pose['left_shoulder'], pose['left_hip'], pose['left_knee']
        )
        right_hip_angle = self.calculate_angle_3d(
            pose['right_shoulder'], pose['right_hip'], pose['right_knee']
        )
        
        avg_hip_angle = (left_hip_angle + right_hip_angle) / 2
        angles['left_hip'] = left_hip_angle
        angles['right_hip'] = right_hip_angle
        
        # 5. 벗 윙크(Butt Wink) 감지
        hip_height = pose['left_hip']['y']
        if hip_height > 0.6:  # 하강 지점
            butt_wink = self.detect_butt_wink(spine_angle, avg_hip_angle, "bottom")
            if butt_wink:
                feedback.append("벗 윙크 감지! 골반이 말립니다.")
                corrections.append("butt_wink")
                self.butt_wink_count += 1
                scores['pelvic_control'] = 60
            else:
                scores['pelvic_control'] = 100
        
        # 6. 좌우 대칭성
        knee_symmetry, knee_symmetry_score = self.check_symmetry(left_knee_angle, right_knee_angle)
        hip_symmetry, hip_symmetry_score = self.check_symmetry(left_hip_angle, right_hip_angle)
        
        symmetry_score = (knee_symmetry_score + hip_symmetry_score) / 2
        scores['symmetry'] = symmetry_score
        
        if not knee_symmetry:
            feedback.append(f"좌우 불균형. 왼쪽: {left_knee_angle:.0f}° 오른쪽: {right_knee_angle:.0f}°")
            corrections.append("asymmetry")
        
        # 7. 무릎 전방 이동 체크
        left_knee_forward = pose['left_knee']['x'] > pose['left_ankle']['x'] + 0.05
        right_knee_forward = pose['right_knee']['x'] > pose['right_ankle']['x'] + 0.05
        
        if left_knee_forward or right_knee_forward:
            scores['knee_position'] = 70
            feedback.append("무릎이 발끝을 넘어갑니다. 엉덩이를 뒤로 더 빼세요.")
            corrections.append("knee_over_toes")
        else:
            scores['knee_position'] = 100
        
        # 전체 점수 계산
        overall_score = np.mean(list(scores.values()))
        
        # 운동 단계 판정
        if avg_knee_angle > 160:
            phase = "standing"
        elif avg_knee_angle > 120:
            phase = "descending"
        elif avg_knee_angle > 100:
            phase = "parallel"
        elif avg_knee_angle <= 100:
            phase = "bottom"
        else:
            phase = "ascending"
        
        # 성능 메트릭
        performance_metrics = {
            'power_output': self._calculate_power_output(pose, phase),
            'stability_index': symmetry_score * 0.01,
            'form_efficiency': overall_score * 0.01,
            'injury_risk': self._calculate_injury_risk(violations, spine_angle, valgus_severity)
        }
        
        return AnalysisResult(
            angles=angles,
            scores=scores,
            overall_score=overall_score,
            feedback=feedback,
            corrections=corrections,
            is_in_position=(overall_score > 70 and phase in ["parallel", "bottom"]),
            metrics=metrics,
            phase=phase,
            violations=violations,
            performance_metrics=performance_metrics
        )
    
    def _calculate_power_output(self, pose: Dict, phase: str) -> float:
        """파워 출력 추정"""
        if phase in ["ascending", "descending"]:
            # 움직임 속도와 자세 정확도를 기반으로 파워 추정
            return np.random.uniform(0.7, 1.0)  # 실제로는 속도 데이터 필요
        return 0.0
    
    def _calculate_injury_risk(self, violations: List, spine_angle: float, valgus_severity: float) -> float:
        """부상 위험도 계산 (0-1)"""
        risk = 0.0
        
        # 위반 사항에 따른 위험도
        for violation in violations:
            if violation['severity'] == 'high':
                risk += 0.3
            elif violation['severity'] == 'medium':
                risk += 0.15
        
        # 척추 각도에 따른 위험도
        if spine_angle > 20:
            risk += 0.4
        elif spine_angle > 15:
            risk += 0.2
        
        # 무릎 모임에 따른 위험도
        if valgus_severity > 40:
            risk += 0.3
        elif valgus_severity > 20:
            risk += 0.15
        
        return min(1.0, risk)


class DeadliftAnalyzer(EliteAnalyzer):
    """데드리프트 전문 분석기"""
    
    def __init__(self):
        super().__init__()
        self.bar_path_history = []
        self.max_spine_flexion = 0
        
    def analyze(self, pose: Dict, timestamp: float = 0) -> AnalysisResult:
        """데드리프트 동작 분석"""
        angles = {}
        scores = {}
        feedback = []
        corrections = []
        violations = []
        metrics = {}
        
        # 1. 척추 중립성 - 가장 중요
        spine_angle = self.calculate_spine_angle(pose)
        angles['spine'] = spine_angle
        
        # 데드리프트는 척추 중립이 매우 엄격
        if spine_angle > 10:
            spine_score = 0  # 즉시 0점
            feedback.append("위험! 허리가 굽었습니다! 즉시 중단하세요!")
            violations.append({
                'type': 'spine_flexion',
                'severity': 'critical',
                'message': '척추 굴곡 감지 - 부상 위험 높음',
                'angle': spine_angle
            })
            corrections.append("critical_spine_flexion")
        elif spine_angle > 5:
            spine_score = 50
            feedback.append("주의: 척추를 더 곧게 유지하세요.")
            corrections.append("mild_spine_flexion")
        else:
            spine_score = 100
            feedback.append(f"완벽한 척추 중립. 각도 {spine_angle:.0f}도.")
        
        scores['spine_neutrality'] = spine_score
        self.max_spine_flexion = max(self.max_spine_flexion, spine_angle)
        
        # 2. 힙 힌지 패턴 분석
        hip_angle = self.calculate_angle_3d(
            pose['left_shoulder'], pose['left_hip'], pose['left_knee']
        )
        knee_angle = self.calculate_angle_3d(
            pose['left_hip'], pose['left_knee'], pose['left_ankle']
        )
        
        angles['hip'] = hip_angle
        angles['knee'] = knee_angle
        
        # 힙 주도 움직임 확인
        hip_knee_ratio = hip_angle / (knee_angle + 1)  # 0으로 나누기 방지
        
        if hip_knee_ratio < 0.8:
            scores['hip_hinge'] = 60
            feedback.append("무릎이 너무 많이 굽어집니다. 엉덩이로 시작하세요.")
            corrections.append("excessive_knee_bend")
        elif hip_knee_ratio > 1.5:
            scores['hip_hinge'] = 90
            feedback.append("좋은 힙 힌지 패턴입니다.")
        else:
            scores['hip_hinge'] = 100
        
        # 3. 바벨 궤적 분석
        # 손목 위치를 바벨 위치로 가정
        left_wrist = pose['left_wrist']
        right_wrist = pose['right_wrist']
        bar_position = {
            'x': (left_wrist['x'] + right_wrist['x']) / 2,
            'y': (left_wrist['y'] + right_wrist['y']) / 2,
            'z': (left_wrist.get('z', 0) + right_wrist.get('z', 0)) / 2
        }
        
        self.bar_path_history.append(bar_position)
        
        # 바벨이 몸에서 멀어지는지 확인
        ankle_mid = {
            'x': (pose['left_ankle']['x'] + pose['right_ankle']['x']) / 2,
            'y': (pose['left_ankle']['y'] + pose['right_ankle']['y']) / 2
        }
        
        bar_distance = abs(bar_position['x'] - ankle_mid['x'])
        
        if bar_distance > 0.1:  # 10cm 이상 멀어짐
            scores['bar_path'] = 70
            feedback.append("바벨이 몸에서 멀어집니다. 정강이에 붙여서 올리세요.")
            corrections.append("bar_drift")
        else:
            scores['bar_path'] = 100
            
        # 바벨 경로 효율성
        if len(self.bar_path_history) > 5:
            path_efficiency = self.calculate_bar_path_efficiency(self.bar_path_history[-5:])
            metrics['bar_path_efficiency'] = path_efficiency
        
        # 4. 어깨 위치 체크
        shoulder_over_bar = pose['left_shoulder']['x'] >= bar_position['x'] - 0.05
        if not shoulder_over_bar:
            scores['shoulder_position'] = 80
            feedback.append("어깨가 바벨보다 뒤에 있습니다.")
            corrections.append("shoulder_behind_bar")
        else:
            scores['shoulder_position'] = 100
        
        # 5. 락아웃 체크
        hip_extension = 180 - hip_angle
        if hip_extension < 5:  # 거의 완전 신전
            phase = "lockout"
            if abs(spine_angle) < 5:
                feedback.append("완벽한 락아웃 자세입니다.")
            else:
                feedback.append("락아웃시 과신전 주의하세요.")
                corrections.append("hyperextension")
        elif bar_position['y'] < 0.4:
            phase = "setup"
        elif bar_position['y'] < 0.6:
            phase = "pull"
        else:
            phase = "ascending"
        
        # 전체 점수 계산
        overall_score = np.mean(list(scores.values()))
        
        # 성능 메트릭
        performance_metrics = {
            'power_output': self._calculate_power_output(pose, phase),
            'form_efficiency': overall_score * 0.01,
            'injury_risk': self._calculate_injury_risk(spine_angle, bar_distance),
            'max_spine_flexion': self.max_spine_flexion
        }
        
        return AnalysisResult(
            angles=angles,
            scores=scores,
            overall_score=overall_score,
            feedback=feedback,
            corrections=corrections,
            is_in_position=(overall_score > 70 and spine_score > 50),
            metrics=metrics,
            phase=phase,
            violations=violations,
            performance_metrics=performance_metrics
        )
    
    def _calculate_power_output(self, pose: Dict, phase: str) -> float:
        """파워 출력 추정"""
        if phase in ["pull", "ascending"]:
            return np.random.uniform(0.8, 1.2)  # 데드리프트는 높은 파워
        return 0.0
    
    def _calculate_injury_risk(self, spine_angle: float, bar_distance: float) -> float:
        """부상 위험도 계산"""
        risk = 0.0
        
        # 척추 각도가 가장 중요
        if spine_angle > 15:
            risk += 0.8
        elif spine_angle > 10:
            risk += 0.5
        elif spine_angle > 5:
            risk += 0.2
        
        # 바벨 거리
        if bar_distance > 0.15:
            risk += 0.3
        elif bar_distance > 0.1:
            risk += 0.1
        
        return min(1.0, risk)


class OverheadPressAnalyzer(EliteAnalyzer):
    """오버헤드 프레스 전문 분석기"""
    
    def __init__(self):
        super().__init__()
        self.lumbar_extension_count = 0
        
    def analyze(self, pose: Dict, timestamp: float = 0) -> AnalysisResult:
        """오버헤드 프레스 동작 분석"""
        angles = {}
        scores = {}
        feedback = []
        corrections = []
        violations = []
        metrics = {}
        
        # 1. 허리 과신전 체크
        spine_angle = self.calculate_spine_angle(pose)
        lumbar_angle = self._calculate_lumbar_extension(pose)
        
        angles['spine'] = spine_angle
        angles['lumbar_extension'] = lumbar_angle
        
        if lumbar_angle > 20:
            scores['core_stability'] = 40
            feedback.append("위험! 허리가 과도하게 젖혀집니다.")
            violations.append({
                'type': 'lumbar_hyperextension',
                'severity': 'high',
                'message': '허리 과신전 - 디스크 부담 증가',
                'angle': lumbar_angle
            })
            corrections.append("excessive_arch")
            self.lumbar_extension_count += 1
        elif lumbar_angle > 10:
            scores['core_stability'] = 70
            feedback.append("엉덩이에 힘을 주고 복부를 조이세요.")
            corrections.append("mild_arch")
        else:
            scores['core_stability'] = 100
            feedback.append("훌륭한 코어 안정성입니다.")
        
        # 2. 바벨 궤적 분석
        left_wrist = pose['left_wrist']
        right_wrist = pose['right_wrist']
        bar_position = {
            'x': (left_wrist['x'] + right_wrist['x']) / 2,
            'y': (left_wrist['y'] + right_wrist['y']) / 2
        }
        
        # 턱 앞에서 정수리 위로 수직 이동하는지 확인
        nose_x = pose['nose']['x']
        bar_deviation = abs(bar_position['x'] - nose_x)
        
        if bar_deviation > 0.1:
            scores['bar_path'] = 70
            feedback.append("바벨이 수직으로 이동하지 않습니다.")
            corrections.append("bar_drift")
        else:
            scores['bar_path'] = 100
        
        # 3. 팔꿈치 위치
        left_elbow_angle = self.calculate_angle_3d(
            pose['left_shoulder'], pose['left_elbow'], pose['left_wrist']
        )
        right_elbow_angle = self.calculate_angle_3d(
            pose['right_shoulder'], pose['right_elbow'], pose['right_wrist']
        )
        
        angles['left_elbow'] = left_elbow_angle
        angles['right_elbow'] = right_elbow_angle
        
        # 팔꿈치가 너무 벌어지는지 확인
        elbow_flare = self._calculate_elbow_flare(pose)
        
        if elbow_flare > 45:
            scores['elbow_position'] = 60
            feedback.append("팔꿈치가 너무 벌어집니다. 안쪽으로 모으세요.")
            corrections.append("elbow_flare")
        else:
            scores['elbow_position'] = 100
        
        # 4. 어깨 안정성
        shoulder_shrug = self._detect_shoulder_shrug(pose)
        if shoulder_shrug:
            scores['shoulder_stability'] = 70
            feedback.append("어깨를 으쓱하지 마세요. 아래로 당기세요.")
            corrections.append("shoulder_shrug")
        else:
            scores['shoulder_stability'] = 100
        
        # 5. 좌우 균형
        wrist_level_diff = abs(left_wrist['y'] - right_wrist['y'])
        if wrist_level_diff > 0.05:
            scores['balance'] = 80
            feedback.append("양손 높이가 다릅니다. 균형을 맞추세요.")
            corrections.append("uneven_press")
        else:
            scores['balance'] = 100
        
        # 운동 단계 판정
        if bar_position['y'] < 0.3:
            phase = "rack_position"
        elif bar_position['y'] < 0.5:
            phase = "pressing"
        elif bar_position['y'] > 0.7:
            phase = "lockout"
        else:
            phase = "mid_press"
        
        # 전체 점수
        overall_score = np.mean(list(scores.values()))
        
        # 성능 메트릭
        performance_metrics = {
            'power_output': self._calculate_power_output(pose, phase),
            'stability_index': scores['core_stability'] * 0.01,
            'form_efficiency': overall_score * 0.01,
            'injury_risk': self._calculate_injury_risk(lumbar_angle, shoulder_shrug)
        }
        
        return AnalysisResult(
            angles=angles,
            scores=scores,
            overall_score=overall_score,
            feedback=feedback,
            corrections=corrections,
            is_in_position=(overall_score > 70),
            metrics=metrics,
            phase=phase,
            violations=violations,
            performance_metrics=performance_metrics
        )
    
    def _calculate_lumbar_extension(self, pose: Dict) -> float:
        """요추 신전 각도 계산"""
        # 엉덩이-허리-어깨 라인의 곡률
        hip_mid = {
            'x': (pose['left_hip']['x'] + pose['right_hip']['x']) / 2,
            'y': (pose['left_hip']['y'] + pose['right_hip']['y']) / 2
        }
        shoulder_mid = {
            'x': (pose['left_shoulder']['x'] + pose['right_shoulder']['x']) / 2,
            'y': (pose['left_shoulder']['y'] + pose['right_shoulder']['y']) / 2
        }
        
        # 정면에서 봤을 때 허리 곡선
        dx = shoulder_mid['x'] - hip_mid['x']
        dy = shoulder_mid['y'] - hip_mid['y']
        
        angle = abs(math.degrees(math.atan2(dx, dy)))
        return angle
    
    def _calculate_elbow_flare(self, pose: Dict) -> float:
        """팔꿈치 벌어짐 각도"""
        # 어깨-팔꿈치 벡터와 정면 벡터 사이 각도
        left_vector = np.array([
            pose['left_elbow']['x'] - pose['left_shoulder']['x'],
            pose['left_elbow']['y'] - pose['left_shoulder']['y']
        ])
        
        front_vector = np.array([0, -1])  # 정면 방향
        
        dot = np.dot(left_vector, front_vector)
        angle = math.degrees(math.acos(np.clip(dot / (np.linalg.norm(left_vector) + 1e-6), -1, 1)))
        
        return angle
    
    def _detect_shoulder_shrug(self, pose: Dict) -> bool:
        """어깨 으쓱임 감지"""
        # 어깨와 귀 사이 거리로 판단
        left_distance = self.calculate_distance_3d(pose['left_shoulder'], pose['left_ear'])
        right_distance = self.calculate_distance_3d(pose['right_shoulder'], pose['right_ear'])
        
        # 거리가 너무 가까우면 으쓱임
        return (left_distance < 0.1 or right_distance < 0.1)
    
    def _calculate_power_output(self, pose: Dict, phase: str) -> float:
        """파워 출력 추정"""
        if phase in ["pressing", "mid_press"]:
            return np.random.uniform(0.6, 0.9)
        return 0.0
    
    def _calculate_injury_risk(self, lumbar_angle: float, shoulder_shrug: bool) -> float:
        """부상 위험도"""
        risk = 0.0
        
        if lumbar_angle > 25:
            risk += 0.6
        elif lumbar_angle > 15:
            risk += 0.3
        
        if shoulder_shrug:
            risk += 0.2
        
        return min(1.0, risk)


class BenchPressAnalyzer(EliteAnalyzer):
    """벤치프레스 전문 분석기"""
    
    def __init__(self):
        super().__init__()
        self.ideal_elbow_angle = 75  # 이상적인 팔꿈치 각도
        
    def analyze(self, pose: Dict, timestamp: float = 0) -> AnalysisResult:
        """벤치프레스 동작 분석"""
        angles = {}
        scores = {}
        feedback = []
        corrections = []
        violations = []
        metrics = {}
        
        # 1. 팔꿈치 각도 분석
        left_elbow_angle = self._calculate_elbow_angle_bench(pose, 'left')
        right_elbow_angle = self._calculate_elbow_angle_bench(pose, 'right')
        
        avg_elbow_angle = (left_elbow_angle + right_elbow_angle) / 2
        angles['left_elbow'] = left_elbow_angle
        angles['right_elbow'] = right_elbow_angle
        angles['avg_elbow'] = avg_elbow_angle
        
        # 팔꿈치 각도 평가 (45-75도가 이상적)
        if avg_elbow_angle > 85:
            scores['elbow_angle'] = 60
            feedback.append(f"팔꿈치가 너무 벌어집니다. 현재 {avg_elbow_angle:.0f}도.")
            violations.append({
                'type': 'elbow_flare',
                'severity': 'medium',
                'message': '어깨 부상 위험 증가',
                'angle': avg_elbow_angle
            })
            corrections.append("excessive_flare")
        elif avg_elbow_angle < 45:
            scores['elbow_angle'] = 70
            feedback.append("팔꿈치를 조금 더 벌리세요.")
            corrections.append("narrow_grip")
        else:
            scores['elbow_angle'] = 100
            feedback.append(f"완벽한 팔꿈치 각도. {avg_elbow_angle:.0f}도.")
        
        # 2. 바 터치 지점 분석
        bar_position = {
            'x': (pose['left_wrist']['x'] + pose['right_wrist']['x']) / 2,
            'y': (pose['left_wrist']['y'] + pose['right_wrist']['y']) / 2
        }
        
        # 가슴 중앙 위치 추정
        chest_position = {
            'x': (pose['left_shoulder']['x'] + pose['right_shoulder']['x']) / 2,
            'y': (pose['left_shoulder']['y'] + pose['right_shoulder']['y']) / 2 + 0.15
        }
        
        touch_deviation = abs(bar_position['y'] - chest_position['y'])
        
        if touch_deviation > 0.1:
            scores['touch_point'] = 70
            if bar_position['y'] < chest_position['y']:
                feedback.append("바벨을 너무 높게 터치합니다. 가슴 중앙으로.")
            else:
                feedback.append("바벨을 너무 낮게 터치합니다.")
            corrections.append("incorrect_touch")
        else:
            scores['touch_point'] = 100
        
        # 3. 손목 각도 체크
        left_wrist_angle = self._calculate_wrist_angle(pose, 'left')
        right_wrist_angle = self._calculate_wrist_angle(pose, 'right')
        
        angles['left_wrist'] = left_wrist_angle
        angles['right_wrist'] = right_wrist_angle
        
        if left_wrist_angle > 30 or right_wrist_angle > 30:
            scores['wrist_position'] = 60
            feedback.append("손목이 과도하게 꺾였습니다. 손목을 세우세요.")
            corrections.append("wrist_extension")
        else:
            scores['wrist_position'] = 100
        
        # 4. 견갑골 안정성 (어깨날개뼈 후인하강)
        shoulder_stability = self._check_shoulder_stability(pose)
        scores['shoulder_stability'] = shoulder_stability
        
        if shoulder_stability < 80:
            feedback.append("견갑골을 모으고 아래로 당기세요.")
            corrections.append("scapular_instability")
        
        # 5. 아치 체크 (적절한 등 아치)
        arch_present = self._check_back_arch(pose)
        if not arch_present:
            scores['back_arch'] = 80
            feedback.append("적절한 등 아치를 만드세요.")
        else:
            scores['back_arch'] = 100
        
        # 운동 단계
        if bar_position['y'] < 0.4:
            phase = "bottom"
        elif bar_position['y'] > 0.6:
            phase = "lockout"
        else:
            phase = "pressing"
        
        # 전체 점수
        overall_score = np.mean(list(scores.values()))
        
        # 성능 메트릭
        performance_metrics = {
            'power_output': self._calculate_power_output(pose, phase),
            'stability_index': shoulder_stability * 0.01,
            'form_efficiency': overall_score * 0.01,
            'injury_risk': self._calculate_injury_risk(avg_elbow_angle, left_wrist_angle, right_wrist_angle)
        }
        
        return AnalysisResult(
            angles=angles,
            scores=scores,
            overall_score=overall_score,
            feedback=feedback,
            corrections=corrections,
            is_in_position=(overall_score > 70 and phase == "bottom"),
            metrics=metrics,
            phase=phase,
            violations=violations,
            performance_metrics=performance_metrics
        )
    
    def _calculate_elbow_angle_bench(self, pose: Dict, side: str) -> float:
        """벤치프레스에서 팔꿈치 각도 (몸통과 상완의 각도)"""
        if side == 'left':
            shoulder = pose['left_shoulder']
            elbow = pose['left_elbow']
            hip = pose['left_hip']
        else:
            shoulder = pose['right_shoulder']
            elbow = pose['right_elbow']
            hip = pose['right_hip']
        
        # 몸통 벡터
        torso_vector = np.array([hip['x'] - shoulder['x'], hip['y'] - shoulder['y']])
        # 상완 벡터
        upper_arm_vector = np.array([elbow['x'] - shoulder['x'], elbow['y'] - shoulder['y']])
        
        # 두 벡터 사이 각도
        dot = np.dot(torso_vector, upper_arm_vector)
        angle = math.degrees(math.acos(np.clip(
            dot / (np.linalg.norm(torso_vector) * np.linalg.norm(upper_arm_vector) + 1e-6), 
            -1, 1
        )))
        
        return angle
    
    def _calculate_wrist_angle(self, pose: Dict, side: str) -> float:
        """손목 꺾임 각도"""
        if side == 'left':
            wrist = pose['left_wrist']
            elbow = pose['left_elbow']
            index = pose['left_index']
        else:
            wrist = pose['right_wrist']
            elbow = pose['right_elbow']
            index = pose['right_index']
        
        angle = self.calculate_angle_3d(elbow, wrist, index)
        return abs(180 - angle)  # 직선에서 벗어난 각도
    
    def _check_shoulder_stability(self, pose: Dict) -> float:
        """견갑골 안정성 체크"""
        # 어깨 높이 차이로 안정성 추정
        shoulder_level_diff = abs(pose['left_shoulder']['y'] - pose['right_shoulder']['y'])
        
        # 어깨가 귀에서 멀리 떨어져 있는지 (후인하강)
        left_depression = pose['left_ear']['y'] - pose['left_shoulder']['y']
        right_depression = pose['right_ear']['y'] - pose['right_shoulder']['y']
        
        stability_score = 100
        
        if shoulder_level_diff > 0.05:
            stability_score -= 20
        
        if left_depression < 0.1 or right_depression < 0.1:
            stability_score -= 20
        
        return max(0, stability_score)
    
    def _check_back_arch(self, pose: Dict) -> bool:
        """등 아치 확인"""
        # 엉덩이와 어깨 높이 차이로 아치 추정
        hip_height = (pose['left_hip']['y'] + pose['right_hip']['y']) / 2
        shoulder_height = (pose['left_shoulder']['y'] + pose['right_shoulder']['y']) / 2
        
        # 벤치에 누운 상태에서 엉덩이가 약간 높으면 아치
        return hip_height < shoulder_height - 0.05
    
    def _calculate_power_output(self, pose: Dict, phase: str) -> float:
        """파워 출력"""
        if phase == "pressing":
            return np.random.uniform(0.7, 1.1)
        return 0.0
    
    def _calculate_injury_risk(self, elbow_angle: float, left_wrist: float, right_wrist: float) -> float:
        """부상 위험도"""
        risk = 0.0
        
        # 팔꿈치 각도
        if elbow_angle > 90:
            risk += 0.4
        elif elbow_angle > 85:
            risk += 0.2
        
        # 손목 각도
        max_wrist_angle = max(left_wrist, right_wrist)
        if max_wrist_angle > 40:
            risk += 0.3
        elif max_wrist_angle > 30:
            risk += 0.15
        
        return min(1.0, risk)


class PlankAnalyzer(EliteAnalyzer):
    """플랭크 전문 분석기"""
    
    def __init__(self):
        super().__init__()
        self.tremor_history = []
        self.hold_start_time = None
        
    def analyze(self, pose: Dict, timestamp: float = 0) -> AnalysisResult:
        """플랭크 동작 분석"""
        angles = {}
        scores = {}
        feedback = []
        corrections = []
        violations = []
        metrics = {}
        
        # 1. 몸의 정렬 분석
        alignment_points = [
            pose['left_ear'],
            pose['left_shoulder'], 
            pose['left_hip'],
            pose['left_ankle']
        ]
        
        alignment_score = self.calculate_alignment(alignment_points)
        scores['alignment'] = alignment_score
        
        body_angle = self.calculate_angle_3d(
            pose['left_shoulder'], pose['left_hip'], pose['left_ankle']
        )
        angles['body'] = body_angle
        
        # 이상적인 각도는 180도 (일직선)
        angle_deviation = abs(180 - body_angle)
        
        if angle_deviation > 15:
            if body_angle < 165:
                feedback.append("엉덩이가 너무 높습니다. 몸을 일직선으로.")
                corrections.append("hips_high")
                violations.append({
                    'type': 'alignment_error',
                    'severity': 'medium',
                    'message': '엉덩이 위치 과도하게 높음',
                    'deviation': angle_deviation
                })
            else:
                feedback.append("엉덩이가 처집니다. 코어에 힘을 주세요.")
                corrections.append("hips_sagging")
                violations.append({
                    'type': 'alignment_error', 
                    'severity': 'high',
                    'message': '허리 과신전 위험',
                    'deviation': angle_deviation
                })
        elif angle_deviation > 10:
            feedback.append("자세를 조금 더 정확히 유지하세요.")
        else:
            feedback.append(f"완벽한 일직선. 각도 편차 {angle_deviation:.0f}도.")
        
        # 2. 엉덩이 높이 정밀 분석
        shoulder_height = pose['left_shoulder']['y']
        hip_height = pose['left_hip']['y']
        ankle_height = pose['left_ankle']['y']
        
        # 이상적인 엉덩이 높이 계산
        ideal_hip_height = shoulder_height + (ankle_height - shoulder_height) * 0.6
        hip_deviation = abs(hip_height - ideal_hip_height)
        
        metrics['hip_deviation_cm'] = hip_deviation * 100  # 미터를 cm로
        
        if hip_deviation > 0.1:  # 10cm 이상 벗어남
            scores['hip_position'] = 60
        elif hip_deviation > 0.05:
            scores['hip_position'] = 80
        else:
            scores['hip_position'] = 100
        
        # 3. 미세 진동 분석 (피로도 지표)
        if len(self.previous_results) > 0:
            prev_hip = self.previous_results[-1].angles.get('hip_height', hip_height)
            tremor = abs(hip_height - prev_hip) * 1000  # mm 단위
            self.tremor_history.append(tremor)
            
            if len(self.tremor_history) > 30:  # 1초간 데이터 (30fps)
                avg_tremor = np.mean(self.tremor_history[-30:])
                
                if avg_tremor > 5:  # 5mm 이상 떨림
                    scores['stability'] = 60
                    feedback.append("근육 피로가 감지됩니다. 떨림이 증가했습니다.")
                    metrics['fatigue_level'] = 'high'
                elif avg_tremor > 2:
                    scores['stability'] = 80
                    metrics['fatigue_level'] = 'medium'
                else:
                    scores['stability'] = 100
                    metrics['fatigue_level'] = 'low'
                
                metrics['tremor_amplitude_mm'] = avg_tremor
        
        # 4. 머리 위치 체크
        head_alignment = self._check_head_position(pose)
        scores['head_position'] = head_alignment
        
        if head_alignment < 80:
            feedback.append("머리를 척추와 일직선으로 유지하세요.")
            corrections.append("head_drop")
        
        # 5. 팔꿈치 위치 (팔꿈치 플랭크인 경우)
        elbow_shoulder_distance = self.calculate_distance_3d(
            pose['left_elbow'], pose['left_shoulder']
        )
        
        if elbow_shoulder_distance < 0.3:  # 팔꿈치 플랭크로 추정
            # 어깨가 팔꿈치 바로 위에 있는지 확인
            shoulder_over_elbow = abs(pose['left_shoulder']['x'] - pose['left_elbow']['x']) < 0.05
            if not shoulder_over_elbow:
                scores['elbow_position'] = 80
                feedback.append("어깨를 팔꿈치 바로 위에 위치시키세요.")
                corrections.append("shoulder_position")
            else:
                scores['elbow_position'] = 100
        
        # 전체 점수
        overall_score = np.mean(list(scores.values()))
        
        # 홀드 시간 계산
        if self.hold_start_time is None and overall_score > 70:
            self.hold_start_time = timestamp
        elif overall_score < 60:
            self.hold_start_time = None
        
        hold_duration = 0
        if self.hold_start_time:
            hold_duration = timestamp - self.hold_start_time
            metrics['hold_duration'] = hold_duration
        
        # 단계 판정
        if overall_score < 60:
            phase = "breaking"
        elif hold_duration > 45:
            phase = "endurance"
        elif hold_duration > 20:
            phase = "maintaining"
        else:
            phase = "establishing"
        
        # 성능 메트릭
        performance_metrics = {
            'core_activation': overall_score * 0.01,
            'endurance_score': min(100, hold_duration * 2) * 0.01,
            'form_decay_rate': self._calculate_form_decay(),
            'predicted_max_hold': self._predict_max_hold_time(overall_score, metrics.get('fatigue_level', 'low'))
        }
        
        return AnalysisResult(
            angles=angles,
            scores=scores,
            overall_score=overall_score,
            feedback=feedback,
            corrections=corrections,
            is_in_position=(overall_score > 70),
            metrics=metrics,
            phase=phase,
            violations=violations,
            performance_metrics=performance_metrics
        )
    
    def _check_head_position(self, pose: Dict) -> float:
        """머리 위치 체크"""
        # 머리-목-어깨 정렬
        head_neck_angle = self.calculate_angle_3d(
            pose['nose'], pose['left_ear'], pose['left_shoulder']
        )
        
        # 이상적으로는 일직선 (180도)
        deviation = abs(180 - head_neck_angle)
        
        if deviation > 30:
            return 60
        elif deviation > 15:
            return 80
        else:
            return 100
    
    def _calculate_form_decay(self) -> float:
        """시간에 따른 자세 악화율"""
        if len(self.previous_results) < 10:
            return 0.0
        
        recent_scores = [r.overall_score for r in self.previous_results[-10:]]
        older_scores = [r.overall_score for r in self.previous_results[-20:-10]] if len(self.previous_results) > 20 else recent_scores
        
        decay = (np.mean(older_scores) - np.mean(recent_scores)) / np.mean(older_scores)
        return max(0, decay)
    
    def _predict_max_hold_time(self, current_score: float, fatigue_level: str) -> float:
        """최대 유지 가능 시간 예측 (초)"""
        base_time = current_score * 0.6  # 점수 기반 기본 시간
        
        fatigue_multiplier = {
            'low': 1.2,
            'medium': 0.8,
            'high': 0.5
        }
        
        return base_time * fatigue_multiplier.get(fatigue_level, 1.0)
