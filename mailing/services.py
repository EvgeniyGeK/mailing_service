import smtplib
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from mailing.models import Mailing, MailingAttempt


def send_mailing(mailing: Mailing):
    """Отправляет рассылку всем её получателям и фиксирует попытки рассылки."""
    now = timezone.now()

    if now < mailing.start_time or now > mailing.end_time:
        return False, "Сейчас отправка недоступна: проверьте период рассылки."

    if mailing.end_time < now:
        mailing.status = Mailing.STATUS_COMPLETED
        mailing.save(update_fields=['status'])
        return False, 'Время окончания рассылки уже прошло.'

    mailing.status = Mailing.STATUS_STARTED
    mailing.save(update_fields=['status'])

    recipients = mailing.recipients.all()
    if not recipients.exists():
        return False, 'В рассылке не выбрано ни одного получателя.'

    success_count = 0
    error_count = 0
    attempts_to_create = []

    for recipient in recipients:
        try:
            send_mail(
                subject=mailing.message.subject,
                message=mailing.message.body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                fail_silently=False,
            )
            attempts_to_create.append(
                MailingAttempt(
                    status=MailingAttempt.STATUS_SUCCESS,
                    server_response=f'Успешно отправлено получателю {recipient.email}',
                    mailing=mailing,
                )
            )
            success_count += 1
        except (smtplib.SMTPException, Exception) as e:
            attempts_to_create.append(
                MailingAttempt(
                    status=MailingAttempt.STATUS_FAILED,
                    server_response=f'Ошибка при отправке {recipient.email}: {str(e)}',
                    mailing=mailing,
                )
            )
            error_count += 1

    # Пакетная запись всех попыток одним запросом в БД
    if attempts_to_create:
        MailingAttempt.objects.bulk_create(attempts_to_create)

    if timezone.now() >= mailing.end_time:
        mailing.status = Mailing.STATUS_COMPLETED
        mailing.save(update_fields=['status'])

    return True, f'Отправка завершена. Успешно: {success_count}, с ошибкой: {error_count}.'
