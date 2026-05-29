from django import forms
from django.contrib.auth import authenticate

from .models import User
from .utils import (
    PHONE_MAX_LENGTH,
    PROFILE_ABOUT_TEXTAREA_ROWS,
    validate_github_url,
    validate_phone,
)


class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput,
    )

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
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput,
    )

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
    phone = forms.CharField(
        label="Телефон",
        max_length=PHONE_MAX_LENGTH,
        required=True,
    )

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
            "about": forms.Textarea(
                attrs={"rows": PROFILE_ABOUT_TEXTAREA_ROWS}
            ),
        }

    def clean_phone(self):
        return validate_phone(
            self.cleaned_data.get("phone"),
            user_instance=self.instance,
        )

    def clean_github_url(self):
        return validate_github_url(self.cleaned_data.get("github_url"))