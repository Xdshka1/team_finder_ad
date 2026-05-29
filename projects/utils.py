from urllib.parse import urlparse

from django import forms


PROJECT_DESCRIPTION_TEXTAREA_ROWS = 6

GITHUB_HOSTS = {"github.com", "www.github.com"}
ALLOWED_URL_SCHEMES = {"http", "https"}


def validate_github_url(value):
    value = (value or "").strip()

    if not value:
        return value

    parsed = urlparse(value)

    if parsed.scheme not in ALLOWED_URL_SCHEMES or not parsed.netloc:
        raise forms.ValidationError("Введите корректную ссылку.")

    if parsed.netloc.lower() not in GITHUB_HOSTS:
        raise forms.ValidationError("Ссылка должна вести на GitHub.")

    return value