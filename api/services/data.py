# 건강 선택지 데이터
HEALTH_OPTIONS = {
    'diseases': [
        '당뇨병', '고혈압', '심장병', '관절염', '골다공증', '천식', '갑상선 질환',
        '신장 질환', '간 질환', '뇌졸중', '암', '우울증', '불안장애', '없음'
    ],
    'health_conditions': [
        '임신', '수유', '수술 후 회복', '만성 통증', '불면증', '스트레스', 
        '소화불량', '변비', '두통', '요통', '목 통증', '어깨 통증', '무릎 통증', '없음'
    ],
    'allergies': [
        '음식 알레르기', '견과류 알레르기', '유제품 알레르기', '글루텐 알레르기',
        '해산물 알레르기', '계란 알레르기', '약물 알레르기', '꽃가루 알레르기',
        '동물 알레르기', '먼지 알레르기', '화학물질 알레르기', '없음'
    ]
}

# 운동 데이터
EXERCISE_DATA = [
    {
        'id': 1,
        'name': '푸시업',
        'category': 'strength',
        'description': '가슴, 어깨, 팔 근육을 강화하는 기본적인 운동',
        'duration': 15,
        'difficulty': 'medium',
        'calories_per_minute': 8.5,
        'equipment_needed': [],
        'muscle_groups': ['chest', 'shoulders', 'triceps'],
        'youtube_url': 'https://youtube.com/watch?v=example1',
        'thumbnail_url': 'https://img.youtube.com/vi/example1/maxresdefault.jpg'
    },
    {
        'id': 2,
        'name': '스쿼트',
        'category': 'strength',
        'description': '하체 근육을 강화하는 핵심 운동',
        'duration': 20,
        'difficulty': 'easy',
        'calories_per_minute': 6.5,
        'equipment_needed': [],
        'muscle_groups': ['quadriceps', 'glutes', 'hamstrings'],
        'youtube_url': 'https://youtube.com/watch?v=example2',
        'thumbnail_url': 'https://img.youtube.com/vi/example2/maxresdefault.jpg'
    },
    {
        'id': 3,
        'name': '조깅',
        'category': 'cardio',
        'description': '심폐지구력 향상을 위한 유산소 운동',
        'duration': 30,
        'difficulty': 'medium',
        'calories_per_minute': 10.0,
        'equipment_needed': ['running_shoes'],
        'muscle_groups': ['legs', 'core'],
        'youtube_url': 'https://youtube.com/watch?v=example3',
        'thumbnail_url': 'https://img.youtube.com/vi/example3/maxresdefault.jpg'
    }
]

# 루틴 데이터
ROUTINE_DATA = [
    {
        'id': 1,
        'name': '초보자 전신 운동',
        'description': '운동을 처음 시작하는 분들을 위한 기본 루틴',
        'total_duration': 45,
        'difficulty': 'easy',
        'exercises': [
            {'name': '워밍업', 'duration': 5},
            {'name': '스쿼트', 'sets': 3, 'reps': 15},
            {'name': '푸시업', 'sets': 3, 'reps': 10},
            {'name': '플랭크', 'duration': 30},
            {'name': '쿨다운', 'duration': 5}
        ]
    },
    {
        'id': 2,
        'name': 'HIIT 카디오',
        'description': '고강도 인터벌 트레이닝으로 체지방 감량',
        'total_duration': 30,
        'difficulty': 'hard',
        'exercises': [
            {'name': '워밍업', 'duration': 5},
            {'name': '버피', 'sets': 4, 'duration': 45},
            {'name': '마운틴 클라이머', 'sets': 4, 'duration': 45},
            {'name': '점핑잭', 'sets': 4, 'duration': 45},
            {'name': '쿨다운', 'duration': 5}
        ]
    }
]
