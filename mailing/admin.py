from django.contrib import admin
from mailing.models import Recipient, Message, Mailing, MailingAttempt


@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'owner')
    search_fields = ('full_name', 'email')
    list_filter = ('owner',)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'owner')
    search_fields = ('subject', 'body')
    list_filter = ('owner',)


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'start_time', 'end_time', 'current_status', 'owner')
    list_filter = ('status', 'owner')
    filter_horizontal = ('recipients',)

    @admin.display(description='Текущий статус')
    def current_status(self, obj):
        return obj.current_status


@admin.register(MailingAttempt)
class MailingAttemptAdmin(admin.ModelAdmin):
    list_display = ('id', 'mailing', 'attempt_time', 'status')
    list_filter = ('status', 'mailing')
    readonly_fields = ('attempt_time',)


