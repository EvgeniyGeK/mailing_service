from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm, PasswordResetForm, SetPasswordForm
from mailing.forms import StyleFormMixin
from users.models import User


class UserRegisterForm(StyleFormMixin, UserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'avatar', 'phone', 'country', 'password1', 'password2')


class UserLoginForm(StyleFormMixin, AuthenticationForm):
    pass


class UserProfileForm(StyleFormMixin, UserChangeForm):
    password = None

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'avatar', 'phone', 'country')


class CustomPasswordResetForm(StyleFormMixin, PasswordResetForm):
    pass


class CustomSetPasswordForm(StyleFormMixin, SetPasswordForm):
    pass
