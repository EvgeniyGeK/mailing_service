import secrets
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView, DetailView

from users.forms import UserRegisterForm, UserProfileForm
from users.models import User
from django.views import View
from django.views.generic import ListView
from mailing.views import is_manager


class RegisterView(CreateView):
    model = User
    form_class = UserRegisterForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('users:login')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False
        token = secrets.token_hex(16)
        user.token = token
        user.save()

        host = self.request.get_host()
        url = f'http://{host}/users/email-confirm/{token}/'
        send_mail(
            subject='Подтверждение регистрации в сервисе рассылок',
            message=f'Здравствуйте! Для подтверждения вашей почты перейдите по ссылке: {url}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )
        messages.info(self.request, 'На ваш email отправлена ссылка для подтверждения регистрации.')
        return super().form_valid(form)


def email_verification(request, token):
    user = get_object_or_404(User, token=token)
    user.is_active = True
    user.token = None
    user.save()
    messages.success(request, 'Email успешно подтверждён! Теперь вы можете войти в систему.')
    return redirect(reverse('users:login'))


class ProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'users/profile.html'
    context_object_name = 'user_obj'

    def get_object(self, queryset=None):
        return self.request.user


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = 'users/profile_form.html'
    success_url = reverse_lazy('users:profile')

    def get_object(self, queryset=None):
        return self.request.user

class ManagerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return is_manager(self.request.user)


class UserListView(LoginRequiredMixin, ManagerRequiredMixin, ListView):
    model = User
    template_name = 'users/user_list.html'
    context_object_name = 'users_list'


class ToggleUserActiveView(LoginRequiredMixin, ManagerRequiredMixin, View):
    def post(self, request, pk):
        target_user = get_object_or_404(User, pk=pk)
        if target_user.is_superuser:
            messages.error(request, 'Нельзя заблокировать суперпользователя.')
        else:
            target_user.is_active = not target_user.is_active
            target_user.save(update_fields=['is_active'])
            status_text = 'разблокирован' if target_user.is_active else 'заблокирован'
            messages.info(request, f'Пользователь {target_user.email} {status_text}.')
        return redirect('users:user_list')

