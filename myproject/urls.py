from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView

from jobs.sitemaps import JobSitemap, StaticViewSitemap

sitemaps = {
    'jobs': JobSitemap,
    'static': StaticViewSitemap,
}

handler404 = 'jobs.views.custom_404'
handler500 = 'jobs.views.custom_500'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('jobs.urls', namespace='jobs')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('analytics/', include('analytics.urls', namespace='analytics')),
    path('api/', include('jobs.api_urls', namespace='jobs_api')),
    path('api/', include('accounts.api_urls', namespace='accounts_api')),
    path('api/', include('analytics.api_urls', namespace='analytics_api')),
    path('api-auth/', include('rest_framework.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
