from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from mailing.models import Recipient, Message, Mailing, MailingAttempt
from mailing.services import send_mailing
from users.models import User


class MailingServiceTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(email='user1@test.ru', password='password123', is_active=True)
        self.user2 = User.objects.create_user(email='user2@test.ru', password='password123', is_active=True)

        self.recipient = Recipient.objects.create(
            email='client@test.ru',
            full_name='Иванов Иван',
            owner=self.user1
        )
        self.message = Message.objects.create(
            subject='Тестовая тема',
            body='Тестовый текст письма',
            owner=self.user1
        )

    def test_anonymous_access_restricted(self):
        """Неавторизованный пользователь видит главную, но перенаправляется со списка рассылок."""
        home_response = self.client.get(reverse('mailing:home'))
        self.assertEqual(home_response.status_code, 200)

        list_response = self.client.get(reverse('mailing:mailing_list'))
        self.assertEqual(list_response.status_code, 302)

    def test_owner_isolation(self):
        """Пользователь видит только свои рассылки и не может редактировать чужие."""
        mailing = Mailing.objects.create(
            start_time=timezone.now() - timedelta(minutes=5),
            end_time=timezone.now() + timedelta(hours=1),
            message=self.message,
            owner=self.user1
        )
        mailing.recipients.add(self.recipient)

        # Входим под вторым пользователем
        self.client.force_login(self.user2)
        response = self.client.get(reverse('mailing:mailing_list'))
        self.assertNotContains(response, 'Тестовая тема')

        # Попытка открыть чужую рассылку возвращает 403 Forbidden
        detail_response = self.client.get(reverse('mailing:mailing_detail', kwargs={'pk': mailing.pk}))
        self.assertEqual(detail_response.status_code, 403)

    def test_send_mailing_creates_attempt(self):
        """Отправка рассылки создаёт успешную попытку в журнале."""
        mailing = Mailing.objects.create(
            start_time=timezone.now() - timedelta(minutes=5),
            end_time=timezone.now() + timedelta(hours=1),
            message=self.message,
            owner=self.user1
        )
        mailing.recipients.add(self.recipient)

        success, _ = send_mailing(mailing)
        self.assertTrue(success)
        self.assertEqual(MailingAttempt.objects.count(), 1)
        self.assertEqual(MailingAttempt.objects.first().status, MailingAttempt.STATUS_SUCCESS)


