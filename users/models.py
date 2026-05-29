from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.db.models import Q

from .managers import UserManager
from .utils import (
    PHONE_MAX_LENGTH,
    generate_avatar,
    generate_avatar_filename,
)


USER_NAME_MAX_LENGTH = 124
USER_SURNAME_MAX_LENGTH = 124
USER_ABOUT_MAX_LENGTH = 256

AVATAR_UPLOAD_PATH = "avatars/"
EMPTY_STRING = ""

UNIQUE_PHONE_CONSTRAINT_NAME = "unique_not_empty_phone"


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField("email", unique=True)

    name = models.CharField(
        "имя",
        max_length=USER_NAME_MAX_LENGTH,
    )
    surname = models.CharField(
        "фамилия",
        max_length=USER_SURNAME_MAX_LENGTH,
    )

    avatar = models.ImageField(
        "аватар",
        upload_to=AVATAR_UPLOAD_PATH,
        blank=True,
    )

    phone = models.CharField(
        "телефон",
        max_length=PHONE_MAX_LENGTH,
        blank=True,
        default=EMPTY_STRING,
    )
    github_url = models.URLField("GitHub", blank=True)

    about = models.TextField(
        "о себе",
        max_length=USER_ABOUT_MAX_LENGTH,
        blank=True,
    )

    is_active = models.BooleanField("активный", default=True)
    is_staff = models.BooleanField("администратор", default=False)

    favorites = models.ManyToManyField(
        "projects.Project",
        blank=True,
        related_name="interested_users",
        verbose_name="избранные проекты",
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "surname"]

    class Meta:
        verbose_name = "пользователь"
        verbose_name_plural = "пользователи"
        constraints = [
            models.UniqueConstraint(
                fields=["phone"],
                condition=~Q(phone=EMPTY_STRING),
                name=UNIQUE_PHONE_CONSTRAINT_NAME,
            )
        ]

    def __str__(self):
        return f"{self.name} {self.surname}"

    def save(self, *args, **kwargs):
        if not self.avatar:
            self.avatar.save(
                generate_avatar_filename(),
                generate_avatar(self.name, self.email),
                save=False,
            )

        super().save(*args, **kwargs)