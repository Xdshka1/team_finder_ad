from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import get_object_or_404, redirect, render

from team_finder.utils import get_query_prefix, paginate_queryset

from .forms import EditProfileForm, LoginForm, RegisterForm
from .models import User


USERS_PER_PAGE = 12

FILTER_QUERY_PARAM = "filter"
USER_ORDERING_BY_NEWEST = "-id"

FILTER_OWNERS_OF_FAVORITE_PROJECTS = "owners-of-favorite-projects"
FILTER_OWNERS_OF_PARTICIPATING_PROJECTS = "owners-of-participating-projects"
FILTER_INTERESTED_IN_MY_PROJECTS = "interested-in-my-projects"
FILTER_PARTICIPANTS_OF_MY_PROJECTS = "participants-of-my-projects"

USER_DETAIL_TEMPLATE = "users/user-details.html"
USERS_LIST_TEMPLATE = "users/participants.html"
REGISTER_TEMPLATE = "users/register.html"
LOGIN_TEMPLATE = "users/login.html"
EDIT_PROFILE_TEMPLATE = "users/edit_profile.html"
CHANGE_PASSWORD_TEMPLATE = "users/change_password.html"


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("projects:list")
    else:
        form = RegisterForm()

    return render(request, REGISTER_TEMPLATE, {"form": form})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)

        if form.is_valid():
            login(request, form.cleaned_data["user"])
            return redirect("projects:list")
    else:
        form = LoginForm()

    return render(request, LOGIN_TEMPLATE, {"form": form})


def logout_view(request):
    logout(request)
    return redirect("projects:list")


def participants_list(request):
    active_filter = _get_active_filter(request)
    participants = User.objects.filter(is_active=True).order_by(
        USER_ORDERING_BY_NEWEST
    )

    if active_filter == FILTER_OWNERS_OF_FAVORITE_PROJECTS:
        participants = participants.filter(
            owned_projects__in=request.user.favorites.all()
        )

    elif active_filter == FILTER_OWNERS_OF_PARTICIPATING_PROJECTS:
        participants = participants.filter(
            owned_projects__in=request.user.participated_projects.all()
        )

    elif active_filter == FILTER_INTERESTED_IN_MY_PROJECTS:
        participants = participants.filter(
            favorites__owner=request.user
        )

    elif active_filter == FILTER_PARTICIPANTS_OF_MY_PROJECTS:
        participants = participants.filter(
            participated_projects__owner=request.user
        ).exclude(pk=request.user.pk)

    elif active_filter:
        active_filter = None

    participants = participants.distinct()
    page_obj = paginate_queryset(request, participants, USERS_PER_PAGE)

    return render(
        request,
        USERS_LIST_TEMPLATE,
        {
            "participants": participants,
            "page_obj": page_obj,
            "active_filter": active_filter,
            "query_prefix": get_query_prefix(request),
        },
    )


def user_detail(request, pk):
    user = get_object_or_404(
        User.objects.prefetch_related("owned_projects", "participated_projects"),
        pk=pk,
        is_active=True,
    )

    return render(request, USER_DETAIL_TEMPLATE, {"user": user})


@login_required(login_url="users:login")
def edit_profile(request):
    if request.method == "POST":
        form = EditProfileForm(
            request.POST,
            request.FILES,
            instance=request.user,
        )

        if form.is_valid():
            form.save()
            return redirect("users:detail", pk=request.user.pk)
    else:
        form = EditProfileForm(instance=request.user)

    return render(
        request,
        EDIT_PROFILE_TEMPLATE,
        {
            "form": form,
            "user": request.user,
        },
    )


@login_required(login_url="users:login")
def change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)

        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect("users:detail", pk=request.user.pk)
    else:
        form = PasswordChangeForm(request.user)

    return render(request, CHANGE_PASSWORD_TEMPLATE, {"form": form})


def _get_active_filter(request):
    if request.user.is_authenticated:
        return request.GET.get(FILTER_QUERY_PARAM)

    return None