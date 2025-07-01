from rest_framework import serializers
from .models import FoodAnalysis, DailyNutrition


class FoodAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodAnalysis
        fields = [
            'id', 'food_name', 'description', 'image_url', 'calories',
            'protein', 'carbohydrates', 'fat', 'fiber', 'sugar', 'sodium',
            'analysis_summary', 'recommendations', 'analyzed_at'
        ]
        read_only_fields = ['id', 'analyzed_at']


class FoodAnalysisRequestSerializer(serializers.Serializer):
    food_name = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    image_base64 = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        if not attrs.get('food_name') and not attrs.get('image_base64'):
            raise serializers.ValidationError("음식 이름 또는 이미지 중 하나는 필수입니다.")
        return attrs


class DailyNutritionSerializer(serializers.ModelSerializer):
    food_analyses = FoodAnalysisSerializer(many=True, read_only=True)
    
    class Meta:
        model = DailyNutrition
        fields = [
            'id', 'date', 'total_calories', 'total_protein',
            'total_carbohydrates', 'total_fat', 'food_analyses',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
