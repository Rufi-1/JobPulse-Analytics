from django.db import models
from django.conf import settings
from django.urls import reverse
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    """Extended profile data for a platform user (job seeker or employer)."""

    class ExperienceLevel(models.TextChoices):
        ENTRY = 'entry', 'Entry Level (0-2 yrs)'
        MID = 'mid', 'Mid Level (2-5 yrs)'
        SENIOR = 'senior', 'Senior Level (5-9 yrs)'
        LEAD = 'lead', 'Lead / Principal (9+ yrs)'
        EXECUTIVE = 'executive', 'Executive'

    class Role(models.TextChoices):
        SEEKER = 'seeker', 'Job Seeker'
        EMPLOYER = 'employer', 'Employer / Recruiter'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.SEEKER)
    headline = models.CharField(max_length=150, blank=True, help_text="e.g. 'Backend Engineer'")
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    desired_role = models.CharField(max_length=150, blank=True)
    desired_location = models.CharField(max_length=150, blank=True)
    experience_level = models.CharField(max_length=15, choices=ExperienceLevel.choices, default=ExperienceLevel.ENTRY)
    open_to_remote = models.BooleanField(default=True)
    expected_salary = models.PositiveIntegerField(blank=True, null=True)

    skills = models.ManyToManyField('jobs.Skill', blank=True, related_name='user_profiles')

    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)

    is_public = models.BooleanField(
        default=False, help_text="Allow anyone with the link to view your public profile page."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile: {self.user.username}"

    def get_absolute_url(self):
        return reverse('accounts:dashboard')

    def get_public_url(self):
        return reverse('accounts:public_profile', kwargs={'username': self.user.username})

    @property
    def is_employer(self):
        return self.role == self.Role.EMPLOYER

    @property
    def completeness(self):
        """Rough percentage of how complete the profile is — used to nudge users."""
        fields = [
            self.headline, self.bio, self.desired_role, self.desired_location,
            self.expected_salary, self.linkedin_url,
        ]
        filled = sum(1 for f in fields if f)
        skill_bonus = 1 if self.skills.exists() else 0
        total_checks = len(fields) + 1
        return int(round((filled + skill_bonus) / total_checks * 100))


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_save_profile(sender, instance, created, **kwargs):
    """Ensure every User always has an associated Profile."""
    if created:
        Profile.objects.create(user=instance)
    else:
        Profile.objects.get_or_create(user=instance)
