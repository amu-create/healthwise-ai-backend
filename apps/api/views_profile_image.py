from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import os
import uuid
from PIL import Image
import io
import base64

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_profile_image(request):
    """프로필 이미지 업로드"""
    try:
        if 'profile_image' not in request.FILES:
            return Response({
                'error': '이미지 파일이 필요합니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        image_file = request.FILES['profile_image']
        
        # 파일 크기 검증 (5MB)
        if image_file.size > 5 * 1024 * 1024:
            return Response({
                'error': '파일 크기는 5MB 이하여야 합니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 이미지 파일 검증 및 리사이징
        try:
            # 이미지 열기
            image_file.seek(0)  # 파일 포인터를 처음으로
            img = Image.open(image_file)
            
            # 이미지 포맷 확인
            if img.format not in ['JPEG', 'PNG', 'GIF', 'WEBP']:
                return Response({
                    'error': '지원하지 않는 이미지 형식입니다.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # RGBA를 RGB로 변환 (PNG의 경우)
            if img.mode in ('RGBA', 'LA', 'P'):
                # 흰색 배경 생성
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # 이미지 크기 제한 (최대 800x800)
            max_size = (800, 800)
            
            # 원본 비율 유지하면서 리사이징
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # 정사각형으로 크롭 (중앙 기준)
            width, height = img.size
            if width != height:
                # 정사각형 크기 결정
                new_size = min(width, height)
                
                # 크롭 위치 계산
                left = (width - new_size) // 2
                top = (height - new_size) // 2
                right = left + new_size
                bottom = top + new_size
                
                # 크롭
                img = img.crop((left, top, right, bottom))
            
            # 최종 크기로 리사이징 (400x400)
            final_size = (400, 400)
            img = img.resize(final_size, Image.Resampling.LANCZOS)
            
            # 이미지를 바이트로 변환
            img_io = io.BytesIO()
            img.save(img_io, format='JPEG', quality=85, optimize=True)
            img_io.seek(0)
            
            # ContentFile로 변환
            image_content = ContentFile(img_io.read())
            
        except Exception as e:
            return Response({
                'error': f'이미지 처리 중 오류가 발생했습니다: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 파일명 생성
        ext = os.path.splitext(image_file.name)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            return Response({
                'error': '지원하지 않는 파일 형식입니다. (jpg, png, gif, webp만 가능)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 파일명 생성 (항상 .jpg로 저장)
        filename = f"profile_{request.user.id}_{uuid.uuid4().hex}.jpg"
        
        # 기존 프로필 이미지 삭제
        profile = request.user.profile
        if profile.profile_image:
            try:
                profile.profile_image.delete(save=False)
            except:
                pass
        
        # 새 이미지 저장
        profile.profile_image.save(filename, image_content)
        profile.save()
        
        # 이미지 URL 생성
        image_url = request.build_absolute_uri(profile.profile_image.url)
        
        return Response({
            'message': '프로필 이미지가 업로드되었습니다.',
            'image_url': image_url
        })
        
    except Exception as e:
        return Response({
            'error': f'이미지 업로드 중 오류가 발생했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_profile_image(request):
    """프로필 이미지 삭제"""
    try:
        profile = request.user.profile
        
        if not profile.profile_image:
            return Response({
                'error': '삭제할 프로필 이미지가 없습니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 이미지 파일 삭제
        try:
            profile.profile_image.delete(save=False)
        except:
            pass
        
        profile.profile_image = None
        profile.save()
        
        return Response({
            'message': '프로필 이미지가 삭제되었습니다.'
        })
        
    except Exception as e:
        return Response({
            'error': f'이미지 삭제 중 오류가 발생했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile_image(request):
    """프로필 이미지 URL 조회"""
    try:
        profile = request.user.profile
        
        if profile.profile_image:
            image_url = request.build_absolute_uri(profile.profile_image.url)
            return Response({
                'image_url': image_url
            })
        else:
            return Response({
                'image_url': None
            })
            
    except Exception as e:
        return Response({
            'error': f'이미지 조회 중 오류가 발생했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
