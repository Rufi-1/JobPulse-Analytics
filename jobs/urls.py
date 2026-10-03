from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('', views.home, name='home'),
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/<slug:slug>/', views.job_detail, name='job_detail'),
    path('jobs/<slug:slug>/save/', views.toggle_save_job, name='toggle_save_job'),
    path('jobs/<slug:slug>/apply/', views.apply_to_job, name='apply_to_job'),
    path('companies/', views.company_list, name='company_list'),
    path('companies/<slug:slug>/', views.company_detail, name='company_detail'),
    path('categories/<slug:slug>/', views.category_detail, name='category_detail'),
    path('skills/<slug:slug>/', views.skill_detail, name='skill_detail'),

    # Employer / recruiter job-posting flow
    path('employer/company/', views.company_setup, name='company_setup'),
    path('employer/jobs/', views.my_job_postings, name='my_job_postings'),
    path('employer/jobs/new/', views.job_create, name='job_create'),
    path('employer/jobs/<slug:slug>/edit/', views.job_edit, name='job_edit'),
    path('employer/jobs/<slug:slug>/toggle/', views.job_toggle_active, name='job_toggle_active'),
    path('employer/jobs/<slug:slug>/applicants/', views.job_applicants, name='job_applicants'),
]
