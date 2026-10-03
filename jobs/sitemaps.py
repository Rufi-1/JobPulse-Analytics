from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import JobPosting


class JobSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.8

    def items(self):
        return JobPosting.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at


class StaticViewSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.5

    def items(self):
        return ['jobs:home', 'jobs:job_list', 'jobs:company_list', 'analytics:dashboard']

    def location(self, item):
        return reverse(item)
