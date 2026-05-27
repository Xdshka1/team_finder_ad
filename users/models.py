import random
import uuid
from io import BytesIO

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.files.base import ContentFile
from django.db import models
from django.db.models import Q
from PIL import Image, ImageDraw, ImageFont


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("У пользователя должен быть email")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("name", "Admin")
        extra_fields.setdefault("surname", "User")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Суперпользователь должен иметь is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Суперпользователь должен иметь is_superuser=True")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField("email", unique=True)
    name = models.CharField("имя", max_length=124)
    surname = models.CharField("фамилия", max_length=124)

    avatar = models.ImageField("аватар", upload_to="avatars/", blank=True)

    phone = models.CharField("телефон", max_length=12, blank=True, default="")
    github_url = models.URLField("GitHub", blank=True)
    about = models.TextField("о себе", max_length=256, blank=True)

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
                condition=~Q(phone=""),
                name="unique_not_empty_phone",
            )
        ]

    def __str__(self):
        return f"{self.name} {self.surname}"

    def save(self, *args, **kwargs):
        if not self.avatar:
            self.avatar.save(
                f"avatar_{uuid.uuid4()}.png",
                self._generate_avatar(),
                save=False,
            )
        super().save(*args, **kwargs)

    def _generate_avatar(self):
        colors = [
            (224, 242, 254),
            (220, 252, 231),
            (254, 249, 195),
            (237, 233, 254),
            (255, 237, 213),
            (252, 231, 243),
        ]

        image = Image.new("RGB", (256, 256), random.choice(colors))
        draw = ImageDraw.Draw(image)

        letter = (self.name[:1] or self.email[:1] or "U").upper()

        try:
            font = ImageFont.truetype("arial.ttf", 120)
        except OSError:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), letter, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        position = (
            (256 - text_width) / 2,
            (256 - text_height) / 2 - 10,
        )

        draw.text(position, letter, fill=(31, 41, 55), font=font)

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return ContentFile(buffer.getvalue())
