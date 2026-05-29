import random
import re
import uuid
from io import BytesIO
from urllib.parse import urlparse

from django import forms
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont


PHONE_RE = re.compile(r"^(8\d{10}|\+7\d{10})$")

LOCAL_PHONE_PREFIX = "8"
INTERNATIONAL_PHONE_PREFIX = "+7"
PHONE_LENGTH_WITH_LOCAL_PREFIX = 11
LOCAL_PREFIX_SLICE_INDEX = 1
PHONE_MAX_LENGTH = 12

PROFILE_ABOUT_TEXTAREA_ROWS = 4

GITHUB_HOSTS = {"github.com", "www.github.com"}
ALLOWED_URL_SCHEMES = {"http", "https"}

AVATAR_UPLOAD_EXTENSION = "png"
AVATAR_FILE_FORMAT = "PNG"
AVATAR_IMAGE_MODE = "RGB"
AVATAR_SIZE = 256
AVATAR_FONT_SIZE = 120
AVATAR_DEFAULT_LETTER = "U"
AVATAR_FONT_NAME = "arial.ttf"
AVATAR_TEXT_VERTICAL_OFFSET = 10

AVATAR_TEXT_START_POSITION = 0
AVATAR_LEFT_INDEX = 0
AVATAR_TOP_INDEX = 1
AVATAR_RIGHT_INDEX = 2
AVATAR_BOTTOM_INDEX = 3
CENTER_DIVIDER = 2

AVATAR_TEXT_COLOR = (31, 41, 55)

AVATAR_BACKGROUND_LIGHT_BLUE = (224, 242, 254)
AVATAR_BACKGROUND_LIGHT_GREEN = (220, 252, 231)
AVATAR_BACKGROUND_LIGHT_YELLOW = (254, 249, 195)
AVATAR_BACKGROUND_LIGHT_PURPLE = (237, 233, 254)
AVATAR_BACKGROUND_LIGHT_ORANGE = (255, 237, 213)
AVATAR_BACKGROUND_LIGHT_PINK = (252, 231, 243)

AVATAR_BACKGROUND_COLORS = [
    AVATAR_BACKGROUND_LIGHT_BLUE,
    AVATAR_BACKGROUND_LIGHT_GREEN,
    AVATAR_BACKGROUND_LIGHT_YELLOW,
    AVATAR_BACKGROUND_LIGHT_PURPLE,
    AVATAR_BACKGROUND_LIGHT_ORANGE,
    AVATAR_BACKGROUND_LIGHT_PINK,
]


def normalize_phone(phone):
    phone = (phone or "").strip()

    if (
        phone.startswith(LOCAL_PHONE_PREFIX)
        and len(phone) == PHONE_LENGTH_WITH_LOCAL_PREFIX
    ):
        return INTERNATIONAL_PHONE_PREFIX + phone[LOCAL_PREFIX_SLICE_INDEX:]

    return phone


def validate_phone(phone, user_instance=None):
    from .models import User

    phone = normalize_phone(phone)

    if not phone:
        raise forms.ValidationError("Введите номер телефона.")

    if not PHONE_RE.match(phone):
        raise forms.ValidationError(
            "Телефон должен быть в формате 8XXXXXXXXXX или +7XXXXXXXXXX."
        )

    users = User.objects.filter(phone=phone)

    if user_instance and user_instance.pk:
        users = users.exclude(pk=user_instance.pk)

    if users.exists():
        raise forms.ValidationError("Пользователь с таким телефоном уже существует.")

    return phone


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


def generate_avatar(name, email):
    image = Image.new(
        AVATAR_IMAGE_MODE,
        (AVATAR_SIZE, AVATAR_SIZE),
        random.choice(AVATAR_BACKGROUND_COLORS),
    )
    draw = ImageDraw.Draw(image)

    letter = (name[:LOCAL_PREFIX_SLICE_INDEX] or email[:LOCAL_PREFIX_SLICE_INDEX]
              or AVATAR_DEFAULT_LETTER).upper()

    try:
        font = ImageFont.truetype(AVATAR_FONT_NAME, AVATAR_FONT_SIZE)
    except OSError:
        font = ImageFont.load_default()

    bbox = draw.textbbox(
        (AVATAR_TEXT_START_POSITION, AVATAR_TEXT_START_POSITION),
        letter,
        font=font,
    )
    text_width = bbox[AVATAR_RIGHT_INDEX] - bbox[AVATAR_LEFT_INDEX]
    text_height = bbox[AVATAR_BOTTOM_INDEX] - bbox[AVATAR_TOP_INDEX]

    position = (
        (AVATAR_SIZE - text_width) / CENTER_DIVIDER,
        (AVATAR_SIZE - text_height) / CENTER_DIVIDER - AVATAR_TEXT_VERTICAL_OFFSET,
    )

    draw.text(position, letter, fill=AVATAR_TEXT_COLOR, font=font)

    buffer = BytesIO()
    image.save(buffer, format=AVATAR_FILE_FORMAT)
    return ContentFile(buffer.getvalue())


def generate_avatar_filename():
    return f"avatar_{uuid.uuid4()}.{AVATAR_UPLOAD_EXTENSION}"