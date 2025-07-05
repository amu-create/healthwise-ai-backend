# 운동 관련 상수 및 데이터 정의

# GIF가 있는 운동만 포함
VALID_EXERCISES_WITH_GIF = {
    "숄더프레스 머신": {"muscle_group": "어깨", "gif_url": "https://media1.tenor.com/m/vFJSvh8AvhAAAAAd/a1.gif"},
    "랙풀": {"muscle_group": "등", "gif_url": "https://media1.tenor.com/m/U-KW3hhwhxcAAAAd/gym.gif"},
    "런지": {"muscle_group": "하체", "gif_url": "https://media1.tenor.com/m/K8EFQDHYz3UAAAAd/gym.gif"},
    "덤벨런지": {"muscle_group": "하체", "gif_url": "https://media1.tenor.com/m/sZ7VwZ6jrbcAAAAd/gym.gif"},
    "핵스쿼트": {"muscle_group": "하체", "gif_url": "https://media1.tenor.com/m/jiqHF0MkHeYAAAAd/gym.gif"},
    "바벨스쿼트": {"muscle_group": "하체", "gif_url": "https://media1.tenor.com/m/pdMmsiutWkcAAAAd/gym.gif"},
    "레그익스텐션": {"muscle_group": "하체", "gif_url": "https://media1.tenor.com/m/bqKtsSuqilQAAAAd/gym.gif"},
    "레그컬": {"muscle_group": "하체", "gif_url": "https://media1.tenor.com/m/fj_cZPprAyMAAAAd/gym.gif"},
    "레그프레스": {"muscle_group": "하체", "gif_url": "https://media1.tenor.com/m/yBaS_oBgidsAAAAd/gym.gif"},
    "체스트프레스 머신": {"muscle_group": "가슴", "gif_url": "https://media1.tenor.com/m/3bJRUkfLN3EAAAAd/supino-na-maquina.gif"},
    "케이블 로프 트라이셉스푸시다운": {"muscle_group": "팔", "gif_url": "https://media1.tenor.com/m/mbebKudZjxYAAAAd/tr%C3%ADceps-pulley.gif"},
    "덤벨플라이": {"muscle_group": "가슴", "gif_url": "https://media1.tenor.com/m/oJXOnsC72qMAAAAd/crussifixo-no-banco-com-halteres.gif"},
    "인클라인 푸시업": {"muscle_group": "가슴", "gif_url": "https://media1.tenor.com/m/e45GckrMBLEAAAAd/flex%C3%A3o-inclinada-no-banco.gif"},
    "케이블 로프 오버헤드 익스텐션": {"muscle_group": "팔", "gif_url": "https://media1.tenor.com/m/Vq6LrVGUAKIAAAAd/tr%C3%ADceps-fraces-na-polia.gif"},
    "밀리터리 프레스": {"muscle_group": "어깨", "gif_url": "https://media1.tenor.com/m/CV1FfGVNpdcAAAAd/desenvolvimento-militar.gif"},
    "사이드레터럴레이즈": {"muscle_group": "어깨", "gif_url": "https://media1.tenor.com/m/-OavRqpxSaEAAAAd/eleva%C3%A7%C3%A3o-lateral.gif"},
    "삼두(맨몸)": {"muscle_group": "팔", "gif_url": "https://media1.tenor.com/m/iGyfarCUXe8AAAAd/tr%C3%ADceps-mergulho.gif"},
    "랫풀다운": {"muscle_group": "등", "gif_url": "https://media1.tenor.com/m/PVR9ra9tAwcAAAAd/pulley-pegada-aberta.gif"},
    "케이블 스트레이트바 트라이셉스 푸시다운": {"muscle_group": "팔", "gif_url": "https://media1.tenor.com/m/sxDebEfnoGcAAAAd/triceps-na-polia-alta.gif"},
    "머신 로우": {"muscle_group": "등", "gif_url": "https://media1.tenor.com/m/ft6FHrqty-8AAAAd/remada-pronada-maquina.gif"},
    "케이블 로우": {"muscle_group": "등", "gif_url": "https://media1.tenor.com/m/vy_b35185M0AAAAd/remada-baixa-triangulo.gif"},
    "라잉 트라이셉스": {"muscle_group": "팔", "gif_url": "https://media1.tenor.com/m/ToAHkKHVQP4AAAAd/on-lying-triceps-al%C4%B1n-press.gif"},
    "바벨 프리쳐 컬": {"muscle_group": "팔", "gif_url": "https://media1.tenor.com/m/m2Dfyh507FQAAAAd/8preacher-curl.gif"},
    "바벨로우": {"muscle_group": "등", "gif_url": "https://media1.tenor.com/m/AYJ_bNXDvoUAAAAd/workout-muscles.gif"},
    "풀업": {"muscle_group": "등", "gif_url": "https://media1.tenor.com/m/bOA5VPeUz5QAAAAd/noequipmentexercisesmen-pullups.gif"},
    "덤벨 체스트 프레스": {"muscle_group": "가슴", "gif_url": "https://media1.tenor.com/m/nxJqRDCmt0MAAAAd/supino-reto.gif"},
    "덤벨 컬": {"muscle_group": "팔", "gif_url": "https://media1.tenor.com/m/pXKe1wAZOlQAAAAd/b%C3%ADceps.gif"},
    "덤벨 트라이셉스 익스텐션": {"muscle_group": "팔", "gif_url": "https://media1.tenor.com/m/V3J-mg9gH0kAAAAd/seated-dumbbell-triceps-extension.gif"},
    "덤벨 고블릿 스쿼트": {"muscle_group": "하체", "gif_url": "https://media1.tenor.com/m/yvyaUSnqMXQAAAAd/agachamento-goblet-com-haltere.gif"},
    "컨센트레이션컬": {"muscle_group": "팔", "gif_url": "https://media1.tenor.com/m/jaX3EUxaQGkAAAAd/rosca-concentrada-no-banco.gif"},
    "해머컬": {"muscle_group": "팔", "gif_url": "https://media1.tenor.com/m/8T_oLOn1XJwAAAAd/rosca-alternada-com-halteres.gif"},
    "머신 이두컬": {"muscle_group": "팔", "gif_url": "https://media1.tenor.com/m/DJ-GuvjNCwgAAAAd/bicep-curl.gif"},
}

# 부위별 운동 목록
VALID_EXERCISES_BY_GROUP = {
    "가슴": ["체스트프레스 머신", "덤벨플라이", "인클라인 푸시업", "덤벨 체스트 프레스"],
    "등": ["랙풀", "랫풀다운", "머신 로우", "케이블 로우", "바벨로우", "풀업"],
    "하체": ["런지", "덤벨런지", "핵스쿼트", "바벨스쿼트", "레그익스텐션", "레그컬", "레그프레스", "덤벨 고블릿 스쿼트"],
    "어깨": ["숄더프레스 머신", "밀리터리 프레스", "사이드레터럴레이즈"],
    "팔": ["케이블 로프 트라이셉스푸시다운", "케이블 스트레이트바 트라이셉스 푸시다운", "케이블 로프 오버헤드 익스텐션", 
         "라잉 트라이셉스", "덤벨 트라이셉스 익스텐션", "삼두(맨몸)", "바벨 프리쳐 컬", "덤벨 컬", "해머컬", "컨센트레이션컬", "머신 이두컬"],
}

# 난이도별 추천 운동
EXERCISES_BY_LEVEL = {
    "초급": {
        "가슴": ["체스트프레스 머신", "인클라인 푸시업"],
        "등": ["랫풀다운", "머신 로우", "케이블 로우"],
        "하체": ["레그프레스", "레그익스텐션", "레그컬", "런지"],
        "어깨": ["숄더프레스 머신", "사이드레터럴레이즈"],
        "팔": ["덤벨 컬", "머신 이두컬", "케이블 로프 트라이셉스푸시다운"],
    },
    "중급": {
        "가슴": ["덤벨 체스트 프레스", "덤벨플라이"],
        "등": ["바벨로우", "랙풀", "풀업"],
        "하체": ["바벨스쿼트", "덤벨런지", "핵스쿼트", "덤벨 고블릿 스쿼트"],
        "어깨": ["밀리터리 프레스", "사이드레터럴레이즈"],
        "팔": ["바벨 프리쳐 컬", "해머컬", "라잉 트라이셉스", "삼두(맨몸)"],
    },
    "상급": {
        "가슴": ["덤벨 체스트 프레스", "덤벨플라이", "체스트프레스 머신"],
        "등": ["바벨로우", "풀업", "랙풀"],
        "하체": ["바벨스쿼트", "핵스쿼트", "런지", "덤벨런지"],
        "어깨": ["밀리터리 프레스", "숄더프레스 머신"],
        "팔": ["바벨 프리쳐 컬", "컨센트레이션컬", "케이블 로프 오버헤드 익스텐션"],
    }
}

# 운동 타입 상수
WORKOUT_TYPES = ['Cardio', 'Strength Training', 'Yoga', 'HIIT', 'Swimming', 'Running']

# 강도 배수
INTENSITY_MULTIPLIER = {
    'low': 5,
    'moderate': 8,
    'high': 12
}
