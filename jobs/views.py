from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from django.conf import settings

from .models import JobPosting, Company, JobCategory, Skill, SavedJob, Application, JobReview
from .forms import JobSearchForm, JobReviewForm, CompanyForm, JobPostingForm, ApplicationForm, ApplicationStatusForm


def home(request):
    featured_jobs = (
        JobPosting.objects.filter(is_active=True, is_featured=True)
        .select_related('company', 'category')[:6]
    )
    if featured_jobs.count() < 6:
        extra = (
            JobPosting.objects.filter(is_active=True)
            .exclude(id__in=[j.id for j in featured_jobs])
            .select_related('company', 'category')[: 6 - featured_jobs.count()]
        )
        featured_jobs = list(featured_jobs) + list(extra)

    top_categories = (
        JobCategory.objects.annotate(job_count=Count('jobs', filter=Q(jobs__is_active=True)))
        .order_by('-job_count')[:8]
    )
    top_companies = (
        Company.objects.annotate(job_count=Count('jobs', filter=Q(jobs__is_active=True)))
        .order_by('-job_count')[:8]
    )

    from analytics.engine import trending_skills
    trending = trending_skills(limit=10)

    context = {
        'featured_jobs': featured_jobs,
        'top_categories': top_categories,
        'top_companies': top_companies,
        'trending_skills': trending,
        'search_form': JobSearchForm(),
        'meta_description': 'Discover live job openings, in-demand skills, and salary trends '
                             'powered by data-driven analytics.',
    }
    return render(request, 'jobs/home.html', context)


def job_list(request):
    form = JobSearchForm(request.GET or None)
    jobs = JobPosting.objects.filter(is_active=True).select_related('company', 'category')

    if form.is_valid():
        data = form.cleaned_data
        if data.get('q'):
            q = data['q']
            jobs = jobs.filter(
                Q(title__icontains=q) | Q(company__name__icontains=q)
                | Q(description__icontains=q) | Q(skills__name__icontains=q)
            ).distinct()
        if data.get('location'):
            jobs = jobs.filter(location__icontains=data['location'])
        if data.get('category'):
            jobs = jobs.filter(category=data['category'])
        if data.get('experience_level'):
            jobs = jobs.filter(experience_level=data['experience_level'])
        if data.get('employment_type'):
            jobs = jobs.filter(employment_type=data['employment_type'])
        if data.get('remote_option'):
            jobs = jobs.filter(remote_option=data['remote_option'])
        if data.get('salary_min'):
            jobs = jobs.filter(salary_max__gte=data['salary_min'])
        sort = data.get('sort') or '-posted_at'
        jobs = jobs.order_by(sort)
    else:
        jobs = jobs.order_by('-posted_at')

    paginator = Paginator(jobs, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    saved_job_ids = set()
    if request.user.is_authenticated:
        saved_job_ids = set(
            SavedJob.objects.filter(user=request.user, job__in=page_obj.object_list)
            .values_list('job_id', flat=True)
        )

    context = {
        'form': form,
        'page_obj': page_obj,
        'jobs': page_obj.object_list,
        'total_results': paginator.count,
        'saved_job_ids': saved_job_ids,
        'meta_description': 'Search and filter thousands of job postings by location, '
                             'category, experience level, and salary.',
    }
    return render(request, 'jobs/job_list.html', context)


def job_detail(request, slug):
    job = get_object_or_404(
        JobPosting.objects.select_related('company', 'category').prefetch_related('job_skills__skill'),
        slug=slug,
    )
    JobPosting.objects.filter(pk=job.pk).update(views_count=job.views_count + 1)

    related_jobs = (
        JobPosting.objects.filter(is_active=True, category=job.category)
        .exclude(pk=job.pk).select_related('company')[:4]
    )

    is_saved = False
    has_applied = False
    if request.user.is_authenticated:
        is_saved = SavedJob.objects.filter(user=request.user, job=job).exists()
        has_applied = Application.objects.filter(user=request.user, job=job).exists()

    context = {
        'job': job,
        'related_jobs': related_jobs,
        'is_saved': is_saved,
        'has_applied': has_applied,
        'required_skills': job.job_skills.filter(importance='required'),
        'preferred_skills': job.job_skills.exclude(importance='required'),
        'meta_description': f"{job.title} at {job.company.name} — {job.location}. {job.salary_display}.",
    }
    return render(request, 'jobs/job_detail.html', context)


@login_required
@require_POST
def toggle_save_job(request, slug):
    job = get_object_or_404(JobPosting, slug=slug)
    saved, created = SavedJob.objects.get_or_create(user=request.user, job=job)
    if not created:
        saved.delete()
        is_saved = False
    else:
        is_saved = True

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'saved': is_saved})

    messages.success(request, 'Job saved.' if is_saved else 'Job removed from saved list.')
    return redirect('jobs:job_detail', slug=slug)


def _notify(subject, message, recipient_email):
    """Best-effort email notification — never breaks the request if sending fails
    (e.g. unconfigured SMTP credentials)."""
    if not recipient_email:
        return
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient_email], fail_silently=True)
    except Exception:
        pass


@login_required
def apply_to_job(request, slug):
    job = get_object_or_404(JobPosting, slug=slug)

    if Application.objects.filter(user=request.user, job=job).exists():
        messages.info(request, 'You already applied to this job.')
        return redirect('jobs:job_detail', slug=slug)

    if request.method == 'POST':
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.user = request.user
            application.job = job
            application.save()
            messages.success(request, f'Application submitted for {job.title} at {job.company.name}.')

            if job.company.owner_id:
                _notify(
                    subject=f'New application: {job.title}',
                    message=(
                        f'{request.user.username} applied to "{job.title}" at {job.company.name}.\n\n'
                        f'Review it from your employer dashboard: My Postings -> {job.title} -> Applicants.'
                    ),
                    recipient_email=job.company.owner.email,
                )
            return redirect('jobs:job_detail', slug=slug)
    else:
        form = ApplicationForm()

    return render(request, 'jobs/apply_form.html', {'form': form, 'job': job})


def company_list(request):
    companies = (
        Company.objects.annotate(job_count=Count('jobs', filter=Q(jobs__is_active=True)))
        .order_by('-job_count', 'name')
    )
    q = request.GET.get('q')
    if q:
        companies = companies.filter(Q(name__icontains=q) | Q(industry__icontains=q))

    paginator = Paginator(companies, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'companies': page_obj.object_list,
        'query': q or '',
        'meta_description': 'Browse companies hiring now, with reviews and open roles.',
    }
    return render(request, 'jobs/company_list.html', context)


def company_detail(request, slug):
    company = get_object_or_404(Company, slug=slug)
    jobs = company.jobs.filter(is_active=True).order_by('-posted_at')
    reviews = company.reviews.select_related('user').all()
    rating_avg = reviews.aggregate(avg=Avg('rating'))['avg']

    review_form = None
    if request.user.is_authenticated:
        already_reviewed = reviews.filter(user=request.user).exists()
        if not already_reviewed:
            if request.method == 'POST':
                review_form = JobReviewForm(request.POST)
                if review_form.is_valid():
                    review = review_form.save(commit=False)
                    review.company = company
                    review.user = request.user
                    review.save()
                    messages.success(request, 'Thanks — your review was posted.')
                    return redirect('jobs:company_detail', slug=slug)
            else:
                review_form = JobReviewForm()

    context = {
        'company': company,
        'jobs': jobs,
        'reviews': reviews,
        'rating_avg': rating_avg,
        'review_form': review_form,
        'meta_description': f"{company.name} — {company.industry or 'company'} profile, "
                             f"open roles, and employee reviews.",
    }
    return render(request, 'jobs/company_detail.html', context)


def category_detail(request, slug):
    category = get_object_or_404(JobCategory, slug=slug)
    jobs = category.jobs.filter(is_active=True).select_related('company').order_by('-posted_at')
    paginator = Paginator(jobs, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'category': category,
        'page_obj': page_obj,
        'jobs': page_obj.object_list,
        'meta_description': category.description or f"Open {category.name} roles.",
    }
    return render(request, 'jobs/category_detail.html', context)


def skill_detail(request, slug):
    skill = get_object_or_404(Skill, slug=slug)
    jobs = (
        JobPosting.objects.filter(is_active=True, skills=skill)
        .select_related('company').order_by('-posted_at')
    )
    paginator = Paginator(jobs, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'skill': skill,
        'page_obj': page_obj,
        'jobs': page_obj.object_list,
        'meta_description': f"Jobs requiring {skill.name} — see openings and demand trends.",
    }
    return render(request, 'jobs/skill_detail.html', context)


def custom_404(request, exception=None):
    return render(request, '404.html', status=404)


def custom_500(request):
    return render(request, '500.html', status=500)


# ---------------------------------------------------------------------------
# Employer / recruiter job-posting flow
# ---------------------------------------------------------------------------

def _require_employer(request):
    """Return an error message if the user isn't allowed to manage job postings, else None."""
    if not request.user.is_authenticated:
        return 'Please log in first.'
    if not request.user.profile.is_employer:
        return 'This area is for employer/recruiter accounts. Job seeker accounts cannot post jobs.'
    return None


@login_required
def company_setup(request):
    """Create or edit the single company an employer account manages."""
    error = _require_employer(request)
    if error:
        messages.error(request, error)
        return redirect('accounts:dashboard')

    company = Company.objects.filter(owner=request.user).first()
    if request.method == 'POST':
        form = CompanyForm(request.POST, request.FILES, instance=company)
        if form.is_valid():
            company = form.save(commit=False)
            company.owner = request.user
            company.save()
            messages.success(request, f'{company.name} is set up. You can now post jobs.')
            return redirect('jobs:my_job_postings')
    else:
        form = CompanyForm(instance=company)

    return render(request, 'jobs/company_form.html', {'form': form, 'company': company})


@login_required
def my_job_postings(request):
    error = _require_employer(request)
    if error:
        messages.error(request, error)
        return redirect('accounts:dashboard')

    company = Company.objects.filter(owner=request.user).first()
    if not company:
        messages.info(request, 'Set up your company profile first, then you can post jobs.')
        return redirect('jobs:company_setup')

    postings = (
        company.jobs.annotate(application_count=Count('applications'))
        .order_by('-posted_at')
    )
    context = {'company': company, 'postings': postings}
    return render(request, 'jobs/employer_job_list.html', context)


@login_required
def job_applicants(request, slug):
    error = _require_employer(request)
    if error:
        messages.error(request, error)
        return redirect('accounts:dashboard')

    job = get_object_or_404(JobPosting, slug=slug)
    if job.company.owner_id != request.user.id:
        messages.error(request, "You can only view applicants for your own company's job postings.")
        return redirect('jobs:my_job_postings')

    if request.method == 'POST':
        application = get_object_or_404(Application, pk=request.POST.get('application_id'), job=job)
        old_status = application.status  # must capture BEFORE binding the form —
        # ModelForm.is_valid() mutates `instance` in place via construct_instance(),
        # so reading this after is_valid() would already see the new value.
        form = ApplicationStatusForm(request.POST, instance=application)
        if form.is_valid():
            form.save()
            if form.cleaned_data['status'] != old_status:
                _notify(
                    subject=f'Your application status changed: {job.title}',
                    message=(
                        f'Your application for "{job.title}" at {job.company.name} is now marked as '
                        f'"{application.get_status_display()}".'
                    ),
                    recipient_email=application.user.email,
                )
                messages.success(request, f'Updated {application.user.username}\'s status.')
        return redirect('jobs:job_applicants', slug=slug)

    applications = (
        Application.objects.filter(job=job)
        .select_related('user', 'user__profile')
        .order_by('-applied_at')
    )
    status_choices = Application.Status.choices
    context = {'job': job, 'applications': applications, 'status_choices': status_choices}
    return render(request, 'jobs/job_applicants.html', context)


@login_required
def job_create(request):
    error = _require_employer(request)
    if error:
        messages.error(request, error)
        return redirect('accounts:dashboard')

    company = Company.objects.filter(owner=request.user).first()
    if not company:
        messages.info(request, 'Set up your company profile first, then you can post jobs.')
        return redirect('jobs:company_setup')

    if request.method == 'POST':
        form = JobPostingForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.company = company
            job.save()
            form.save_m2m()
            messages.success(request, f'"{job.title}" has been posted.')
            return redirect('jobs:my_job_postings')
    else:
        form = JobPostingForm()

    return render(request, 'jobs/job_form.html', {'form': form, 'company': company, 'is_new': True})


@login_required
def job_edit(request, slug):
    error = _require_employer(request)
    if error:
        messages.error(request, error)
        return redirect('accounts:dashboard')

    job = get_object_or_404(JobPosting, slug=slug)
    if job.company.owner_id != request.user.id:
        messages.error(request, "You can only edit your own company's job postings.")
        return redirect('jobs:my_job_postings')

    if request.method == 'POST':
        form = JobPostingForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{job.title}" has been updated.')
            return redirect('jobs:my_job_postings')
    else:
        form = JobPostingForm(instance=job)

    return render(request, 'jobs/job_form.html', {'form': form, 'company': job.company, 'is_new': False, 'job': job})


@login_required
@require_POST
def job_toggle_active(request, slug):
    job = get_object_or_404(JobPosting, slug=slug)
    if job.company.owner_id != request.user.id:
        messages.error(request, "You can only manage your own company's job postings.")
        return redirect('jobs:my_job_postings')
    job.is_active = not job.is_active
    job.save(update_fields=['is_active'])
    messages.success(request, f'"{job.title}" is now {"active" if job.is_active else "inactive"}.')
    return redirect('jobs:my_job_postings')
