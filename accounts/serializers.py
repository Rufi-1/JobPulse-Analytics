from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile
from jobs.serializers import SkillSerializer
from jobs.models import Skill


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    skills = SkillSerializer(many=True, read_only=True)
    skill_ids = serializers.PrimaryKeyRelatedField(
        queryset=Skill.objects.all(), source='skills', many=True, write_only=True, required=False
    )
    completeness = serializers.ReadOnlyField()

    class Meta:
        model = Profile
        fields = [
            'id', 'username', 'headline', 'bio', 'avatar', 'desired_role',
            'desired_location', 'experience_level', 'open_to_remote', 'expected_salary',
            'skills', 'skill_ids', 'linkedin_url', 'github_url', 'portfolio_url', 'completeness',
        ]


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'date_joined', 'profile']
        read_only_fields = ['date_joined']
