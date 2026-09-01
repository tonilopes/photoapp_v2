from django.db import migrations


EVENT_PERMISSIONS = [
    ('download_fotos_evento', 'Pode baixar fotos de eventos'),
    ('download_cadastros_evento', 'Pode baixar cadastros de eventos'),
    ('finalizar_captura_evento', 'Pode encerrar captura de eventos'),
]


def create_event_role_permissions(apps, schema_editor):
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    content_type, _ = ContentType.objects.get_or_create(app_label='gestcaptur', model='evento')
    permissions = []
    for codename, name in EVENT_PERMISSIONS:
        permission, _ = Permission.objects.get_or_create(
            content_type=content_type,
            codename=codename,
            defaults={'name': name},
        )
        permissions.append(permission)
    gestor, _ = Group.objects.get_or_create(name='Gestor')
    gestor.permissions.add(*permissions)


class Migration(migrations.Migration):
    dependencies = [
        ('gestcaptur', '0011_grant_gestor_event_permissions'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='evento',
            options={
                'ordering': ['-data', '-created_at'],
                'permissions': tuple(EVENT_PERMISSIONS),
            },
        ),
        migrations.RunPython(create_event_role_permissions, migrations.RunPython.noop),
    ]