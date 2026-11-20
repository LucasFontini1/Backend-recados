from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0011_superadmin_group'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='legal_accepted_at',
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='terms_version',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
        migrations.AddField(
            model_name='user',
            name='privacy_version',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
    ]
