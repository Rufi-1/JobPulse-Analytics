from django.contrib import admin
from .models import (
    JobCategory, Skill, Company, JobPosting, JobSkill, SavedJob, Application, JobReview,
)


class JobSkillInline(admin.TabularInline):
    model = JobSkill
    extra = 1
    autocomplete_fields = ['skill']


@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'job_count')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

    @admin.display(description='Active jobs')
    def job_count(self, obj):
        return obj.jobs.filter(is_active=True).count()


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'skill_type', 'slug')
    list_filter = ('skill_type',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'industry', 'size', 'headquarters', 'active_job_count')
    list_filter = ('size', 'industry')
    search_fields = ('name', 'industry', 'headquarters', 'owner__username')
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ['owner']


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'company', 'category', 'location', 'experience_level',
        'employment_type', 'remote_option', 'salary_display', 'is_active',
        'is_featured', 'views_count', 'posted_at',
    )
    list_filter = (
        'is_active', 'is_featured', 'experience_level', 'employment_type',
        'remote_option', 'category',
    )
    search_fields = ('title', 'company__name', 'location', 'description')
    prepopulated_fields = {'slug': ('title',)}
    autocomplete_fields = ['company', 'category']
    inlines = [JobSkillInline]
    date_hierarchy = 'posted_at'
    list_editable = ('is_active', 'is_featured')
    readonly_fields = ('views_count', 'posted_at', 'updated_at')
    fieldsets = (
        ('Core details', {'fields': ('title', 'slug', 'company', 'category', 'description')}),
        ('Requirements', {'fields': ('responsibilities', 'requirements')}),
        ('Logistics', {'fields': ('location', 'remote_option', 'experience_level', 'employment_type')}),
        ('Compensation', {'fields': ('salary_min', 'salary_max', 'currency')}),
        ('Status', {'fields': ('is_active', 'is_featured', 'source', 'expires_at')}),
        ('Metrics', {'fields': ('views_count', 'posted_at', 'updated_at')}),
    )


@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display = ('user', 'job', 'saved_at')
    search_fields = ('user__username', 'job__title')
    autocomplete_fields = ['user', 'job']


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'job', 'status', 'has_resume', 'applied_at', 'updated_at')
    list_filter = ('status',)
    search_fields = ('user__username', 'job__title')
    autocomplete_fields = ['user', 'job']
    list_editable = ('status',)

    @admin.display(description='Resume', boolean=True)
    def has_resume(self, obj):
        return bool(obj.resume)


@admin.register(JobReview)
class JobReviewAdmin(admin.ModelAdmin):
    list_display = ('company', 'user', 'rating', 'title', 'created_at')
    list_filter = ('rating',)
    search_fields = ('company__name', 'user__username', 'title')
