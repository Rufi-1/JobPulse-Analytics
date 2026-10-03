from rest_framework.routers import DefaultRouter
from . import api_views

app_name = 'jobs_api'

router = DefaultRouter()
router.register('categories', api_views.JobCategoryViewSet, basename='category')
router.register('skills', api_views.SkillViewSet, basename='skill')
router.register('companies', api_views.CompanyViewSet, basename='company')
router.register('jobs', api_views.JobPostingViewSet, basename='job')
router.register('saved-jobs', api_views.SavedJobViewSet, basename='savedjob')
router.register('applications', api_views.ApplicationViewSet, basename='application')
router.register('reviews', api_views.JobReviewViewSet, basename='review')

urlpatterns = router.urls
