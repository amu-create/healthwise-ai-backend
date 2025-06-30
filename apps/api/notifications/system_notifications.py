from datetime import timedelta
from django.utils import timezone
from apps.api.notification_service_v2 import NotificationService
from apps.api.models import UserProfile
import logging

logger = logging.getLogger(__name__)


class SystemNotificationService:
    """시스템 관련 알림 서비스"""
    
    @staticmethod
    def send_profile_completion_reminder(user, completion_percentage):
        """프로필 완성도 리마인더"""
        if completion_percentage < 80:
            missing_fields = []
            profile = getattr(user, 'profile', None)
            
            if profile:
                if not profile.birth_date:
                    missing_fields.append('birth_date')
                if not profile.height:
                    missing_fields.append('height')
                if not profile.weight:
                    missing_fields.append('weight')
                if not profile.fitness_goals:
                    missing_fields.append('fitness_goals')
            
            missing_text = {
                'birth_date': ('생년월일', 'Birth Date', 'Fecha de Nacimiento'),
                'height': ('키', 'Height', 'Altura'),
                'weight': ('체중', 'Weight', 'Peso'),
                'fitness_goals': ('운동 목표', 'Fitness Goals', 'Objetivos de Fitness'),
            }
            
            NotificationService.create_notification(
                user=user,
                notification_type='system',
                title_ko='프로필을 완성해주세요',
                title_en='Complete Your Profile',
                title_es='Completa tu Perfil',
                message_ko=f'프로필이 {completion_percentage}% 완성되었어요. 더 나은 맞춤 서비스를 위해 완성해주세요!',
                message_en=f'Your profile is {completion_percentage}% complete. Complete it for better personalized service!',
                message_es=f'Tu perfil está {completion_percentage}% completo. ¡Complétalo para un mejor servicio personalizado!',
                metadata={
                    'icon': 'account_circle',
                    'completion_percentage': completion_percentage,
                    'missing_fields': missing_fields
                },
                action_url='/profile/edit'
            )
    
    @staticmethod
    def send_new_feature_announcement(user, feature_data):
        """새로운 기능 소개 알림"""
        feature_name = feature_data.get('name', {})
        feature_description = feature_data.get('description', {})
        
        NotificationService.create_notification(
            user=user,
            notification_type='system',
            title_ko='새로운 기능 출시! 🎉',
            title_en='New Feature Released! 🎉',
            title_es='¡Nueva Función Lanzada! 🎉',
            message_ko=f'{feature_name.get("ko", "새로운 기능")}이 추가되었습니다. {feature_description.get("ko", "")}',
            message_en=f'{feature_name.get("en", "New feature")} is now available. {feature_description.get("en", "")}',
            message_es=f'{feature_name.get("es", "Nueva función")} ya está disponible. {feature_description.get("es", "")}',
            metadata={
                'icon': 'new_releases',
                'feature_id': feature_data.get('id'),
                'feature_type': feature_data.get('type'),
                'release_date': feature_data.get('release_date')
            },
            action_url=feature_data.get('action_url', '/whats-new')
        )
    
    @staticmethod
    def send_maintenance_notice(user, maintenance_data):
        """시스템 점검 안내"""
        start_time = maintenance_data.get('start_time')
        end_time = maintenance_data.get('end_time')
        
        # 시간 포맷팅
        start_str = start_time.strftime('%m월 %d일 %H:%M')
        end_str = end_time.strftime('%H:%M')
        
        NotificationService.create_notification(
            user=user,
            notification_type='system',
            title_ko='시스템 점검 예정',
            title_en='System Maintenance Scheduled',
            title_es='Mantenimiento del Sistema Programado',
            message_ko=f'{start_str}부터 {end_str}까지 시스템 점검이 예정되어 있습니다.',
            message_en=f'System maintenance is scheduled from {start_time.strftime("%b %d at %I:%M %p")} to {end_time.strftime("%I:%M %p")}.',
            message_es=f'El mantenimiento del sistema está programado desde {start_time.strftime("%d de %b a las %H:%M")} hasta las {end_time.strftime("%H:%M")}.',
            metadata={
                'icon': 'engineering',
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'maintenance_type': maintenance_data.get('type', 'regular')
            },
            action_url='/system/maintenance'
        )
    
    @staticmethod
    def send_security_alert(user, security_event):
        """보안 알림 (비정상 로그인 시도 등)"""
        event_type = security_event.get('type')
        
        if event_type == 'unusual_login':
            location = security_event.get('location', 'Unknown')
            device = security_event.get('device', 'Unknown Device')
            
            NotificationService.create_notification(
                user=user,
                notification_type='security',
                title_ko='비정상 로그인 감지',
                title_en='Unusual Login Detected',
                title_es='Inicio de Sesión Inusual Detectado',
                message_ko=f'{location}에서 {device}를 통한 로그인이 감지되었습니다. 본인이 아니라면 비밀번호를 변경하세요.',
                message_en=f'Login detected from {location} on {device}. If this wasn\'t you, please change your password.',
                message_es=f'Inicio de sesión detectado desde {location} en {device}. Si no fuiste tú, cambia tu contraseña.',
                metadata={
                    'icon': 'security',
                    'event_type': event_type,
                    'location': location,
                    'device': device,
                    'ip_address': security_event.get('ip_address'),
                    'timestamp': security_event.get('timestamp')
                },
                action_url='/security/settings'
            )
            
            # 긴급 실시간 알림
            NotificationService.send_realtime_notification(user, {
                'type': 'security_alert',
                'severity': 'high',
                'event': security_event
            })
    
    @staticmethod
    def send_subscription_reminder(user, subscription_data):
        """구독 관련 알림"""
        days_remaining = subscription_data.get('days_remaining')
        plan_name = subscription_data.get('plan_name', 'Premium')
        
        if days_remaining <= 7:
            NotificationService.create_notification(
                user=user,
                notification_type='system',
                title_ko='구독 만료 임박',
                title_en='Subscription Expiring Soon',
                title_es='Suscripción por Expirar',
                message_ko=f'{plan_name} 구독이 {days_remaining}일 후 만료됩니다. 갱신하시겠습니까?',
                message_en=f'Your {plan_name} subscription expires in {days_remaining} days. Would you like to renew?',
                message_es=f'Tu suscripción {plan_name} expira en {days_remaining} días. ¿Te gustaría renovar?',
                metadata={
                    'icon': 'subscription',
                    'days_remaining': days_remaining,
                    'plan_name': plan_name,
                    'expiry_date': subscription_data.get('expiry_date')
                },
                action_url='/subscription/renew'
            )
    
    @staticmethod
    def send_data_export_ready(user, export_data):
        """데이터 내보내기 완료 알림"""
        export_type = export_data.get('type', 'full')
        download_url = export_data.get('download_url')
        
        export_types = {
            'full': ('전체 데이터', 'Full Data', 'Datos Completos'),
            'workouts': ('운동 기록', 'Workout History', 'Historial de Ejercicios'),
            'nutrition': ('영양 기록', 'Nutrition History', 'Historial Nutricional'),
            'health': ('건강 데이터', 'Health Data', 'Datos de Salud'),
        }
        
        type_ko, type_en, type_es = export_types.get(
            export_type,
            ('데이터', 'Data', 'Datos')
        )
        
        NotificationService.create_notification(
            user=user,
            notification_type='system',
            title_ko='데이터 내보내기 완료',
            title_en='Data Export Complete',
            title_es='Exportación de Datos Completa',
            message_ko=f'{type_ko} 내보내기가 완료되었습니다. 다운로드하세요.',
            message_en=f'Your {type_en} export is complete. Download now.',
            message_es=f'Tu exportación de {type_es} está completa. Descarga ahora.',
            metadata={
                'icon': 'download',
                'export_type': export_type,
                'file_size': export_data.get('file_size'),
                'expiry_time': export_data.get('expiry_time')
            },
            action_url=download_url
        )
    
    @staticmethod
    def send_achievement_badge_upgrade(user, badge_data):
        """업적 배지 업그레이드 알림"""
        badge_name = badge_data.get('name')
        old_level = badge_data.get('old_level', 'bronze')
        new_level = badge_data.get('new_level', 'silver')
        
        levels = {
            'bronze': ('브론즈', 'Bronze', 'Bronce'),
            'silver': ('실버', 'Silver', 'Plata'),
            'gold': ('골드', 'Gold', 'Oro'),
            'platinum': ('플래티넘', 'Platinum', 'Platino'),
        }
        
        old_ko, old_en, old_es = levels.get(old_level, ('', '', ''))
        new_ko, new_en, new_es = levels.get(new_level, ('', '', ''))
        
        NotificationService.create_notification(
            user=user,
            notification_type='achievement',
            title_ko='배지 업그레이드!',
            title_en='Badge Upgraded!',
            title_es='¡Insignia Mejorada!',
            message_ko=f'{badge_name} 배지가 {old_ko}에서 {new_ko}로 업그레이드되었습니다!',
            message_en=f'Your {badge_name} badge upgraded from {old_en} to {new_en}!',
            message_es=f'¡Tu insignia {badge_name} mejoró de {old_es} a {new_es}!',
            metadata={
                'icon': 'badge',
                'badge_name': badge_name,
                'old_level': old_level,
                'new_level': new_level,
                'badge_id': badge_data.get('id')
            },
            action_url='/achievements/badges'
        )
    
    @staticmethod
    def send_privacy_policy_update(user):
        """개인정보 처리방침 업데이트 알림"""
        NotificationService.create_notification(
            user=user,
            notification_type='system',
            title_ko='개인정보 처리방침 업데이트',
            title_en='Privacy Policy Update',
            title_es='Actualización de Política de Privacidad',
            message_ko='개인정보 처리방침이 업데이트되었습니다. 변경사항을 확인해주세요.',
            message_en='Our Privacy Policy has been updated. Please review the changes.',
            message_es='Nuestra Política de Privacidad ha sido actualizada. Por favor revisa los cambios.',
            metadata={
                'icon': 'privacy',
                'update_date': timezone.now().isoformat(),
                'requires_acceptance': True
            },
            action_url='/privacy-policy'
        )
