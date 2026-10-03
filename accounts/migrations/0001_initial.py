import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('jobs', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('headline', models.CharField(blank=True, help_text="e.g. 'Backend Engineer'", max_length=150)),
                ('bio', models.TextField(blank=True)),
                ('avatar', models.ImageField(blank=True, null=True, upload_to='avatars/')),
                ('desired_role', models.CharField(blank=True, max_length=150)),
                ('desired_location', models.CharField(blank=True, max_length=150)),
                ('experience_level', models.CharField(choices=[('entry', 'Entry Level (0-2 yrs)'), ('mid', 'Mid Level (2-5 yrs)'), ('senior', 'Senior Level (5-9 yrs)'), ('lead', 'Lead / Principal (9+ yrs)'), ('executive', 'Executive')], default='entry', max_length=15)),
                ('open_to_remote', models.BooleanField(default=True)),
                ('expected_salary', models.PositiveIntegerField(blank=True, null=True)),
                ('linkedin_url', models.URLField(blank=True)),
                ('github_url', models.URLField(blank=True)),
                ('portfolio_url', models.URLField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('skills', models.ManyToManyField(blank=True, related_name='user_profiles', to='jobs.skill')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
