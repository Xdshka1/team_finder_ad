import re
from urllib.parse import urlparse

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordChangeForm

from .models import User


PHONE_RE = re.compile(r"^(8\d{10}|\+7\d{10})$")


def normalize_phone(phone):
    phone = (phone or "").strip()

    if phone.startswith("8") and len(phone) == 11:
        return "+7" + phone[1:]

    return phone


def validate_github_url(value):
    value = (value or "").strip()

    if not value:
        return value

    parsed = urlparse(value)

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise forms.ValidationError("Введите корректную ссылку.")

    if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
        raise forms.ValidationError("Ссылка должна вести на GitHub.")

    return value


class RegisterForm(forms.ModelForm):
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["name", "surname", "email", "password"]
        labels = {
            "name": "Имя",
            "surname": "Фамилия",
            "email": "Email",
        }

    def clean_email(self):
        email = self.cleaned_data["email"].lower()

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже существует.")

        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].lower()
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()

        return user


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()

        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if email and password:
            user = authenticate(email=email.lower(), password=password)

            if user is None:
                raise forms.ValidationError("Неверный имейл или пароль")

            cleaned_data["user"] = user

        return cleaned_data


class EditProfileForm(forms.ModelForm):
    phone = forms.CharField(label="Телефон", max_length=12, required=True)

    class Meta:
        model = User
        fields = ["name", "surname", "avatar", "about", "phone", "github_url"]
        labels = {
            "name": "Имя",
            "surname": "Фамилия",
            "avatar": "Аватар",
            "about": "О себе",
            "phone": "Телефон",
            "github_url": "GitHub",
        }
        widgets = {
            "about": forms.Textarea(attrs={"rows": 4}),
        }

    def clean_phone(self):
        phone = normalize_phone(self.cleaned_data.get("phone"))

        if not phone:
            raise forms.ValidationError("Введите номер телефона.")

        if not PHONE_RE.match(phone):
            raise forms.ValidationError(
                "Телефон должен быть в формате 8XXXXXXXXXX или +7XXXXXXXXXX."
            )

        users = User.objects.filter(phone=phone)

        if self.instance.pk:
            users = users.exclude(pk=self.instance.pk)

        if users.exists():
            raise forms.ValidationError("Пользователь с таким телефоном уже существует.")

        return phone

    def clean_github_url(self):
        return validate_github_url(self.cleaned_data.get("github_url"))


class UserPasswordChangeForm(PasswordChangeForm):
    pass
