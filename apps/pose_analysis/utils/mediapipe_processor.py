import json
import numpy as np
import math
from typing import Dict, List, Tuple, Any, Optional

from ..analyzers import (
    EliteAnalyzer,
    SquatAnalyzer,
    DeadliftAnalyzer,
    OverheadPressAnalyzer,
    BenchPressAnalyzer,
    PlankAnalyzer,
)


class EliteMediaPipeProcessor:
    """엘리트 레벨의 MediaPipe 포즈 분석 프로세서"""
    
    # MediaPipe 랜드마크 인덱스
    POSE_LANDMARKS = {
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
        
        # 운동별 전문 분석기 초기화
        self.analyzers = {
            '스쿼트': SquatAnalyzer(),
            'squat': SquatAnalyzer(),
            '데드리프트': DeadliftAnalyzer(),
            'deadlift': DeadliftAnalyzer(),
            '오버헤드프레스': OverheadPressAnalyzer(),
            'overhead_press': OverheadPressAnalyzer(),
            '벤치프레스': BenchPressAnalyzer(),
            'bench_press': BenchPressAnalyzer(),
            '플랭크': PlankAnalyzer(),
            'plank': PlankAnalyzer(),
        }
        
        # 기본 분석기
        self.default_analyzer = EliteAnalyzer()
        
        # 세션 데이터
        self.session_data = {
            'total_duration': 0,
            'calories_burned': 0,
            'form_scores': [],
            'violations': [],
            'phase_history': [],
            'performance_metrics': []
        }
        
        # 사용자 설정 (기본값)
        self.user_weight = 70  # kg
        self.user_height = 170  # cm
        self.user_fitness_level = 'intermediate'
        
        self.last_timestamp = 0
    
    def set_user_info(self, weight: float = 70, height: float = 170, fitness_level: str = 'intermediate'):
        """사용자 정보 설정"""
        self.user_weight = weight
        self.user_height = height
        self.user_fitness_level = fitness_level
    
    def analyze_pose(self, landmarks: List[Dict], exercise, timestamp: float = 0) -> Dict:
        """포즈 분석 - 전문가 수준"""
        if not landmarks or len(landmarks) < 33:
            return self._empty_result()
        
        # 랜드마크를 딕셔너리로 변환
        pose_dict = self._landmarks_to_dict(landmarks)
        
        # 랜드마크 신뢰도 체크
        if not self._validate_landmarks(pose_dict):
            return self._empty_result()
        
        # 운동별 전문 분석기 선택
        analyzer = self.analyzers.get(exercise.name) or self.analyzers.get(exercise.name_en) or self.default_analyzer
        
        # 분석 실행
        result = analyzer.analyze(pose_dict, timestamp)
        
        # 칼로리 계산 (훨씬 정확한 계산)
        duration = timestamp - self.last_timestamp if self.last_timestamp > 0 else 0
        calories = analyzer.calculate_calories_burned(
            exercise_type=exercise.name_en.lower() if hasattr(exercise, 'name_en') else 'general',
            duration=duration,
            reps=0,  # 반복 횟수는 제외
            intensity_score=result.overall_score,
            user_weight=self.user_weight
        )
        
        # 세션 데이터 업데이트
        self.session_data['total_duration'] += duration
        self.session_data['calories_burned'] += calories
        self.session_data['form_scores'].append(result.overall_score)
        self.session_data['violations'].extend(result.violations)
        self.session_data['phase_history'].append(result.phase)
        if result.performance_metrics:
            self.session_data['performance_metrics'].append(result.performance_metrics)
        
        self.last_timestamp = timestamp
        
        # 음성 피드백 생성
        voice_feedback = analyzer.generate_voice_feedback(result)
        
        # 최종 결과 구성
        return {
            'angles': result.angles,
            'scores': result.scores,
            'overall_score': result.overall_score,
            'feedback': result.feedback,
            'corrections': result.corrections,
            'is_in_position': result.is_in_position,
            'phase': result.phase,
            'violations': result.violations,
            'metrics': {
                **result.metrics,
                'calories_burned': calories,
                'session_calories': self.session_data['calories_burned'],
                'session_duration': self.session_data['total_duration'],
                'average_form_score': np.mean(self.session_data['form_scores']) if self.session_data['form_scores'] else 0
            },
            'performance_metrics': result.performance_metrics,
            'voice_feedback': voice_feedback,
            'expert_analysis': self._generate_expert_summary(result, exercise)
        }
    
    def _landmarks_to_dict(self, landmarks: List[Dict]) -> Dict:
        """랜드마크 리스트를 이름 기반 딕셔너리로 변환"""
        pose_dict = {}
        for i, landmark in enumerate(landmarks):
            for name, idx in self.POSE_LANDMARKS.items():
                if idx == i:
                    pose_dict[name] = landmark
                    break
        return pose_dict
    
    def _validate_landmarks(self, pose_dict: Dict) -> bool:
        """랜드마크 신뢰도 검증"""
        # 핵심 랜드마크 체크
        essential_landmarks = [
            'left_shoulder', 'right_shoulder',
            'left_hip', 'right_hip',
            'left_knee', 'right_knee',
            'left_ankle', 'right_ankle'
        ]
        
        for landmark_name in essential_landmarks:
            if landmark_name not in pose_dict:
                return False
            
            landmark = pose_dict[landmark_name]
            if landmark.get('visibility', 0) < self.min_detection_confidence:
                return False
        
        return True
    
    def _generate_expert_summary(self, result, exercise) -> Dict:
        """전문가 수준의 분석 요약"""
        summary = {
            'form_grade': self._calculate_form_grade(result.overall_score),
            'technique_level': self._assess_technique_level(result),
            'injury_prevention_tips': self._get_injury_prevention_tips(result, exercise),
            'performance_insights': self._get_performance_insights(result),
            'recommendations': self._get_recommendations(result, exercise)
        }
        
        return summary
    
    def _calculate_form_grade(self, score: float) -> str:
        """점수를 등급으로 변환"""
        if score >= 95:
            return "Elite (엘리트)"
        elif score >= 90:
            return "Excellent (우수)"
        elif score >= 80:
            return "Good (양호)"
        elif score >= 70:
            return "Fair (보통)"
        elif score >= 60:
            return "Poor (미흡)"
        else:
            return "Needs Work (개선필요)"
    
    def _assess_technique_level(self, result) -> str:
        """기술 수준 평가"""
        if result.violations:
            severity_scores = {
                'critical': 0,
                'high': 1,
                'medium': 2,
                'low': 3
            }
            
            worst_severity = min([severity_scores.get(v['severity'], 3) for v in result.violations])
            
            if worst_severity == 0:
                return "위험 - 즉시 교정 필요"
            elif worst_severity == 1:
                return "주의 - 부상 위험"
            elif worst_severity == 2:
                return "개선 필요"
            else:
                return "미세 조정 필요"
        
        if result.overall_score >= 90:
            return "전문가 수준"
        elif result.overall_score >= 80:
            return "숙련자 수준"
        else:
            return "초급-중급 수준"
    
    def _get_injury_prevention_tips(self, result, exercise) -> List[str]:
        """부상 예방 팁"""
        tips = []
        
        if result.performance_metrics and result.performance_metrics.get('injury_risk', 0) > 0.5:
            tips.append("⚠️ 현재 자세로는 부상 위험이 높습니다. 무게를 줄이거나 휴식을 취하세요.")
        
        for violation in result.violations:
            if violation['type'] == 'spine_flexion':
                tips.append("🔴 척추 보호: 복압을 높이고 가슴을 펴서 척추를 중립으로 유지하세요.")
            elif violation['type'] == 'knee_valgus':
                tips.append("🔴 무릎 보호: 무릎을 발끝 방향으로 밀어내는 연습을 하세요.")
            elif violation['type'] == 'lumbar_hyperextension':
                tips.append("🔴 허리 보호: 골반을 중립으로 유지하고 복근을 단단히 조이세요.")
        
        return tips
    
    def _get_performance_insights(self, result) -> List[str]:
        """퍼포먼스 인사이트"""
        insights = []
        
        if result.performance_metrics:
            power = result.performance_metrics.get('power_output', 0)
            if power > 0.9:
                insights.append("💪 폭발적인 파워 출력! 현재 강도를 유지하세요.")
            elif power < 0.5:
                insights.append("📈 파워 출력이 낮습니다. 속도를 높여보세요.")
            
            efficiency = result.performance_metrics.get('form_efficiency', 0)
            if efficiency > 0.9:
                insights.append("✨ 매우 효율적인 움직임입니다.")
            elif efficiency < 0.7:
                insights.append("🎯 움직임 효율성을 개선하면 더 좋은 결과를 얻을 수 있습니다.")
        
        return insights
    
    def _get_recommendations(self, result, exercise) -> List[str]:
        """개인화된 추천사항"""
        recommendations = []
        
        # 점수 기반 추천
        if result.overall_score < 70:
            recommendations.append("🎯 기본 자세부터 다시 연습하는 것을 추천합니다.")
            recommendations.append("🎯 거울을 보며 자세를 확인하거나 전문 트레이너의 지도를 받으세요.")
        elif result.overall_score < 85:
            recommendations.append("🎯 주요 교정 포인트에 집중하여 연습하세요.")
            recommendations.append("🎯 가벼운 무게로 완벽한 자세를 만든 후 무게를 증가시키세요.")
        else:
            recommendations.append("🎯 현재 수준을 유지하며 점진적으로 강도를 높이세요.")
            recommendations.append("🎯 세부적인 기술 향상에 집중하세요.")
        
        # 특정 문제에 대한 추천
        if 'knee_valgus' in result.corrections:
            recommendations.append("💡 둔근 강화 운동(힙 쓰러스트, 클램쉘)을 추가하세요.")
        
        if 'spine_flexion' in result.corrections or 'excessive_flexion' in result.corrections:
            recommendations.append("💡 코어 강화와 흉추 가동성 운동을 병행하세요.")
        
        if 'insufficient_depth' in result.corrections:
            recommendations.append("💡 발목과 고관절 가동성 운동을 추가하세요.")
        
        return recommendations
    
    def get_session_report(self) -> Dict:
        """세션 종료 후 상세 리포트"""
        if not self.session_data['form_scores']:
            return {}
        
        avg_score = np.mean(self.session_data['form_scores'])
        
        # 위반 사항 분석
        violation_summary = {}
        for violation in self.session_data['violations']:
            vtype = violation['type']
            if vtype not in violation_summary:
                violation_summary[vtype] = {
                    'count': 0,
                    'severity': violation['severity']
                }
            violation_summary[vtype]['count'] += 1
        
        # 단계별 시간 분석
        phase_summary = {}
        for phase in self.session_data['phase_history']:
            if phase not in phase_summary:
                phase_summary[phase] = 0
            phase_summary[phase] += 1
        
        # 성능 지표 평균
        avg_performance = {}
        if self.session_data['performance_metrics']:
            for metric in self.session_data['performance_metrics'][0].keys():
                values = [p.get(metric, 0) for p in self.session_data['performance_metrics']]
                avg_performance[metric] = np.mean(values)
        
        return {
            'session_summary': {
                'total_duration': self.session_data['total_duration'],
                'total_calories': self.session_data['calories_burned'],
                'average_form_score': avg_score,
                'form_grade': self._calculate_form_grade(avg_score),
                'total_frames_analyzed': len(self.session_data['form_scores'])
            },
            'violation_summary': violation_summary,
            'phase_distribution': phase_summary,
            'performance_metrics': avg_performance,
            'improvement_areas': self._identify_improvement_areas(violation_summary),
            'session_highlights': self._get_session_highlights(),
            'next_session_focus': self._suggest_next_focus(violation_summary, avg_score)
        }
    
    def _identify_improvement_areas(self, violation_summary: Dict) -> List[str]:
        """개선이 필요한 영역 식별"""
        areas = []
        
        priority_violations = sorted(
            violation_summary.items(), 
            key=lambda x: x[1]['count'], 
            reverse=True
        )
        
        for vtype, data in priority_violations[:3]:  # 상위 3개
            if vtype == 'spine_flexion':
                areas.append("척추 중립 유지 - 코어 강화 필요")
            elif vtype == 'knee_valgus':
                areas.append("무릎 정렬 - 둔근 및 중둔근 강화")
            elif vtype == 'insufficient_depth':
                areas.append("가동범위 증가 - 유연성 향상")
            elif vtype == 'lumbar_hyperextension':
                areas.append("골반 컨트롤 - 복부 근력 강화")
            elif vtype == 'bar_drift':
                areas.append("바벨 경로 최적화 - 기술 연습")
        
        return areas
    
    def _get_session_highlights(self) -> List[str]:
        """세션 하이라이트"""
        highlights = []
        
        if self.session_data['form_scores']:
            best_score = max(self.session_data['form_scores'])
            if best_score >= 95:
                highlights.append(f"🏆 최고 점수 {best_score:.0f}점 달성!")
            
            # 점수 향상 추세
            if len(self.session_data['form_scores']) > 10:
                early_avg = np.mean(self.session_data['form_scores'][:5])
                late_avg = np.mean(self.session_data['form_scores'][-5:])
                if late_avg > early_avg + 5:
                    highlights.append(f"📈 세션 중 {late_avg - early_avg:.0f}% 향상!")
        
        # 칼로리 소모
        if self.session_data['calories_burned'] > 50:
            highlights.append(f"🔥 {self.session_data['calories_burned']:.0f}kcal 소모")
        
        return highlights
    
    def _suggest_next_focus(self, violation_summary: Dict, avg_score: float) -> List[str]:
        """다음 세션 집중 포인트"""
        focus_points = []
        
        if avg_score < 70:
            focus_points.append("💡 다음 세션: 가벼운 무게로 기본 자세 마스터하기")
            focus_points.append("💡 거울을 보며 천천히 움직이며 자세 확인")
        elif avg_score < 85:
            focus_points.append("💡 다음 세션: 주요 문제점 1-2개만 집중 개선")
            focus_points.append("💡 템포를 느리게 하여 컨트롤 향상")
        else:
            focus_points.append("💡 다음 세션: 점진적 과부하 적용")
            focus_points.append("💡 속도와 파워 향상에 집중")
        
        # 특정 위반사항 기반 제안
        if violation_summary:
            most_common = max(violation_summary.items(), key=lambda x: x[1]['count'])[0]
            if most_common == 'spine_flexion':
                focus_points.append("💡 운동 전 코어 활성화 드릴 추가")
            elif most_common == 'knee_valgus':
                focus_points.append("💡 밴드를 이용한 무릎 정렬 연습")
        
        return focus_points
    
    def _empty_result(self) -> Dict:
        """빈 결과 반환"""
        return {
            'angles': {},
            'scores': {},
            'overall_score': 0,
            'feedback': ["포즈를 감지할 수 없습니다. 카메라 각도를 조정해주세요."],
            'corrections': [],
            'is_in_position': False,
            'phase': 'not_detected',
            'violations': [],
            'metrics': {
                'calories_burned': 0,
                'session_calories': self.session_data.get('calories_burned', 0),
                'session_duration': self.session_data.get('total_duration', 0),
                'average_form_score': 0
            },
            'performance_metrics': {},
            'voice_feedback': "자세를 감지할 수 없습니다.",
            'expert_analysis': {}
        }
    
    def reset_session(self):
        """세션 데이터 초기화"""
        self.session_data = {
            'total_duration': 0,
            'calories_burned': 0,
            'form_scores': [],
            'violations': [],
            'phase_history': [],
            'performance_metrics': []
        }
        self.last_timestamp = 0
        
        # 각 분석기의 상태도 초기화
        for analyzer in self.analyzers.values():
            if hasattr(analyzer, 'reset'):
                analyzer.reset()


# 기존 MediaPipeProcessor와의 호환성을 위한 별칭
MediaPipeProcessor = EliteMediaPipeProcessor
