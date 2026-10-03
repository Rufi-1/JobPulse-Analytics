from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import api_views

app_name = 'analytics_api'

router = DefaultRouter()
router.register('skill-demand', api_views.SkillDemandSnapshotViewSet, basename='skill-demand')
router.register('salary-trends', api_views.SalaryTrendSnapshotViewSet, basename='salary-trend')
router.register('prediction-history', api_views.PredictionQueryViewSet, basename='prediction-history')

urlpatterns = [
    path('predict-salary/', api_views.SalaryPredictionView.as_view(), name='predict-salary'),
    path('', include(router.urls)),
]
