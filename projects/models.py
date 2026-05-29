from django.conf import settings
from django.db import models


PROJECT_NAME_MAX_LENGTH = 200
PROJECT_STATUS_MAX_LENGTH = 6

STATUS_OPEN = "open"
STATUS_CLOSED = "closed"

STATUS_OPEN_VERBOSE = "Open"
STATUS_CLOSED_VERBOSE = "Closed"

PROJECT_OWNER_RELATED_NAME = "owned_projects"
PROJECT_PARTICIPANTS_RELATED_NAME = "participated_projects"

PROJECT_ORDERING_BY_NEWEST = "-created_at"


class Project(models.Model):
    STATUS_OPEN = STATUS_OPEN
    STATUS_CLOSED = STATUS_CLOSED

    STATUS_CHOICES = [
        (STATUS_OPEN, STATUS_OPEN_VERBOSE),
        (STATUS_CLOSED, STATUS_CLOSED_VERBOSE),
    ]

    name = models.CharField(
        "название",
        max_length=PROJECT_NAME_MAX_LENGTH,
    )
    description = models.TextField(
        "описание",
        blank=True,
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name=PROJECT_OWNER_RELATED_NAME,
        verbose_name="автор",
    )

    created_at = models.DateTimeField(
        "дата создания",
        auto_now_add=True,
        db_index=True,
    )

    github_url = models.URLField(
        "GitHub",
        blank=True,
    )

    status = models.CharField(
        "статус",
        max_length=PROJECT_STATUS_MAX_LENGTH,
        choices=STATUS_CHOICES,
        default=STATUS_OPEN,
    )

    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name=PROJECT_PARTICIPANTS_RELATED_NAME,
        verbose_name="участники",
    )

    class Meta:
        ordering = [PROJECT_ORDERING_BY_NEWEST]
        verbose_name = "проект"
        verbose_name_plural = "проекты"

    def __str__(self):
        return self.name