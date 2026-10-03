from rest_framework import serializers
from .models import JobCategory, Skill, Company, JobPosting, JobSkill, SavedJob, Application, JobReview


class JobCategorySerializer(serializers.ModelSerializer):
    job_count = serializers.SerializerMethodField()

    class Meta:
        model = JobCategory
        fields = ['id', 'name', 'slug', 'description', 'icon', 'job_count']

    def get_job_count(self, obj):
        return obj.jobs.filter(is_active=True).count()


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'name', 'slug', 'skill_type']


class CompanySerializer(serializers.ModelSerializer):
    active_job_count = serializers.ReadOnlyField()

    class Meta:
        model = Company
        fields = [
            'id', 'name', 'slug', 'industry', 'size', 'headquarters', 'website',
            'description', 'founded_year', 'active_job_count',
        ]


class JobSkillSerializer(serializers.ModelSerializer):
    skill = SkillSerializer(read_only=True)

    class Meta:
        model = JobSkill
        fields = ['skill', 'importance']


class JobPostingListSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True, default=None)
    salary_display = serializers.ReadOnlyField()

    class Meta:
        model = JobPosting
        fields = [
            'id', 'title', 'slug', 'company_name', 'category_name', 'location',
            'remote_option', 'experience_level', 'employment_type', 'salary_display',
            'salary_min', 'salary_max', 'is_featured', 'posted_at', 'views_count',
        ]


class JobPostingDetailSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)
    category = JobCategorySerializer(read_only=True)
    job_skills = JobSkillSerializer(many=True, read_only=True)
    salary_display = serializers.ReadOnlyField()

    class Meta:
        model = JobPosting
        fields = [
            'id', 'title', 'slug', 'company', 'category', 'job_skills', 'description',
            'responsibilities', 'requirements', 'location', 'remote_option',
            'experience_level', 'employment_type', 'salary_min', 'salary_max',
            'currency', 'salary_display', 'source', 'is_active', 'is_featured',
            'views_count', 'posted_at', 'updated_at', 'expires_at',
        ]


class SavedJobSerializer(serializers.ModelSerializer):
    job = JobPostingListSerializer(read_only=True)
    job_id = serializers.PrimaryKeyRelatedField(
        queryset=JobPosting.objects.all(), source='job', write_only=True
    )

    class Meta:
        model = SavedJob
        fields = ['id', 'job', 'job_id', 'saved_at']
        read_only_fields = ['saved_at']


class ApplicationSerializer(serializers.ModelSerializer):
    job = JobPostingListSerializer(read_only=True)
    job_id = serializers.PrimaryKeyRelatedField(
        queryset=JobPosting.objects.all(), source='job', write_only=True
    )

    class Meta:
        model = Application
        fields = ['id', 'job', 'job_id', 'status', 'resume', 'cover_letter', 'notes', 'applied_at', 'updated_at']
        read_only_fields = ['applied_at', 'updated_at']


class JobReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = JobReview
        fields = ['id', 'company', 'username', 'rating', 'title', 'body', 'created_at']
        read_only_fields = ['created_at']
