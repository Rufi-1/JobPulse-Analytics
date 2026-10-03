from django.db import models
from django.conf import settings


class SkillDemandSnapshot(models.Model):
    """Monthly aggregated demand count for a skill — the backbone of trend charts."""
    skill = models.ForeignKey('jobs.Skill', on_delete=models.CASCADE, related_name='demand_snapshots')
    period = models.DateField(help_text="First day of the month this snapshot represents")
    job_count = models.PositiveIntegerField(default=0)
    avg_salary = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        unique_together = ('skill', 'period')
        ordering = ['period']

    def __str__(self):
        return f"{self.skill.name} — {self.period:%b %Y}: {self.job_count} jobs"


class SalaryTrendSnapshot(models.Model):
    """Monthly aggregated salary statistics for a (role/category, location) pair."""
    category = models.ForeignKey('jobs.JobCategory', on_delete=models.CASCADE, related_name='salary_snapshots')
    location = models.CharField(max_length=150)
    period = models.DateField()
    avg_salary = models.PositiveIntegerField()
    min_salary = models.PositiveIntegerField()
    max_salary = models.PositiveIntegerField()
    job_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('category', 'location', 'period')
        ordering = ['period']

    def __str__(self):
        return f"{self.category.name} in {self.location} — {self.period:%b %Y}"


class PredictionQuery(models.Model):
    """A logged salary-prediction request, so the platform can learn what users search for."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='prediction_queries',
    )
    category = models.ForeignKey('jobs.JobCategory', on_delete=models.SET_NULL, null=True)
    location = models.CharField(max_length=150)
    experience_level = models.CharField(max_length=15)
    skills = models.ManyToManyField('jobs.Skill', blank=True)

    predicted_min = models.PositiveIntegerField()
    predicted_max = models.PositiveIntegerField()
    confidence = models.PositiveSmallIntegerField(help_text="0-100 confidence score")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Prediction queries'

    def __str__(self):
        return f"Prediction for {self.category} in {self.location} ({self.created_at:%Y-%m-%d})"
