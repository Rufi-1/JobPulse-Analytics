from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import Http404

from .forms import SignUpForm, ProfileForm, UserUpdateForm
from .models import Profile
from jobs.models import SavedJob, Application, Company


def register(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            profile = user.profile
            profile.role = form.cleaned_data['role']
            profile.save()
            login(request, user)
            messages.success(request, f'Welcome to the platform, {user.first_name or user.username}!')
            if profile.is_employer:
                messages.info(request, 'Next, set up your company so you can start posting jobs.')
                return redirect('jobs:company_setup')
            return redirect('accounts:profile_edit')
    else:
        form = SignUpForm()

    return render(request, 'registration/register.html', {'form': form})


@login_required
def dashboard(request):
    profile = request.user.profile

    if profile.is_employer:
        company = Company.objects.filter(owner=request.user).first()
        postings = []
        total_applications = 0
        if company:
            postings = company.jobs.order_by('-posted_at')[:5]
            total_applications = Application.objects.filter(job__company=company).count()
        context = {
            'profile': profile,
            'company': company,
            'postings': postings,
            'posting_count': company.jobs.count() if company else 0,
            'total_applications': total_applications,
        }
        return render(request, 'accounts/dashboard_employer.html', context)

    from analytics.engine import recommend_jobs_for_profile, skill_gap_analysis, market_position_for_profile

    saved_jobs = SavedJob.objects.filter(user=request.user).select_related('job__company')[:5]
    applications = Application.objects.filter(user=request.user).select_related('job__company')[:5]

    recommendations = []
    gap_analysis = None
    position = None
    if profile.skills.exists() or profile.desired_role:
        recommendations = recommend_jobs_for_profile(profile, limit=6)
        gap_analysis = skill_gap_analysis(profile, limit=4)
        position = market_position_for_profile(profile)

    context = {
        'profile': profile,
        'saved_jobs': saved_jobs,
        'applications': applications,
        'recommendations': recommendations,
        'gap_analysis': gap_analysis,
        'position': position,
        'applications_count': Application.objects.filter(user=request.user).count(),
        'saved_count': SavedJob.objects.filter(user=request.user).count(),
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile_edit(request):
    profile = request.user.profile
    if request.method == 'POST':
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
        user_form = UserUpdateForm(request.POST, instance=request.user)
        if profile_form.is_valid() and user_form.is_valid():
            profile_form.save()
            user_form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('accounts:dashboard')
    else:
        profile_form = ProfileForm(instance=profile)
        user_form = UserUpdateForm(instance=request.user)

    return render(request, 'accounts/profile_edit.html', {
        'profile_form': profile_form,
        'user_form': user_form,
        'profile': profile,
    })


@login_required
def my_applications(request):
    applications = (
        Application.objects.filter(user=request.user)
        .select_related('job__company').order_by('-applied_at')
    )
    return render(request, 'accounts/my_applications.html', {'applications': applications})


@login_required
def my_saved_jobs(request):
    saved_jobs = (
        SavedJob.objects.filter(user=request.user)
        .select_related('job__company').order_by('-saved_at')
    )
    return render(request, 'accounts/my_saved_jobs.html', {'saved_jobs': saved_jobs})


def public_profile(request, username):
    """A read-only, shareable profile page — only visible if the owner opted in."""
    user = get_object_or_404(User, username=username)
    profile = getattr(user, 'profile', None)
    is_owner = request.user.is_authenticated and request.user.id == user.id

    if not profile or (not profile.is_public and not is_owner):
        raise Http404("This profile is private or doesn't exist.")

    context = {'profile_user': user, 'profile': profile, 'is_owner': is_owner}
    return render(request, 'accounts/public_profile.html', context)
