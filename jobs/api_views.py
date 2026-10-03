from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q

from .models import JobCategory, Skill, Company, JobPosting, SavedJob, Application, JobReview
from .serializers import (
    JobCategorySerializer, SkillSerializer, CompanySerializer,
    JobPostingListSerializer, JobPostingDetailSerializer,
    SavedJobSerializer, ApplicationSerializer, JobReviewSerializer,
)


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return getattr(obj, 'user_id', None) == request.user.id


class JobCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = JobCategory.objects.all()
    serializer_class = JobCategorySerializer
    lookup_field = 'slug'
    permission_classes = [permissions.AllowAny]


class SkillViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    lookup_field = 'slug'
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class CompanyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    lookup_field = 'slug'
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'industry', 'headquarters']


class JobPostingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only public API over job postings, with query-param filtering:
    ``?q=&location=&category=&experience_level=&employment_type=&remote_option=&salary_min=``
    """
    queryset = JobPosting.objects.filter(is_active=True).select_related('company', 'category')
    lookup_field = 'slug'
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['posted_at', 'salary_min', 'salary_max', 'views_count']
    ordering = ['-posted_at']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return JobPostingDetailSerializer
        return JobPostingListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        q = params.get('q')
        if q:
            qs = qs.filter(
                Q(title__icontains=q) | Q(company__name__icontains=q) | Q(description__icontains=q)
            ).distinct()
        if params.get('location'):
            qs = qs.filter(location__icontains=params['location'])
        if params.get('category'):
            qs = qs.filter(category__slug=params['category'])
        if params.get('experience_level'):
            qs = qs.filter(experience_level=params['experience_level'])
        if params.get('employment_type'):
            qs = qs.filter(employment_type=params['employment_type'])
        if params.get('remote_option'):
            qs = qs.filter(remote_option=params['remote_option'])
        if params.get('salary_min'):
            qs = qs.filter(salary_max__gte=params['salary_min'])
        return qs

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def recommended(self, request):
        """Rule-based personalized recommendations for the authenticated user."""
        from analytics.engine import recommend_jobs_for_profile
        profile = request.user.profile
        scored = recommend_jobs_for_profile(profile, limit=int(request.query_params.get('limit', 10)))
        results = []
        for job, result in scored:
            data = JobPostingListSerializer(job).data
            data['match_score'] = result['score']
            data['match_reasons'] = result['reasons']
            results.append(data)
        return Response(results)


class SavedJobViewSet(viewsets.ModelViewSet):
    serializer_class = SavedJobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SavedJob.objects.filter(user=self.request.user).select_related('job__company')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Application.objects.filter(user=self.request.user).select_related('job__company')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class JobReviewViewSet(viewsets.ModelViewSet):
    serializer_class = JobReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        qs = JobReview.objects.select_related('user', 'company')
        company_slug = self.request.query_params.get('company')
        if company_slug:
            qs = qs.filter(company__slug=company_slug)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
