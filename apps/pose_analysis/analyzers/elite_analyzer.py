import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import math


@dataclass
class AnalysisResult:
    """분석 결과 데이터 클래스"""
    angles: Dict[str, float]
    scores: Dict[str, float]
    overall_score: float
    feedback: List[str]
    corrections: List[str]
    is_in_position: bool
    metrics: Dict[str, Any]
    phase: str = "unknown"
    violations: List[Dict[str, Any]] = None
    performance_metrics: Dict[str, float] = None
    
    def __post_init__(self):
        if self.violations is None:
            self.violations = []
        if self.performance_metrics is None:
            self.performance_metrics = {}


class EliteAnalyzer:
    """엘리트 트레이너 수준의 운동 분석 베이스 클래스"""
    
    # 신체 키포인트 인덱스
    LANDMARKS = {
        'nose': 0, 'left_eye_inner': 1, 'left_eye': 2, 'left_eye_outer': 3,
        'right_eye_inner': 4, 'right_eye': 5, 'right_eye_outer': 6,
        'left_ear': 7, 'right_ear': 8, 'mouth_left': 9, 'mouth_right': 10,
        'left_shoulder': 11, 'right_shoulder': 12, 'left_elbow': 13,
        'right_elbow': 14, 'left_wrist': 15, 'right_wrist': 16,
        'left_pinky': 17, 'right_pinky': 18, 'left_index': 19,
        'right_index': 20, 'left_thumb': 21, 'right_thumb': 22,
        'left_hip': 23, 'right_hip': 24, 'left_knee': 25,
        'right_knee': 26, 'left_ankle': 27, 'right_ankle': 28,
        'left_heel': 29, 'right_heel': 30, 'left_foot_index': 31,
        'right_foot_index': 32
    }
    
    def __init__(self):
        self.min_detection_confidence = 0.7
        self.min_tracking_confidence = 0.7
        self.previous_results = []
        self.rep_counter = 0
        self.current_phase = "ready"
        self.phase_history = []
        self.violation_history = []
        
    def calculate_angle_3d(self, p1: Dict, p2: Dict, p3: Dict) -> float:
        """3D 공간에서 세 점 사이의 각도 계산"""
        try:
            a = np.array([p1['x'], p1['y'], p1.get('z', 0)])
            b = np.array([p2['x'], p2['y'], p2.get('z', 0)])
            c = np.array([p3['x'], p3['y'], p3.get('z', 0)])
            
            ba = a - b
            bc = c - b
            
            cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
            angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
            
            return np.degrees(angle)
        except:
            return 0
    
    def calculate_angle_2d(self, p1: Dict, p2: Dict, p3: Dict, plane: str = 'xy') -> float:
        """특정 평면에서의 각도 계산"""
        if plane == 'xy':
            a = np.array([p1['x'], p1['y']])
            b = np.array([p2['x'], p2['y']])
            c = np.array([p3['x'], p3['y']])
        elif plane == 'xz':
            a = np.array([p1['x'], p1.get('z', 0)])
            b = np.array([p2['x'], p2.get('z', 0)])
            c = np.array([p3['x'], c.get('z', 0)])
        elif plane == 'yz':
            a = np.array([p1['y'], p1.get('z', 0)])
            b = np.array([p2['y'], p2.get('z', 0)])
            c = np.array([p3['y'], c.get('z', 0)])
        else:
            return 0
            
        ba = a - b
        bc = c - b
        
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
        angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
        
        return np.degrees(angle)
    
    def calculate_distance_3d(self, p1: Dict, p2: Dict) -> float:
        """3D 공간에서 두 점 사이의 거리"""
        return math.sqrt(
            (p1['x'] - p2['x'])**2 + 
            (p1['y'] - p2['y'])**2 + 
            (p1.get('z', 0) - p2.get('z', 0))**2
        )
    
    def calculate_velocity(self, current_pos: Dict, previous_pos: Dict, dt: float = 0.033) -> float:
        """속도 계산 (프레임 간격 기본 30fps)"""
        if not previous_pos:
            return 0
        distance = self.calculate_distance_3d(current_pos, previous_pos)
        return distance / dt
    
    def calculate_alignment(self, points: List[Dict]) -> float:
        """여러 점들의 일직선 정렬도 계산 (0-100)"""
        if len(points) < 3:
            return 100
        
        # 최소제곱법으로 직선 피팅
        x_coords = [p['x'] for p in points]
        y_coords = [p['y'] for p in points]
        
        # 선형 회귀
        A = np.vstack([x_coords, np.ones(len(x_coords))]).T
        m, c = np.linalg.lstsq(A, y_coords, rcond=None)[0]
        
        # 각 점의 직선으로부터의 거리 계산
        total_error = 0
        for x, y in zip(x_coords, y_coords):
            predicted_y = m * x + c
            error = abs(y - predicted_y)
            total_error += error
        
        avg_error = total_error / len(points)
        # 오차를 0-100 점수로 변환 (오차가 0.1이면 0점)
        score = max(0, 100 - (avg_error * 1000))
        
        return score
    
    def check_symmetry(self, left_angle: float, right_angle: float, tolerance: float = 10) -> Tuple[bool, float]:
        """좌우 대칭성 체크"""
        difference = abs(left_angle - right_angle)
        is_symmetric = difference <= tolerance
        symmetry_score = max(0, 100 - (difference * 10))
        return is_symmetric, symmetry_score
    
    def calculate_spine_angle(self, pose: Dict) -> float:
        """척추 각도 계산 (어깨-엉덩이 연결선)"""
        left_shoulder = pose['left_shoulder']
        right_shoulder = pose['right_shoulder']
        left_hip = pose['left_hip']
        right_hip = pose['right_hip']
        
        # 어깨 중점
        shoulder_mid = {
            'x': (left_shoulder['x'] + right_shoulder['x']) / 2,
            'y': (left_shoulder['y'] + right_shoulder['y']) / 2,
            'z': (left_shoulder.get('z', 0) + right_shoulder.get('z', 0)) / 2
        }
        
        # 엉덩이 중점
        hip_mid = {
            'x': (left_hip['x'] + right_hip['x']) / 2,
            'y': (left_hip['y'] + right_hip['y']) / 2,
            'z': (left_hip.get('z', 0) + right_hip.get('z', 0)) / 2
        }
        
        # 수직선과의 각도
        dx = shoulder_mid['x'] - hip_mid['x']
        dy = shoulder_mid['y'] - hip_mid['y']
        
        angle = math.degrees(math.atan2(dx, dy))
        return abs(angle)
    
    def detect_valgus(self, pose: Dict) -> Tuple[bool, float]:
        """무릎 모임(Knee Valgus) 감지"""
        left_hip = pose['left_hip']
        left_knee = pose['left_knee']
        left_ankle = pose['left_ankle']
        
        right_hip = pose['right_hip']
        right_knee = pose['right_knee']
        right_ankle = pose['right_ankle']
        
        # 정면에서 봤을 때 무릎이 발목보다 안쪽에 있는지 확인
        left_valgus = left_knee['x'] > left_ankle['x'] + 0.02  # 2cm 허용
        right_valgus = right_knee['x'] < right_ankle['x'] - 0.02
        
        valgus_detected = left_valgus or right_valgus
        
        # 심각도 계산 (0-100, 0이 정상)
        left_deviation = max(0, (left_knee['x'] - left_ankle['x']) * 100)
        right_deviation = max(0, (right_ankle['x'] - right_knee['x']) * 100)
        severity = max(left_deviation, right_deviation)
        
        return valgus_detected, severity
    
    def calculate_bar_path_efficiency(self, bar_positions: List[Dict]) -> float:
        """바벨 경로 효율성 계산 (수직 이동 대비 실제 이동 거리)"""
        if len(bar_positions) < 2:
            return 100
        
        # 수직 이동 거리
        vertical_distance = abs(bar_positions[-1]['y'] - bar_positions[0]['y'])
        
        # 실제 이동 거리
        total_distance = 0
        for i in range(1, len(bar_positions)):
            total_distance += self.calculate_distance_3d(
                bar_positions[i], bar_positions[i-1]
            )
        
        if total_distance == 0:
            return 100
        
        efficiency = (vertical_distance / total_distance) * 100
        return min(100, efficiency)
    
    def detect_butt_wink(self, spine_angle: float, hip_angle: float, phase: str) -> bool:
        """벗 윙크(Butt Wink) 감지"""
        if phase != "bottom":
            return False
        
        # 하강 최저점에서 척추가 굽어지는지 확인
        # 척추각이 15도 이상 변하거나 엉덩이 각도가 급격히 변하면 벗 윙크
        return spine_angle > 15 or hip_angle < 70
    
    def calculate_calories_burned(self, exercise_type: str, duration: float, 
                                 reps: int, intensity_score: float, 
                                 user_weight: float = 70) -> float:
        """정확한 칼로리 소모량 계산"""
        
        # 운동별 MET (Metabolic Equivalent of Task) 값
        met_values = {
            'squat': {'low': 3.5, 'medium': 5.0, 'high': 8.0},
            'deadlift': {'low': 3.0, 'medium': 6.0, 'high': 9.5},
            'overhead_press': {'low': 3.0, 'medium': 4.5, 'high': 6.0},
            'bench_press': {'low': 3.0, 'medium': 5.5, 'high': 8.0},
            'plank': {'low': 3.0, 'medium': 4.0, 'high': 5.0},
            'pushup': {'low': 3.5, 'medium': 5.0, 'high': 8.0},
            'lunge': {'low': 3.5, 'medium': 5.5, 'high': 7.0},
            'burpee': {'low': 6.0, 'medium': 10.0, 'high': 12.5},
        }
        
        # 강도 분류 (점수 기반)
        if intensity_score >= 85:
            intensity = 'high'
        elif intensity_score >= 70:
            intensity = 'medium'
        else:
            intensity = 'low'
        
        # 기본 MET 값
        base_met = met_values.get(exercise_type, {}).get(intensity, 5.0)
        
        # 반복 횟수에 따른 보정 (더 많은 반복 = 더 높은 강도)
        rep_multiplier = 1 + (reps * 0.02)  # 반복당 2% 증가
        
        # 자세 정확도에 따른 보정 (정확한 자세 = 더 효율적인 근육 사용)
        form_multiplier = 0.8 + (intensity_score / 100) * 0.4  # 80-120% 범위
        
        # 최종 MET 계산
        adjusted_met = base_met * rep_multiplier * form_multiplier
        
        # 칼로리 계산: METs × 체중(kg) × 시간(시간)
        duration_hours = duration / 3600
        calories = adjusted_met * user_weight * duration_hours
        
        # 최소 칼로리 보장 (운동했으면 최소한의 칼로리는 소모)
        min_calories = reps * 0.5  # 반복당 최소 0.5kcal
        
        return max(calories, min_calories)
    
    def generate_voice_feedback(self, result: AnalysisResult) -> str:
        """실시간 음성 피드백 생성"""
        if result.overall_score >= 90:
            return self._generate_positive_feedback(result)
        elif result.overall_score >= 70:
            return self._generate_corrective_feedback(result)
        else:
            return self._generate_warning_feedback(result)
    
    def _generate_positive_feedback(self, result: AnalysisResult) -> str:
        """긍정적 피드백"""
        feedbacks = [
            f"완벽합니다. 현재 점수 {result.overall_score:.0f}점.",
            f"훌륭한 자세입니다. 지속하세요.",
            f"정확한 움직임입니다. 점수 {result.overall_score:.0f}점."
        ]
        return np.random.choice(feedbacks)
    
    def _generate_corrective_feedback(self, result: AnalysisResult) -> str:
        """교정 피드백"""
        if result.corrections:
            return result.feedback[0] if result.feedback else "자세를 조금 더 정확히 해주세요."
        return f"좋습니다. 조금만 더 정확히 하면 완벽합니다."
    
    def _generate_warning_feedback(self, result: AnalysisResult) -> str:
        """경고 피드백"""
        if result.violations:
            return f"주의! {result.violations[0]['message']}"
        return result.feedback[0] if result.feedback else "자세를 다시 확인해주세요."
