from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ProjectForm
from .models import Project


PROJECTS_PER_PAGE = 12


def _query_prefix(request):
    params = request.GET.copy()
    params.pop("page", None)

    if params:
        return params.urlencode() + "&"

    return ""


def project_list(request):
    projects = (
        Project.objects
        .select_related("owner")
        .prefetch_related("participants")
        .order_by("-created_at")
    )

    paginator = Paginator(projects, PROJECTS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "projects/project_list.html",
        {
            "projects": projects,
            "page_obj": page_obj,
            "query_prefix": _query_prefix(request),
        },
    )


@login_required(login_url="/users/login/")
def favorite_projects(request):
    projects = (
        request.user.favorites
        .select_related("owner")
        .prefetch_related("participants")
        .order_by("-created_at")
    )

    return render(
        request,
        "projects/favorite_projects.html",
        {
            "projects": projects,
        },
    )


def project_detail(request, pk):
    project = get_object_or_404(
        Project.objects.select_related("owner").prefetch_related("participants"),
        pk=pk,
    )

    return render(request, "projects/project-details.html", {"project": project})


@login_required(login_url="/users/login/")
def create_project(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)

        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            project.participants.add(request.user)
            return redirect(f"/projects/{project.pk}/")
    else:
        form = ProjectForm(initial={"status": Project.STATUS_OPEN})

    return render(
        request,
        "projects/create-project.html",
        {
            "form": form,
            "is_edit": False,
        },
    )


@login_required(login_url="/users/login/")
def edit_project(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if request.user != project.owner and not request.user.is_staff:
        return redirect(f"/projects/{project.pk}/")

    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)

        if form.is_valid():
            project = form.save()
            return redirect(f"/projects/{project.pk}/")
    else:
        form = ProjectForm(instance=project)

    return render(
        request,
        "projects/create-project.html",
        {
            "form": form,
            "is_edit": True,
        },
    )


@require_POST
def toggle_favorite(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse(
            {
                "status": "error",
                "detail": "login_required",
            },
            status=401,
        )

    project = get_object_or_404(Project, pk=pk)

    if request.user.favorites.filter(pk=project.pk).exists():
        request.user.favorites.remove(project)
        favorited = False
    else:
        request.user.favorites.add(project)
        favorited = True

    return JsonResponse(
        {
            "status": "ok",
            "favorited": favorited,
        }
    )


@require_POST
def complete_project(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse(
            {
                "status": "error",
                "detail": "login_required",
            },
            status=401,
        )

    project = get_object_or_404(Project, pk=pk)

    if request.user != project.owner and not request.user.is_staff:
        return JsonResponse(
            {
                "status": "error",
                "detail": "forbidden",
            },
            status=403,
        )

    if project.status != Project.STATUS_OPEN:
        return JsonResponse(
            {
                "status": "error",
                "detail": "already_closed",
            },
            status=400,
        )

    project.status = Project.STATUS_CLOSED
    project.save(update_fields=["status"])

    return JsonResponse(
        {
            "status": "ok",
            "project_status": Project.STATUS_CLOSED,
        }
    )


@require_POST
def toggle_participate(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse(
            {
                "status": "error",
                "detail": "login_required",
            },
            status=401,
        )

    project = get_object_or_404(Project, pk=pk)

    if request.user == project.owner:
        return JsonResponse(
            {
                "status": "error",
                "detail": "owner_is_already_participant",
            },
            status=403,
        )

    if project.participants.filter(pk=request.user.pk).exists():
        project.participants.remove(request.user)
        participant = False
    else:
        project.participants.add(request.user)
        participant = True

    return JsonResponse(
        {
            "status": "ok",
            "participant": participant,
        }
    )
