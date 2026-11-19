from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0009_question_and_groups'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='answer',
            field=models.TextField(blank=True, max_length=5000),
        ),
        migrations.AddField(
            model_name='question',
            name='answered_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='question',
            name='answered_by',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='answered_questions', to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
