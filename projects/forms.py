from django import forms

from .models import Project
from .utils import PROJECT_DESCRIPTION_TEXTAREA_ROWS, validate_github_url


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
            "description": forms.Textarea(
                attrs={"rows": PROJECT_DESCRIPTION_TEXTAREA_ROWS}
            ),
        }

    def clean_github_url(self):
        return validate_github_url(self.cleaned_data.get("github_url"))