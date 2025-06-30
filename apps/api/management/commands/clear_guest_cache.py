from django.core.management.base import BaseCommand
from django.core.cache import cache

class Command(BaseCommand):
    help = '비회원 API 사용량 캐시 초기화'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pattern',
            type=str,
            default='guest_api_limit_*',
            help='삭제할 캐시 키 패턴'
        )

    def handle(self, *args, **options):
        pattern = options['pattern']
        
        # Django 캐시에서 패턴과 일치하는 키 삭제
        if hasattr(cache, '_cache'):
            # 로컬 메모리 캐시인 경우
            keys_to_delete = []
            for key in cache._cache.keys():
                if key.startswith('guest_api_limit_'):
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                cache.delete(key)
                self.stdout.write(f"Deleted: {key}")
            
            self.stdout.write(
                self.style.SUCCESS(f'총 {len(keys_to_delete)}개의 캐시 키를 삭제했습니다.')
            )
        else:
            # Redis 등 외부 캐시인 경우
            self.stdout.write(
                self.style.WARNING('캐시 타입이 지원되지 않습니다. Redis인 경우 별도 처리가 필요합니다.')
            )
