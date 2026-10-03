from django.contrib import admin
from .models import SkillDemandSnapshot, SalaryTrendSnapshot, PredictionQuery


@admin.register(SkillDemandSnapshot)
class SkillDemandSnapshotAdmin(admin.ModelAdmin):
    list_display = ('skill', 'period', 'job_count', 'avg_salary')
    list_filter = ('period',)
    search_fields = ('skill__name',)
    autocomplete_fields = ['skill']


@admin.register(SalaryTrendSnapshot)
class SalaryTrendSnapshotAdmin(admin.ModelAdmin):
    list_display = ('category', 'location', 'period', 'avg_salary', 'min_salary', 'max_salary', 'job_count')
    list_filter = ('period', 'category')
    search_fields = ('location', 'category__name')
    autocomplete_fields = ['category']


@admin.register(PredictionQuery)
class PredictionQueryAdmin(admin.ModelAdmin):
    list_display = ('category', 'location', 'experience_level', 'predicted_min', 'predicted_max', 'confidence', 'created_at')
    list_filter = ('experience_level', 'created_at')
    search_fields = ('location',)
    readonly_fields = ('created_at',)
