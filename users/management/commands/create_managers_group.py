from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Создаёт группу Managers с необходимыми правами доступа'

    def handle(self, *args, **options):
        group, created = Group.objects.get_or_create(name='Managers')
        permissions = Permission.objects.filter(
            codename__in=[
                'view_mailing',
                'can_disable_mailing',
                'view_recipient',
                'view_user',
            ]
        )
        group.permissions.set(permissions)
        self.stdout.write(self.style.SUCCESS('Группа Managers успешно создана и настроена!'))
