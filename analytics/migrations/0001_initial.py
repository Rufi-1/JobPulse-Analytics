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
            name='SkillDemandSnapshot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('period', models.DateField(help_text='First day of the month this snapshot represents')),
                ('job_count', models.PositiveIntegerField(default=0)),
                ('avg_salary', models.PositiveIntegerField(blank=True, null=True)),
                ('skill', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='demand_snapshots', to='jobs.skill')),
            ],
            options={
                'ordering': ['period'],
            },
        ),
        migrations.CreateModel(
            name='SalaryTrendSnapshot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('location', models.CharField(max_length=150)),
                ('period', models.DateField()),
                ('avg_salary', models.PositiveIntegerField()),
                ('min_salary', models.PositiveIntegerField()),
                ('max_salary', models.PositiveIntegerField()),
                ('job_count', models.PositiveIntegerField(default=0)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='salary_snapshots', to='jobs.jobcategory')),
            ],
            options={
                'ordering': ['period'],
            },
        ),
        migrations.CreateModel(
            name='PredictionQuery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('location', models.CharField(max_length=150)),
                ('experience_level', models.CharField(max_length=15)),
                ('predicted_min', models.PositiveIntegerField()),
                ('predicted_max', models.PositiveIntegerField()),
                ('confidence', models.PositiveSmallIntegerField(help_text='0-100 confidence score')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('category', models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL, to='jobs.jobcategory')),
                ('skills', models.ManyToManyField(blank=True, to='jobs.skill')),
                ('user', models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL, related_name='prediction_queries', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
                'verbose_name_plural': 'Prediction queries',
            },
        ),
        migrations.AlterUniqueTogether(
            name='skilldemandsnapshot',
            unique_together={('skill', 'period')},
        ),
        migrations.AlterUniqueTogether(
            name='salarytrendsnapshot',
            unique_together={('category', 'location', 'period')},
        ),
    ]
