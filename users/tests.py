import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import Group
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from users.models import User


class UsersAppTests(TestCase):
    def setUp(self):
        self.user_data = {
            'email': 'newuser@test.ru',
            'phone': '+79991234567',
            'country': 'Россия',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        }

    def test_registration_and_email_verification(self):
        """Регистрация создаёт неактивного пользователя и отправляет токен на почту, переход по ссылке активирует аккаунт."""
        response = self.client.post(reverse('users:register'), data=self.user_data)
        self.assertEqual(response.status_code, 302)

        user = User.objects.get(email='newuser@test.ru')
        self.assertFalse(user.is_active)
        self.assertIsNotNone(user.token)
        self.assertEqual(len(mail.outbox), 1)

        # Переходим по ссылке подтверждения с токеном
        confirm_url = reverse('users:email_confirm', kwargs={'token': user.token})
        confirm_response = self.client.get(confirm_url)
        self.assertEqual(confirm_response.status_code, 302)

        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertIsNone(user.token)

    def test_login_and_profile_access(self):
        """Авторизованный пользователь может открыть свой профиль."""
        user = User.objects.create_user(email='active@test.ru', password='password123', is_active=True)
        self.client.force_login(user)

        response = self.client.get(reverse('users:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'active@test.ru')

    def test_manager_can_block_user(self):
        """Менеджер из группы Managers может просматривать список пользователей и блокировать их."""
        managers_group, _ = Group.objects.get_or_create(name='Managers')
        manager = User.objects.create_user(email='manager@test.ru', password='password123', is_active=True)
        manager.groups.add(managers_group)

        target_user = User.objects.create_user(email='victim@test.ru', password='password123', is_active=True)

        # Обычный пользователь не имеет доступа к списку пользователей
        self.client.force_login(target_user)
        forbidden_resp = self.client.get(reverse('users:user_list'))
        self.assertEqual(forbidden_resp.status_code, 403)

        # Менеджер имеет доступ и может заблокировать
        self.client.force_login(manager)
        list_resp = self.client.get(reverse('users:user_list'))
        self.assertEqual(list_resp.status_code, 200)

        toggle_resp = self.client.post(reverse('users:toggle_active', kwargs={'pk': target_user.pk}))
        self.assertEqual(toggle_resp.status_code, 302)

        target_user.refresh_from_db()
        self.assertFalse(target_user.is_active)
