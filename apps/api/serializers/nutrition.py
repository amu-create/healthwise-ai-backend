from rest_framework import serializers
from apps.api.models import FoodAnalysis, DailyNutrition


class FoodAnalysisRequestSerializer(serializers.Serializer):
    """음식 분석 요청 시리얼라이저"""
    food_name = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    image_base64 = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        """최소한 음식 이름이나 이미지 중 하나는 있어야 함"""
        if not attrs.get('food_name') and not attrs.get('image_base64'):
            raise serializers.ValidationError(
                "음식 이름이나 이미지 중 적어도 하나는 입력해주세요."
            )
        return attrs


class FoodAnalysisSerializer(serializers.ModelSerializer):
    """음식 분석 결과 시리얼라이저"""
    class Meta:
        model = FoodAnalysis
        fields = [
            'id', 'food_name', 'description', 'image_url',
            'calories', 'protein', 'carbohydrates', 'fat',
            'fiber', 'sugar', 'sodium',
            'analysis_summary', 'recommendations',
            'analyzed_at'
        ]
        read_only_fields = ['id', 'analyzed_at']


class DailyNutritionSerializer(serializers.ModelSerializer):
    """일일 영양 기록 시리얼라이저"""
    food_analyses = FoodAnalysisSerializer(many=True, read_only=True)
    
    class Meta:
        model = DailyNutrition
        fields = [
            'id', 'date', 'total_calories', 'total_protein',
            'total_carbohydrates', 'total_fat', 'food_analyses'
        ]
        read_only_fields = ['id']
