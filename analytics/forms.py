from django import forms
from jobs.models import JobCategory, Skill, JobPosting


class SalaryPredictionForm(forms.Form):
    category = forms.ModelChoiceField(
        queryset=JobCategory.objects.all(), required=False, empty_label='Any category',
        widget=forms.Select(attrs={'class': 'input'})
    )
    location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'input', 'placeholder': 'e.g. San Francisco, Remote, Bangalore'})
    )
    experience_level = forms.ChoiceField(
        choices=JobPosting.ExperienceLevel.choices,
        initial='mid', widget=forms.Select(attrs={'class': 'input'})
    )
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(), required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text='Check every skill you have — each one can add a premium to the estimate.',
    )
