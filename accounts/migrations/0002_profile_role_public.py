from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='role',
            field=models.CharField(
                choices=[('seeker', 'Job Seeker'), ('employer', 'Employer / Recruiter')],
                default='seeker', max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='profile',
            name='is_public',
            field=models.BooleanField(
                default=False,
                help_text='Allow anyone with the link to view your public profile page.',
            ),
        ),
    ]
