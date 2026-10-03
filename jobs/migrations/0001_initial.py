import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='JobCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, unique=True)),
                ('slug', models.SlugField(blank=True, max_length=140, unique=True)),
                ('description', models.TextField(blank=True)),
                ('icon', models.CharField(blank=True, help_text='Emoji or short icon code', max_length=50)),
            ],
            options={
                'verbose_name_plural': 'Job categories',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Skill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('slug', models.SlugField(blank=True, max_length=120, unique=True)),
                ('skill_type', models.CharField(choices=[('technical', 'Technical'), ('soft', 'Soft Skill'), ('tool', 'Tool / Platform'), ('certification', 'Certification')], default='technical', max_length=20)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, unique=True)),
                ('slug', models.SlugField(blank=True, max_length=170, unique=True)),
                ('industry', models.CharField(blank=True, max_length=100)),
                ('size', models.CharField(choices=[('startup', '1-50 employees'), ('small', '51-200 employees'), ('medium', '201-1000 employees'), ('large', '1001-10000 employees'), ('enterprise', '10000+ employees')], default='small', max_length=20)),
                ('headquarters', models.CharField(blank=True, max_length=150)),
                ('website', models.URLField(blank=True)),
                ('logo', models.ImageField(blank=True, null=True, upload_to='logos/')),
                ('description', models.TextField(blank=True)),
                ('founded_year', models.PositiveIntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name_plural': 'Companies',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='JobPosting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('slug', models.SlugField(blank=True, max_length=230, unique=True)),
                ('description', models.TextField()),
                ('responsibilities', models.TextField(blank=True)),
                ('requirements', models.TextField(blank=True)),
                ('location', models.CharField(db_index=True, max_length=150)),
                ('remote_option', models.CharField(choices=[('onsite', 'On-site'), ('hybrid', 'Hybrid'), ('remote', 'Remote')], default='onsite', max_length=10)),
                ('experience_level', models.CharField(choices=[('entry', 'Entry Level (0-2 yrs)'), ('mid', 'Mid Level (2-5 yrs)'), ('senior', 'Senior Level (5-9 yrs)'), ('lead', 'Lead / Principal (9+ yrs)'), ('executive', 'Executive')], default='mid', max_length=15)),
                ('employment_type', models.CharField(choices=[('full_time', 'Full-time'), ('part_time', 'Part-time'), ('contract', 'Contract'), ('internship', 'Internship'), ('freelance', 'Freelance')], default='full_time', max_length=15)),
                ('salary_min', models.PositiveIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0)])),
                ('salary_max', models.PositiveIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0)])),
                ('currency', models.CharField(default='USD', max_length=10)),
                ('source', models.CharField(default='JobPulse Direct', help_text='Origin of the listing', max_length=100)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('is_featured', models.BooleanField(default=False)),
                ('views_count', models.PositiveIntegerField(default=0)),
                ('posted_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('expires_at', models.DateField(blank=True, null=True)),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='jobs', to='jobs.jobcategory')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='jobs', to='jobs.company')),
            ],
            options={
                'ordering': ['-posted_at'],
            },
        ),
        migrations.CreateModel(
            name='JobSkill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('importance', models.CharField(choices=[('required', 'Required'), ('preferred', 'Preferred'), ('nice_to_have', 'Nice to have')], default='required', max_length=15)),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='job_skills', to='jobs.jobposting')),
                ('skill', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='skill_jobs', to='jobs.skill')),
            ],
        ),
        migrations.AddField(
            model_name='jobposting',
            name='skills',
            field=models.ManyToManyField(related_name='jobs', through='jobs.JobSkill', to='jobs.skill'),
        ),
        migrations.CreateModel(
            name='SavedJob',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('saved_at', models.DateTimeField(auto_now_add=True)),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saved_by', to='jobs.jobposting')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saved_jobs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-saved_at'],
            },
        ),
        migrations.CreateModel(
            name='Application',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('applied', 'Applied'), ('under_review', 'Under Review'), ('interview', 'Interview'), ('offer', 'Offer'), ('rejected', 'Rejected'), ('withdrawn', 'Withdrawn')], default='applied', max_length=15)),
                ('notes', models.TextField(blank=True)),
                ('applied_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='applications', to='jobs.jobposting')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='applications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-applied_at'],
            },
        ),
        migrations.CreateModel(
            name='JobReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.PositiveSmallIntegerField(default=5)),
                ('title', models.CharField(max_length=150)),
                ('body', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='jobs.company')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='company_reviews', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='jobposting',
            index=models.Index(fields=['-posted_at'], name='jobs_jobpos_posted__1f5e21_idx'),
        ),
        migrations.AddIndex(
            model_name='jobposting',
            index=models.Index(fields=['location'], name='jobs_jobpos_locatio_6e2b8b_idx'),
        ),
        migrations.AddIndex(
            model_name='jobposting',
            index=models.Index(fields=['experience_level'], name='jobs_jobpos_experie_9c1a3e_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='jobskill',
            unique_together={('job', 'skill')},
        ),
        migrations.AlterUniqueTogether(
            name='savedjob',
            unique_together={('user', 'job')},
        ),
        migrations.AlterUniqueTogether(
            name='application',
            unique_together={('user', 'job')},
        ),
        migrations.AlterUniqueTogether(
            name='jobreview',
            unique_together={('company', 'user')},
        ),
    ]
