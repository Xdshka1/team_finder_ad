from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import EditProfileForm, LoginForm, RegisterForm, UserPasswordChangeForm
from .models import User


USERS_PER_PAGE = 12


def _query_prefix(request):
    params = request.GET.copy()
    params.pop("page", None)

    if params:
        return params.urlencode() + "&"

    return ""


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("/projects/list/")
    else:
        form = RegisterForm()

    return render(request, "users/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)

        if form.is_valid():
            login(request, form.cleaned_data["user"])
            return redirect("/projects/list/")
    else:
        form = LoginForm()

    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("/projects/list/")


def participants_list(request):
    active_filter = request.GET.get("filter") if request.user.is_authenticated else None
    participants = User.objects.filter(is_active=True).order_by("-id")

    if active_filter == "owners-of-favorite-projects":
        participants = participants.filter(
            owned_projects__in=request.user.favorites.all()
        )

    elif active_filter == "owners-of-participating-projects":
        participants = participants.filter(
            owned_projects__in=request.user.participated_projects.all()
        )

    elif active_filter == "interested-in-my-projects":
        participants = participants.filter(
            favorites__owner=request.user
        )

    elif active_filter == "participants-of-my-projects":
        participants = participants.filter(
            participated_projects__owner=request.user
        ).exclude(pk=request.user.pk)

    elif active_filter:
        active_filter = None

    participants = participants.distinct()

    paginator = Paginator(participants, USERS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "users/participants.html",
        {
            "participants": participants,
            "page_obj": page_obj,
            "active_filter": active_filter,
            "query_prefix": _query_prefix(request),
        },
    )


def user_detail(request, pk):
    user = get_object_or_404(
        User.objects.prefetch_related("owned_projects", "participated_projects"),
        pk=pk,
        is_active=True,
    )

    return render(request, "users/user-details.html", {"user": user})


@login_required(login_url="/users/login/")
def edit_profile(request):
    if request.method == "POST":
        form = EditProfileForm(request.POST, request.FILES, instance=request.user)

        if form.is_valid():
            form.save()
            return redirect(f"/users/{request.user.pk}/")
    else:
        form = EditProfileForm(instance=request.user)

    return render(
        request,
        "users/edit_profile.html",
        {
            "form": form,
            "user": request.user,
        },
    )


@login_required(login_url="/users/login/")
def change_password(request):
    if request.method == "POST":
        form = UserPasswordChangeForm(request.user, request.POST)

        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect(f"/users/{request.user.pk}/")
    else:
        form = UserPasswordChangeForm(request.user)

    return render(request, "users/change_password.html", {"form": form})
