from rest_framework import serializers
from .models import SkillDemandSnapshot, SalaryTrendSnapshot, PredictionQuery


class SkillDemandSnapshotSerializer(serializers.ModelSerializer):
    skill_name = serializers.CharField(source='skill.name', read_only=True)

    class Meta:
        model = SkillDemandSnapshot
        fields = ['id', 'skill', 'skill_name', 'period', 'job_count', 'avg_salary']


class SalaryTrendSnapshotSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = SalaryTrendSnapshot
        fields = ['id', 'category', 'category_name', 'location', 'period', 'avg_salary', 'min_salary', 'max_salary', 'job_count']


class PredictionQuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = PredictionQuery
        fields = [
            'id', 'category', 'location', 'experience_level', 'skills',
            'predicted_min', 'predicted_max', 'confidence', 'created_at',
        ]
        read_only_fields = ['predicted_min', 'predicted_max', 'confidence', 'created_at']


class SalaryPredictionRequestSerializer(serializers.Serializer):
    category = serializers.IntegerField(required=False, allow_null=True)
    location = serializers.CharField(required=False, allow_blank=True, default='')
    experience_level = serializers.ChoiceField(
        choices=['entry', 'mid', 'senior', 'lead', 'executive'], default='mid'
    )
    skills = serializers.ListField(child=serializers.IntegerField(), required=False, default=list)
