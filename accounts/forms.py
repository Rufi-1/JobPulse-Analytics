from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'input'}))
    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'input'}))
    last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'input'}))
    role = forms.ChoiceField(
        choices=Profile.Role.choices, initial=Profile.Role.SEEKER,
        widget=forms.RadioSelect,
        label='I am signing up as a...',
        help_text="Job seekers browse and apply to jobs. Employers/recruiters post and manage job listings.",
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'input'})
        self.fields['password1'].widget.attrs.update({'class': 'input'})
        self.fields['password2'].widget.attrs.update({'class': 'input'})
        # Keep the role field first so it's the first thing a new user sees.
        self.order_fields(['role', 'username', 'first_name', 'last_name', 'email', 'password1', 'password2'])

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'headline', 'bio', 'avatar', 'desired_role', 'desired_location',
            'experience_level', 'open_to_remote', 'expected_salary', 'skills',
            'linkedin_url', 'github_url', 'portfolio_url', 'is_public',
        ]
        widgets = {
            'headline': forms.TextInput(attrs={'class': 'input', 'placeholder': 'e.g. Backend Engineer'}),
            'bio': forms.Textarea(attrs={'class': 'input', 'rows': 4}),
            'desired_role': forms.TextInput(attrs={'class': 'input'}),
            'desired_location': forms.TextInput(attrs={'class': 'input'}),
            'experience_level': forms.Select(attrs={'class': 'input'}),
            'expected_salary': forms.NumberInput(attrs={'class': 'input'}),
            'skills': forms.CheckboxSelectMultiple,
            'linkedin_url': forms.URLInput(attrs={'class': 'input'}),
            'github_url': forms.URLInput(attrs={'class': 'input'}),
            'portfolio_url': forms.URLInput(attrs={'class': 'input'}),
        }
        help_texts = {
            'skills': 'Check every skill that applies — this powers your recommendations and market analysis.',
            'is_public': 'Turns on a shareable, read-only profile page anyone with the link can view.',
        }


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'input'}),
            'last_name': forms.TextInput(attrs={'class': 'input'}),
            'email': forms.EmailInput(attrs={'class': 'input'}),
        }
