from rest_framework import viewsets, permissions, views
from rest_framework.response import Response

from jobs.models import JobCategory, Skill
from .models import SkillDemandSnapshot, SalaryTrendSnapshot, PredictionQuery
from .serializers import (
    SkillDemandSnapshotSerializer, SalaryTrendSnapshotSerializer,
    PredictionQuerySerializer, SalaryPredictionRequestSerializer,
)
from .engine import predict_salary


class SkillDemandSnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SkillDemandSnapshot.objects.select_related('skill').all()
    serializer_class = SkillDemandSnapshotSerializer
    permission_classes = [permissions.AllowAny]


class SalaryTrendSnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SalaryTrendSnapshot.objects.select_related('category').all()
    serializer_class = SalaryTrendSnapshotSerializer
    permission_classes = [permissions.AllowAny]


class PredictionQueryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PredictionQuerySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PredictionQuery.objects.filter(user=self.request.user)


class SalaryPredictionView(views.APIView):
    """POST a role/location/experience/skills combo, get back a predicted salary range."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SalaryPredictionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        category = None
        if data.get('category'):
            category = JobCategory.objects.filter(pk=data['category']).first()

        skills = Skill.objects.filter(pk__in=data.get('skills') or [])

        result = predict_salary(
            category=category,
            location=data.get('location', ''),
            experience_level=data.get('experience_level', 'mid'),
            skills=skills,
        )

        return Response({
            'predicted_min': result.predicted_min,
            'predicted_max': result.predicted_max,
            'predicted_mid': result.predicted_mid,
            'confidence': result.confidence,
            'basis': result.basis,
            'factors': result.factors,
        })
