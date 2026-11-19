from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

def create_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    User = apps.get_model('core', 'User')
    viewer, _ = Group.objects.using(schema_editor.connection.alias).get_or_create(name='viewer')
    Group.objects.using(schema_editor.connection.alias).get_or_create(name='admin')
    for user in User.objects.using(schema_editor.connection.alias).filter(is_superuser=False):
        user.groups.add(viewer)

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0008_alter_message_image'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=150)),
                ('text', models.TextField(max_length=5000)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at'], 'verbose_name': 'Pergunta à diretoria', 'verbose_name_plural': 'Perguntas à diretoria'},
        ),
        migrations.RunPython(create_groups, migrations.RunPython.noop),
    ]
