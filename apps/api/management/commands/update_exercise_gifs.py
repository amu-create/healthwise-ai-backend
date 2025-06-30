from django.core.management.base import BaseCommand
from apps.api.models import Exercise

class Command(BaseCommand):
    help = "운동 이름에 해당하는 gif_url을 업데이트합니다."

    def handle(self, *args, **kwargs):
        gif_update_data = {
            # 가슴 운동
            "벤치프레스": "https://media1.tenor.com/m/nxJqRDCmt0MAAAAd/supino-reto.gif",
            "인클라인 벤치프레스": "https://media1.tenor.com/m/e45GckrMBLEAAAAd/flex%C3%A3o-inclinada-no-banco.gif",
            "덤벨 플라이": "https://media1.tenor.com/m/oJXOnsC72qMAAAAd/crussifixo-no-banco-com-halteres.gif",
            "체스트 프레스 머신": "https://media1.tenor.com/m/3bJRUkfLN3EAAAAd/supino-na-maquina.gif",
            "푸시업": "https://media1.tenor.com/m/e45GckrMBLEAAAAd/flex%C3%A3o-inclinada-no-banco.gif",
            
            # 등 운동
            "풀업": "https://media1.tenor.com/m/bOA5VPeUz5QAAAAd/noequipmentexercisesmen-pullups.gif",
            "랫풀다운": "https://media1.tenor.com/m/PVR9ra9tAwcAAAAd/pulley-pegada-aberta.gif",
            "바벨로우": "https://media1.tenor.com/m/AYJ_bNXDvoUAAAAd/workout-muscles.gif",
            "시티드 로우": "https://media1.tenor.com/m/vy_b35185M0AAAAd/remada-baixa-triangulo.gif",
            "데드리프트": "https://media1.tenor.com/m/AYJ_bNXDvoUAAAAd/workout-muscles.gif",
            
            # 하체 운동
            "스쿼트": "https://media1.tenor.com/m/pdMmsiutWkcAAAAd/gym.gif",
            "레그프레스": "https://media1.tenor.com/m/yBaS_oBgidsAAAAd/gym.gif",
            "런지": "https://media1.tenor.com/m/K8EFQDHYz3UAAAAd/gym.gif",
            "레그컬": "https://media1.tenor.com/m/fj_cZPprAyMAAAAd/gym.gif",
            "레그 익스텐션": "https://media1.tenor.com/m/bqKtsSuqilQAAAAd/gym.gif",
            
            # 어깨 운동
            "숄더프레스": "https://media1.tenor.com/m/vFJSvh8AvhAAAAAd/a1.gif",
            "사이드 레터럴 레이즈": "https://media1.tenor.com/m/-OavRqpxSaEAAAAd/eleva%C3%A7%C3%A3o-lateral.gif",
            "프론트 레이즈": "https://media1.tenor.com/m/-OavRqpxSaEAAAAd/eleva%C3%A7%C3%A3o-lateral.gif",
            "업라이트 로우": "https://media1.tenor.com/m/AYJ_bNXDvoUAAAAd/workout-muscles.gif",
            "리어 델트 플라이": "https://media1.tenor.com/m/-OavRqpxSaEAAAAd/eleva%C3%A7%C3%A3o-lateral.gif",
            
            # 팔 운동
            "바벨컬": "https://media1.tenor.com/m/m2Dfyh507FQAAAAd/8preacher-curl.gif",
            "해머컬": "https://media1.tenor.com/m/8T_oLOn1XJwAAAAd/rosca-alternada-com-halteres.gif",
            "트라이셉스 익스텐션": "https://media1.tenor.com/m/V3J-mg9gH0kAAAAd/seated-dumbbell-triceps-extension.gif",
            "케이블 푸시다운": "https://media1.tenor.com/m/mbebKudZjxYAAAAd/tr%C3%ADceps-pulley.gif",
            "프리처컬": "https://media1.tenor.com/m/m2Dfyh507FQAAAAd/8preacher-curl.gif",
            
            # 복근 운동
            "크런치": "https://media1.tenor.com/m/e45GckrMBLEAAAAd/flex%C3%A3o-inclinada-no-banco.gif",
            "플랭크": "https://media1.tenor.com/m/e45GckrMBLEAAAAd/flex%C3%A3o-inclinada-no-banco.gif",
            "레그레이즈": "https://media1.tenor.com/m/e45GckrMBLEAAAAd/flex%C3%A3o-inclinada-no-banco.gif",
            "러시안 트위스트": "https://media1.tenor.com/m/e45GckrMBLEAAAAd/flex%C3%A3o-inclinada-no-banco.gif",
            "바이시클 크런치": "https://media1.tenor.com/m/e45GckrMBLEAAAAd/flex%C3%A3o-inclinada-no-banco.gif",
            
            # 유산소 운동
            "러닝머신": "https://media1.tenor.com/m/pdMmsiutWkcAAAAd/gym.gif",
            "사이클": "https://media1.tenor.com/m/pdMmsiutWkcAAAAd/gym.gif",
            "로잉머신": "https://media1.tenor.com/m/pdMmsiutWkcAAAAd/gym.gif",
            "버피": "https://media1.tenor.com/m/e45GckrMBLEAAAAd/flex%C3%A3o-inclinada-no-banco.gif",
            "점핑잭": "https://media1.tenor.com/m/e45GckrMBLEAAAAd/flex%C3%A3o-inclinada-no-banco.gif",
            
            # 추가 운동들
            "덤벨 고블릿 스쿼트": "https://media1.tenor.com/m/yvyaUSnqMXQAAAAd/agachamento-goblet-com-haltere.gif",
            "컨센트레이션컬": "https://media1.tenor.com/m/jaX3EUxaQGkAAAAd/rosca-concentrada-no-banco.gif",
            "머신 이두컬": "https://media1.tenor.com/m/DJ-GuvjNCwgAAAAd/bicep-curl.gif",
            "덤벨 컬": "https://media1.tenor.com/m/pXKe1wAZOlQAAAAd/b%C3%ADceps.gif",
            "밀리터리 프레스": "https://media1.tenor.com/m/CV1FfGVNpdcAAAAd/desenvolvimento-militar.gif",
            "라잉 트라이셉스": "https://media1.tenor.com/m/ToAHkKHVQP4AAAAd/on-lying-triceps-al%C4%B1n-press.gif",
            "케이블 로프 오버헤드 익스텐션": "https://media1.tenor.com/m/Vq6LrVGUAKIAAAAd/tr%C3%ADceps-fraces-na-polia.gif",
            "머신 로우": "https://media1.tenor.com/m/ft6FHrqty-8AAAAd/remada-pronada-maquina.gif",
            "케이블 로우": "https://media1.tenor.com/m/vy_b35185M0AAAAd/remada-baixa-triangulo.gif",
            "케이블 스트레이트바 트라이셉스 푸시다운": "https://media1.tenor.com/m/sxDebEfnoGcAAAAd/triceps-na-polia-alta.gif",
            "바벨스쿼트": "https://media1.tenor.com/m/pdMmsiutWkcAAAAd/gym.gif",
            "핵스쿼트": "https://media1.tenor.com/m/jiqHF0MkHeYAAAAd/gym.gif",
            "덤벨런지": "https://media1.tenor.com/m/sZ7VwZ6jrbcAAAAd/gym.gif",
            "랙풀": "https://media1.tenor.com/m/U-KW3hhwhxcAAAAd/gym.gif",
            "숄더프레스 머신": "https://media1.tenor.com/m/vFJSvh8AvhAAAAAd/a1.gif",
            "체스트프레스 머신": "https://media1.tenor.com/m/3bJRUkfLN3EAAAAd/supino-na-maquina.gif",
            "덤벨플라이": "https://media1.tenor.com/m/oJXOnsC72qMAAAAd/crussifixo-no-banco-com-halteres.gif",
            "인클라인 푸시업": "https://media1.tenor.com/m/e45GckrMBLEAAAAd/flex%C3%A3o-inclinada-no-banco.gif",
            "케이블 로프 트라이셉스푸시다운": "https://media1.tenor.com/m/mbebKudZjxYAAAAd/tr%C3%ADceps-pulley.gif",
            "사이드레터럴레이즈": "https://media1.tenor.com/m/-OavRqpxSaEAAAAd/eleva%C3%A7%C3%A3o-lateral.gif",
            "삼두(맨몸)": "https://media1.tenor.com/m/iGyfarCUXe8AAAAd/tr%C3%ADceps-mergulho.gif",
            "덤벨 체스트 프레스": "https://media1.tenor.com/m/nxJqRDCmt0MAAAAd/supino-reto.gif",
            "덤벨 트라이셉스 익스텐션": "https://media1.tenor.com/m/V3J-mg9gH0kAAAAd/seated-dumbbell-triceps-extension.gif",
            "레그익스텐션": "https://media1.tenor.com/m/bqKtsSuqilQAAAAd/gym.gif",
        }

        updated_count = 0
        not_found_count = 0
        
        for exercise_name, gif_url in gif_update_data.items():
            try:
                exercise = Exercise.objects.get(name=exercise_name)
                exercise.gif_url = gif_url
                exercise.save()
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f'Updated: {exercise_name}'))
            except Exercise.DoesNotExist:
                not_found_count += 1
                self.stdout.write(self.style.WARNING(f'Not found: {exercise_name}'))

        self.stdout.write(self.style.SUCCESS(f'\nTotal {updated_count} exercises updated.'))
        if not_found_count > 0:
            self.stdout.write(self.style.WARNING(f'{not_found_count} exercises not found.'))
