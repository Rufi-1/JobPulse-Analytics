from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import MinValueValidator


class JobCategory(models.Model):
    """A broad industry / functional category, e.g. Software Engineering, Data Science."""
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Emoji or short icon code")

    class Meta:
        verbose_name_plural = 'Job categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('jobs:category_detail', kwargs={'slug': self.slug})


class Skill(models.Model):
    """A discrete, matchable skill (e.g. Python, SQL, Project Management)."""

    class SkillType(models.TextChoices):
        TECHNICAL = 'technical', 'Technical'
        SOFT = 'soft', 'Soft Skill'
        TOOL = 'tool', 'Tool / Platform'
        CERTIFICATION = 'certification', 'Certification'

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    skill_type = models.CharField(max_length=20, choices=SkillType.choices, default=SkillType.TECHNICAL)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('jobs:skill_detail', kwargs={'slug': self.slug})


class Company(models.Model):
    """An employer posting jobs on the platform."""

    class CompanySize(models.TextChoices):
        STARTUP = 'startup', '1-50 employees'
        SMALL = 'small', '51-200 employees'
        MEDIUM = 'medium', '201-1000 employees'
        LARGE = 'large', '1001-10000 employees'
        ENTERPRISE = 'enterprise', '10000+ employees'

    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='owned_companies', help_text="The employer/recruiter account that manages this company.",
    )
    industry = models.CharField(max_length=100, blank=True)
    size = models.CharField(max_length=20, choices=CompanySize.choices, default=CompanySize.SMALL)
    headquarters = models.CharField(max_length=150, blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    description = models.TextField(blank=True)
    founded_year = models.PositiveIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Companies'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('jobs:company_detail', kwargs={'slug': self.slug})

    @property
    def active_job_count(self):
        return self.jobs.filter(is_active=True).count()


class JobPosting(models.Model):
    """A single job listing, the central entity of the platform."""

    class ExperienceLevel(models.TextChoices):
        ENTRY = 'entry', 'Entry Level (0-2 yrs)'
        MID = 'mid', 'Mid Level (2-5 yrs)'
        SENIOR = 'senior', 'Senior Level (5-9 yrs)'
        LEAD = 'lead', 'Lead / Principal (9+ yrs)'
        EXECUTIVE = 'executive', 'Executive'

    class EmploymentType(models.TextChoices):
        FULL_TIME = 'full_time', 'Full-time'
        PART_TIME = 'part_time', 'Part-time'
        CONTRACT = 'contract', 'Contract'
        INTERNSHIP = 'internship', 'Internship'
        FREELANCE = 'freelance', 'Freelance'

    class RemoteOption(models.TextChoices):
        ONSITE = 'onsite', 'On-site'
        HYBRID = 'hybrid', 'Hybrid'
        REMOTE = 'remote', 'Remote'

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=230, unique=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='jobs')
    category = models.ForeignKey(JobCategory, on_delete=models.SET_NULL, null=True, related_name='jobs')
    skills = models.ManyToManyField(Skill, through='JobSkill', related_name='jobs')

    description = models.TextField()
    responsibilities = models.TextField(blank=True)
    requirements = models.TextField(blank=True)

    location = models.CharField(max_length=150, db_index=True)
    remote_option = models.CharField(max_length=10, choices=RemoteOption.choices, default=RemoteOption.ONSITE)
    experience_level = models.CharField(max_length=15, choices=ExperienceLevel.choices, default=ExperienceLevel.MID)
    employment_type = models.CharField(max_length=15, choices=EmploymentType.choices, default=EmploymentType.FULL_TIME)

    salary_min = models.PositiveIntegerField(validators=[MinValueValidator(0)], blank=True, null=True)
    salary_max = models.PositiveIntegerField(validators=[MinValueValidator(0)], blank=True, null=True)
    currency = models.CharField(max_length=10, default='USD')

    source = models.CharField(max_length=100, default='JobPulse Direct', help_text="Origin of the listing")
    is_active = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False)
    views_count = models.PositiveIntegerField(default=0)

    posted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ['-posted_at']
        indexes = [
            models.Index(fields=['-posted_at']),
            models.Index(fields=['location']),
            models.Index(fields=['experience_level']),
        ]

    def __str__(self):
        return f"{self.title} @ {self.company.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(f"{self.title}-{self.company.name}")[:220]
            slug = base
            counter = 1
            while JobPosting.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                counter += 1
                slug = f"{base}-{counter}"
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('jobs:job_detail', kwargs={'slug': self.slug})

    @property
    def salary_display(self):
        if self.salary_min and self.salary_max:
            return f"{self.currency} {self.salary_min:,} - {self.salary_max:,}"
        if self.salary_min:
            return f"{self.currency} {self.salary_min:,}+"
        return "Not disclosed"

    @property
    def salary_mid(self):
        if self.salary_min and self.salary_max:
            return (self.salary_min + self.salary_max) / 2
        return self.salary_min or self.salary_max or None


class JobSkill(models.Model):
    """Through-model linking a JobPosting to a Skill, with an importance weight."""

    class Importance(models.TextChoices):
        REQUIRED = 'required', 'Required'
        PREFERRED = 'preferred', 'Preferred'
        NICE_TO_HAVE = 'nice_to_have', 'Nice to have'

    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='job_skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='skill_jobs')
    importance = models.CharField(max_length=15, choices=Importance.choices, default=Importance.REQUIRED)

    class Meta:
        unique_together = ('job', 'skill')

    def __str__(self):
        return f"{self.skill.name} ({self.importance}) for {self.job.title}"

    @property
    def weight(self):
        return {'required': 3, 'preferred': 2, 'nice_to_have': 1}.get(self.importance, 1)


class SavedJob(models.Model):
    """A job bookmarked by a user."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_jobs')
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'job')
        ordering = ['-saved_at']

    def __str__(self):
        return f"{self.user.username} saved {self.job.title}"


class Application(models.Model):
    """A user's tracked application to a job posting."""

    class Status(models.TextChoices):
        APPLIED = 'applied', 'Applied'
        UNDER_REVIEW = 'under_review', 'Under Review'
        INTERVIEW = 'interview', 'Interview'
        OFFER = 'offer', 'Offer'
        REJECTED = 'rejected', 'Rejected'
        WITHDRAWN = 'withdrawn', 'Withdrawn'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications')
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.APPLIED)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    cover_letter = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'job')
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.user.username} -> {self.job.title} ({self.status})"


class JobReview(models.Model):
    """A short, anonymous-style rating of a company left by an authenticated user."""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='company_reviews')
    rating = models.PositiveSmallIntegerField(default=5)
    title = models.CharField(max_length=150)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('company', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.rating}★ review of {self.company.name}"
