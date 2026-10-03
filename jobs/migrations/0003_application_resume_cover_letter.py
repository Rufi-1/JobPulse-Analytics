from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0002_company_owner'),
    ]

    operations = [
        migrations.AddField(
            model_name='application',
            name='resume',
            field=models.FileField(blank=True, null=True, upload_to='resumes/'),
        ),
        migrations.AddField(
            model_name='application',
            name='cover_letter',
            field=models.TextField(blank=True),
        ),
    ]
