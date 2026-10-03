from django import forms
from .models import JobCategory, JobReview, JobPosting, Company, Skill, Application


class JobSearchForm(forms.Form):
    q = forms.CharField(
        required=False, label='Keyword',
        widget=forms.TextInput(attrs={'placeholder': 'Job title, company, or skill...', 'class': 'input'})
    )
    location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'City, state, or "remote"', 'class': 'input'})
    )
    category = forms.ModelChoiceField(
        queryset=JobCategory.objects.all(), required=False, empty_label='All categories',
        widget=forms.Select(attrs={'class': 'input'})
    )
    experience_level = forms.ChoiceField(
        choices=[('', 'Any experience')] + list(JobPosting.ExperienceLevel.choices),
        required=False, widget=forms.Select(attrs={'class': 'input'})
    )
    employment_type = forms.ChoiceField(
        choices=[('', 'Any type')] + list(JobPosting.EmploymentType.choices),
        required=False, widget=forms.Select(attrs={'class': 'input'})
    )
    remote_option = forms.ChoiceField(
        choices=[('', 'Any arrangement')] + list(JobPosting.RemoteOption.choices),
        required=False, widget=forms.Select(attrs={'class': 'input'})
    )
    salary_min = forms.IntegerField(
        required=False, min_value=0,
        widget=forms.NumberInput(attrs={'placeholder': 'Min. salary', 'class': 'input'})
    )
    sort = forms.ChoiceField(
        choices=[
            ('-posted_at', 'Newest first'),
            ('posted_at', 'Oldest first'),
            ('-salary_max', 'Highest salary'),
            ('salary_min', 'Lowest salary'),
            ('-views_count', 'Most viewed'),
        ],
        required=False, initial='-posted_at', widget=forms.Select(attrs={'class': 'input'})
    )


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['resume', 'cover_letter']
        widgets = {
            'cover_letter': forms.Textarea(attrs={
                'class': 'input', 'rows': 6,
                'placeholder': "Tell the employer why you're a good fit (optional).",
            }),
        }
        help_texts = {
            'resume': 'Optional — PDF, DOC, or DOCX recommended.',
        }


class ApplicationStatusForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['status']
        widgets = {'status': forms.Select(attrs={'class': 'input'})}


class JobReviewForm(forms.ModelForm):
    class Meta:
        model = JobReview
        fields = ['rating', 'title', 'body']
        widgets = {
            'rating': forms.Select(choices=[(i, f'{i} star{"s" if i != 1 else ""}') for i in range(1, 6)],
                                    attrs={'class': 'input'}),
            'title': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Summarize your experience'}),
            'body': forms.Textarea(attrs={'class': 'input', 'rows': 4, 'placeholder': 'Share more detail...'}),
        }


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'industry', 'size', 'headquarters', 'website', 'logo', 'description', 'founded_year']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input'}),
            'industry': forms.TextInput(attrs={'class': 'input'}),
            'size': forms.Select(attrs={'class': 'input'}),
            'headquarters': forms.TextInput(attrs={'class': 'input'}),
            'website': forms.URLInput(attrs={'class': 'input'}),
            'description': forms.Textarea(attrs={'class': 'input', 'rows': 4}),
            'founded_year': forms.NumberInput(attrs={'class': 'input'}),
        }


class JobPostingForm(forms.ModelForm):
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(), required=False, widget=forms.CheckboxSelectMultiple,
        help_text='Select the skills required or preferred for this role.',
    )

    class Meta:
        model = JobPosting
        fields = [
            'title', 'category', 'description', 'responsibilities', 'requirements',
            'location', 'remote_option', 'experience_level', 'employment_type',
            'salary_min', 'salary_max', 'currency', 'is_active', 'expires_at',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'input'}),
            'category': forms.Select(attrs={'class': 'input'}),
            'description': forms.Textarea(attrs={'class': 'input', 'rows': 5}),
            'responsibilities': forms.Textarea(attrs={'class': 'input', 'rows': 4}),
            'requirements': forms.Textarea(attrs={'class': 'input', 'rows': 4}),
            'location': forms.TextInput(attrs={'class': 'input'}),
            'remote_option': forms.Select(attrs={'class': 'input'}),
            'experience_level': forms.Select(attrs={'class': 'input'}),
            'employment_type': forms.Select(attrs={'class': 'input'}),
            'salary_min': forms.NumberInput(attrs={'class': 'input'}),
            'salary_max': forms.NumberInput(attrs={'class': 'input'}),
            'currency': forms.TextInput(attrs={'class': 'input'}),
            'expires_at': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['skills'].initial = self.instance.skills.all()

    def save(self, commit=True):
        job = super().save(commit=commit)
        if commit:
            self._save_skills(job)
        else:
            self.save_m2m = lambda: self._save_skills(job)
        return job

    def _save_skills(self, job):
        from .models import JobSkill
        selected = self.cleaned_data.get('skills') or []
        job.job_skills.exclude(skill__in=selected).delete()
        existing_ids = set(job.job_skills.values_list('skill_id', flat=True))
        for skill in selected:
            if skill.id not in existing_ids:
                JobSkill.objects.create(job=job, skill=skill, importance='required')
