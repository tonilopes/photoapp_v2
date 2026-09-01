from django.db import migrations


def grant_gestor_event_permissions(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    gestor, _ = Group.objects.get_or_create(name='Gestor')
    permissions = Permission.objects.filter(
        content_type__app_label='gestcaptur',
        content_type__model='evento',
        codename__in=['add_evento', 'change_evento', 'delete_evento', 'view_evento'],
    )
    gestor.permissions.add(*permissions)


class Migration(migrations.Migration):
    dependencies = [
        ('gestcaptur', '0010_alter_aluno_codigo_turma_alter_evento_codigo_turma'),
    ]

    operations = [
        migrations.RunPython(grant_gestor_event_permissions, migrations.RunPython.noop),
    ]