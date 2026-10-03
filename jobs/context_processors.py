from django.conf import settings
from django.core.cache import cache


def site_metrics(request):
    """Expose lightweight, cheap sitewide numbers + SEO metadata to every template."""
    from jobs.models import JobPosting, Company

    metrics = cache.get('site_metrics')
    if metrics is None:
        metrics = {
            'total_active_jobs': JobPosting.objects.filter(is_active=True).count(),
            'total_companies': Company.objects.count(),
        }
        cache.set('site_metrics', metrics, 300)

    return {
        'SITE_NAME': settings.SITE_NAME,
        'SITE_DESCRIPTION': settings.SITE_DESCRIPTION,
        'site_metrics': metrics,
    }
