from django.db import migrations


def create_superadmin_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.using(schema_editor.connection.alias).get_or_create(name='superadmin')


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0010_question_answers'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(create_superadmin_group, migrations.RunPython.noop),
    ]
