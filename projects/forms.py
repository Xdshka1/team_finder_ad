from urllib.parse import urlparse

from django import forms

from .models import Project


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description", "github_url", "status"]
        labels = {
            "name": "Название проекта",
            "description": "Описание проекта",
            "github_url": "Ссылка на GitHub",
            "status": "Статус",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 6}),
        }

    def clean_github_url(self):
        value = (self.cleaned_data.get("github_url") or "").strip()

        if not value:
            return value

        parsed = urlparse(value)

        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise forms.ValidationError("Введите корректную ссылку.")

        if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
            raise forms.ValidationError("Ссылка должна вести на GitHub.")

        return value
