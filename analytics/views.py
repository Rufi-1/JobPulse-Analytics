import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Q

from jobs.models import JobPosting, JobCategory, Skill
from .models import SkillDemandSnapshot, SalaryTrendSnapshot, PredictionQuery
from .forms import SalaryPredictionForm
from .engine import predict_salary, trending_skills, recommend_jobs_for_profile


def dashboard(request):
    total_jobs = JobPosting.objects.filter(is_active=True).count()

    category_breakdown = list(
        JobCategory.objects.annotate(job_count=Count('jobs', filter=Q(jobs__is_active=True)))
        .filter(job_count__gt=0).order_by('-job_count')[:8]
        .values('name', 'job_count')
    )

    location_breakdown = list(
        JobPosting.objects.filter(is_active=True)
        .values('location').annotate(job_count=Count('id')).order_by('-job_count')[:8]
    )

    top_skills = trending_skills(limit=10)
    skill_labels = [s.name for s in top_skills]
    skill_data = [s.demand for s in top_skills]

    experience_breakdown = list(
        JobPosting.objects.filter(is_active=True)
        .values('experience_level').annotate(job_count=Count('id')).order_by('experience_level')
    )

    remote_breakdown = list(
        JobPosting.objects.filter(is_active=True)
        .values('remote_option').annotate(job_count=Count('id'))
    )

    avg_salary_by_category = list(
        JobPosting.objects.filter(is_active=True, salary_min__isnull=False, salary_max__isnull=False)
        .values('category__name')
        .annotate(avg_salary=Avg('salary_min'))
        .exclude(category__name__isnull=True)
        .order_by('-avg_salary')[:8]
    )

    salary_trend = list(
        SalaryTrendSnapshot.objects.values('period')
        .annotate(avg_salary=Avg('avg_salary'))
        .order_by('period')
    )

    context = {
        'total_jobs': total_jobs,
        'total_companies': JobPosting.objects.values('company').distinct().count(),
        'category_labels': json.dumps([c['name'] for c in category_breakdown]),
        'category_data': json.dumps([c['job_count'] for c in category_breakdown]),
        'location_labels': json.dumps([l['location'] for l in location_breakdown]),
        'location_data': json.dumps([l['job_count'] for l in location_breakdown]),
        'skill_labels': json.dumps(skill_labels),
        'skill_data': json.dumps(skill_data),
        'experience_labels': json.dumps([dict(JobPosting.ExperienceLevel.choices).get(e['experience_level'], e['experience_level']) for e in experience_breakdown]),
        'experience_data': json.dumps([e['job_count'] for e in experience_breakdown]),
        'remote_labels': json.dumps([dict(JobPosting.RemoteOption.choices).get(r['remote_option'], r['remote_option']) for r in remote_breakdown]),
        'remote_data': json.dumps([r['job_count'] for r in remote_breakdown]),
        'salary_category_labels': json.dumps([c['category__name'] for c in avg_salary_by_category]),
        'salary_category_data': json.dumps([round(c['avg_salary'] or 0) for c in avg_salary_by_category]),
        'salary_trend_labels': json.dumps([t['period'].strftime('%b %Y') for t in salary_trend]),
        'salary_trend_data': json.dumps([round(t['avg_salary'] or 0) for t in salary_trend]),
        'meta_description': 'Live market analytics: in-demand skills, salary trends by role and '
                             'location, and hiring activity across the platform.',
    }
    return render(request, 'analytics/dashboard.html', context)


def salary_predictor(request):
    prediction = None
    used_profile = False

    if request.method == 'POST':
        form = SalaryPredictionForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            prediction = predict_salary(
                category=data.get('category'),
                location=data.get('location', ''),
                experience_level=data.get('experience_level', 'mid'),
                skills=data.get('skills'),
            )
            PredictionQuery.objects.create(
                user=request.user if request.user.is_authenticated else None,
                category=data.get('category'),
                location=data.get('location', ''),
                experience_level=data.get('experience_level', 'mid'),
                predicted_min=prediction.predicted_min,
                predicted_max=prediction.predicted_max,
                confidence=prediction.confidence,
            ).skills.set(data.get('skills') or [])
    else:
        initial = {}
        # Pre-fill from the logged-in user's own profile so their market
        # analysis is one click away instead of re-entering everything.
        if request.user.is_authenticated and request.GET.get('use_profile') == '1':
            profile = request.user.profile
            initial = {
                'location': profile.desired_location,
                'experience_level': profile.experience_level,
                'skills': profile.skills.all(),
            }
            used_profile = True
        form = SalaryPredictionForm(initial=initial)

    context = {
        'form': form,
        'prediction': prediction,
        'used_profile': used_profile,
        'meta_description': 'Get a rule-based salary prediction for any role, location, '
                             'experience level, and skill set — powered by live market data.',
    }
    return render(request, 'analytics/salary_predictor.html', context)


@login_required
def market_position(request):
    """Personalized market analysis: how the user's own skills and salary
    expectations stack up against current demand — the feature that answers
    'what does the market think of ME', not just 'what does a role pay'."""
    from .engine import skill_gap_analysis, market_position_for_profile

    profile = request.user.profile
    gap_analysis = skill_gap_analysis(profile)
    position = market_position_for_profile(profile)

    context = {
        'profile': profile,
        'gap_analysis': gap_analysis,
        'position': position,
        'meta_description': 'Your personal market position: how your skills and salary '
                             'expectations compare to current demand.',
    }
    return render(request, 'analytics/market_position.html', context)


@login_required
def recommendations(request):
    profile = request.user.profile
    scored = recommend_jobs_for_profile(profile, limit=20)
    context = {
        'profile': profile,
        'scored_jobs': scored,
        'meta_description': 'Personalized job recommendations based on your skills, '
                             'desired role, and experience.',
    }
    return render(request, 'analytics/recommendations.html', context)
