import random

# 간단한 건강 상담 지식베이스 (벡터스토어 대신)
HEALTH_KNOWLEDGE = {
    'nutrition': {
        '다이어트': [
            '건강한 다이어트를 위해서는 급격한 체중 감량보다는 꾸준한 생활습관 변화가 중요합니다.',
            '일일 권장 칼로리에서 300-500kcal 정도 줄이는 것이 안전한 감량 속도입니다.',
            '단백질 섭취를 충분히 하여 근육량을 유지하면서 체지방을 줄이세요.'
        ],
        '영양소': [
            '균형잡힌 식단을 위해서는 탄수화물 45-65%, 단백질 10-35%, 지방 20-35%의 비율로 섭취하세요.',
            '비타민과 미네랄이 풍부한 다양한 색깔의 채소와 과일을 드세요.',
            '하루 8잔 이상의 물을 마셔 충분한 수분을 섭취하세요.'
        ],
        '식사': [
            '규칙적인 식사 시간을 지키고, 천천히 꼭꼭 씹어서 드세요.',
            '과식을 피하고 적당량을 여러 번 나누어 드시는 것이 좋습니다.',
            '가공식품보다는 자연식품을 선택하세요.'
        ]
    },
    'exercise': {
        '운동': [
            '운동을 시작할 때는 무리하지 말고 점진적으로 강도를 높여나가세요.',
            '주 3-5회, 30분 이상의 유산소 운동과 주 2-3회의 근력 운동을 병행하세요.',
            '운동 전후 충분한 워밍업과 쿨다운으로 부상을 예방하세요.'
        ],
        '근력': [
            '근력 운동은 큰 근육군부터 작은 근육군 순서로 진행하세요.',
            '같은 부위는 48시간 간격을 두고 운동하여 회복시간을 주세요.',
            '정확한 자세가 무게보다 중요합니다.'
        ],
        '유산소': [
            '심박수를 목표 범위(최대심박수의 50-85%)에 맞춰 운동하세요.',
            '처음에는 저강도로 시작하여 점차 강도를 높이세요.',
            '다양한 유산소 운동을 번갈아가며 하여 지루함을 피하세요.'
        ]
    },
    'health': {
        '수면': [
            '성인은 하루 7-9시간의 충분한 수면이 필요합니다.',
            '규칙적인 수면 패턴을 유지하고, 잠들기 2시간 전에는 식사를 피하세요.',
            '침실은 어둡고 시원하게 유지하세요.'
        ],
        '스트레스': [
            '규칙적인 운동과 명상, 호흡법으로 스트레스를 관리하세요.',
            '취미 활동이나 사회적 관계를 통해 스트레스를 해소하세요.',
            '과도한 스트레스가 지속되면 전문가의 도움을 받으세요.'
        ],
        '일반': [
            '정기적인 건강검진을 통해 건강상태를 체크하세요.',
            '금연과 금주, 적절한 운동으로 건강한 생활습관을 유지하세요.',
            '증상이 지속되면 반드시 의료진과 상담하세요.'
        ]
    }
}

def find_best_answer(question, category='general'):
    """질문에 가장 적합한 답변 찾기 (간단한 키워드 매칭)"""
    
    question_lower = question.lower()
    
    # 카테고리별 키워드 매칭
    if category == 'nutrition' or any(word in question_lower for word in ['식사', '영양', '다이어트', '음식', '칼로리']):
        if any(word in question_lower for word in ['다이어트', '살', '체중', '감량']):
            responses = HEALTH_KNOWLEDGE['nutrition']['다이어트']
        elif any(word in question_lower for word in ['영양소', '비타민', '단백질', '탄수화물']):
            responses = HEALTH_KNOWLEDGE['nutrition']['영양소']
        else:
            responses = HEALTH_KNOWLEDGE['nutrition']['식사']
    
    elif category == 'exercise' or any(word in question_lower for word in ['운동', '근력', '유산소', '헬스', '피트니스']):
        if any(word in question_lower for word in ['근력', '웨이트', '근육']):
            responses = HEALTH_KNOWLEDGE['exercise']['근력']
        elif any(word in question_lower for word in ['유산소', '달리기', '조깅', '심폐']):
            responses = HEALTH_KNOWLEDGE['exercise']['유산소']
        else:
            responses = HEALTH_KNOWLEDGE['exercise']['운동']
    
    elif any(word in question_lower for word in ['수면', '잠', '불면']):
        responses = HEALTH_KNOWLEDGE['health']['수면']
    elif any(word in question_lower for word in ['스트레스', '우울', '불안']):
        responses = HEALTH_KNOWLEDGE['health']['스트레스']
    else:
        responses = HEALTH_KNOWLEDGE['health']['일반']
    
    return random.choice(responses)

def get_health_consultation(question, category='general', user_profile=None):
    """건강 상담 응답 생성"""
    
    # 기본 응답 찾기
    ai_response = find_best_answer(question, category)
    
    # 사용자 프로필 기반 개인화
    if user_profile:
        if user_profile.get('fitness_level') == 'beginner':
            ai_response += '\n\n💡 초보자이시라면 천천히 시작하여 꾸준히 하는 것이 가장 중요합니다.'
        elif user_profile.get('fitness_level') == 'advanced':
            ai_response += '\n\n💪 이미 경험이 있으시니 더 세부적인 목표를 설정하여 도전해보세요.'
        
        # 질병이나 알레르기 고려
        if user_profile.get('diseases') and '당뇨병' in user_profile.get('diseases', []):
            ai_response += '\n\n⚠️ 당뇨병이 있으시니 혈당 관리에 특히 주의하세요.'
        
        if user_profile.get('allergies') and '음식 알레르기' in user_profile.get('allergies', []):
            ai_response += '\n\n⚠️ 알레르기가 있으시니 해당 식품은 피해주세요.'
    
    return {
        'question': question,
        'ai_response': ai_response,
        'category': category,
        'confidence': random.uniform(0.8, 0.95),
        'follow_up_questions': [
            '더 구체적인 운동 계획을 원하시나요?',
            '영양 섭취에 대해 더 자세히 알고 싶으신가요?',
            '다른 궁금한 점이 있으신가요?'
        ]
    }
