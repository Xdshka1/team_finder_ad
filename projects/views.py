from http import HTTPStatus

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from team_finder.utils import get_query_prefix, paginate_queryset

from .forms import ProjectForm
from .models import Project


PROJECTS_PER_PAGE = 12

PROJECT_ORDERING_BY_NEWEST = "-created_at"

PROJECT_LIST_TEMPLATE = "projects/project_list.html"
FAVORITE_PROJECTS_TEMPLATE = "projects/favorite_projects.html"
PROJECT_DETAIL_TEMPLATE = "projects/project-details.html"
CREATE_PROJECT_TEMPLATE = "projects/create-project.html"

JSON_STATUS_KEY = "status"
JSON_STATUS_OK = "ok"
JSON_STATUS_ERROR = "error"

JSON_DETAIL_KEY = "detail"
JSON_LOGIN_REQUIRED = "login_required"
JSON_FORBIDDEN = "forbidden"
JSON_NOT_FOUND = "not_found"
JSON_ALREADY_CLOSED = "already_closed"
JSON_OWNER_IS_ALREADY_PARTICIPANT = "owner_is_already_participant"

JSON_FAVORITED_KEY = "favorited"
JSON_PARTICIPANT_KEY = "participant"
JSON_PROJECT_STATUS_KEY = "project_status"

PROJECT_STATUS_UPDATE_FIELDS = ["status"]


def project_list(request):
    projects = (
        Project.objects
        .select_related("owner")
        .prefetch_related("participants")
        .order_by(PROJECT_ORDERING_BY_NEWEST)
    )
    page_obj = paginate_queryset(request, projects, PROJECTS_PER_PAGE)

    return render(
        request,
        PROJECT_LIST_TEMPLATE,
        {
            "projects": projects,
            "page_obj": page_obj,
            "query_prefix": get_query_prefix(request),
        },
    )


@login_required(login_url="users:login")
def favorite_projects(request):
    projects = (
        request.user.favorites
        .select_related("owner")
        .prefetch_related("participants")
        .order_by(PROJECT_ORDERING_BY_NEWEST)
    )
    page_obj = paginate_queryset(request, projects, PROJECTS_PER_PAGE)

    return render(
        request,
        FAVORITE_PROJECTS_TEMPLATE,
        {
            "projects": projects,
            "page_obj": page_obj,
            "query_prefix": get_query_prefix(request),
        },
    )


def project_detail(request, pk):
    project = get_object_or_404(
        Project.objects.select_related("owner").prefetch_related("participants"),
        pk=pk,
    )

    return render(request, PROJECT_DETAIL_TEMPLATE, {"project": project})


@login_required(login_url="users:login")
def create_project(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)

        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            project.participants.add(request.user)
            return redirect("projects:detail", pk=project.pk)
    else:
        form = ProjectForm(initial={"status": Project.STATUS_OPEN})

    return render(
        request,
        CREATE_PROJECT_TEMPLATE,
        {
            "form": form,
            "is_edit": False,
        },
    )


@login_required(login_url="users:login")
def edit_project(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if request.user != project.owner and not request.user.is_staff:
        return redirect("projects:detail", pk=project.pk)

    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)

        if form.is_valid():
            project = form.save()
            return redirect("projects:detail", pk=project.pk)
    else:
        form = ProjectForm(instance=project)

    return render(
        request,
        CREATE_PROJECT_TEMPLATE,
        {
            "form": form,
            "is_edit": True,
        },
    )


@require_POST
def toggle_favorite(request, pk):
    if not request.user.is_authenticated:
        return _json_error(
            JSON_LOGIN_REQUIRED,
            HTTPStatus.UNAUTHORIZED,
        )

    project = _get_project_for_json_response(pk)

    if project is None:
        return _json_error(
            JSON_NOT_FOUND,
            HTTPStatus.NOT_FOUND,
        )

    is_favorited = request.user.favorites.filter(pk=project.pk).exists()

    if is_favorited:
        request.user.favorites.remove(project)
    else:
        request.user.favorites.add(project)

    return JsonResponse(
        {
            JSON_STATUS_KEY: JSON_STATUS_OK,
            JSON_FAVORITED_KEY: not is_favorited,
        }
    )


@require_POST
def complete_project(request, pk):
    if not request.user.is_authenticated:
        return _json_error(
            JSON_LOGIN_REQUIRED,
            HTTPStatus.UNAUTHORIZED,
        )

    project = _get_project_for_json_response(pk)

    if project is None:
        return _json_error(
            JSON_NOT_FOUND,
            HTTPStatus.NOT_FOUND,
        )

    if request.user != project.owner and not request.user.is_staff:
        return _json_error(
            JSON_FORBIDDEN,
            HTTPStatus.FORBIDDEN,
        )

    if project.status != Project.STATUS_OPEN:
        return _json_error(
            JSON_ALREADY_CLOSED,
            HTTPStatus.BAD_REQUEST,
        )

    project.status = Project.STATUS_CLOSED
    project.save(update_fields=PROJECT_STATUS_UPDATE_FIELDS)

    return JsonResponse(
        {
            JSON_STATUS_KEY: JSON_STATUS_OK,
            JSON_PROJECT_STATUS_KEY: Project.STATUS_CLOSED,
        }
    )


@require_POST
def toggle_participate(request, pk):
    if not request.user.is_authenticated:
        return _json_error(
            JSON_LOGIN_REQUIRED,
            HTTPStatus.UNAUTHORIZED,
        )

    project = _get_project_for_json_response(pk)

    if project is None:
        return _json_error(
            JSON_NOT_FOUND,
            HTTPStatus.NOT_FOUND,
        )

    if request.user == project.owner:
        return _json_error(
            JSON_OWNER_IS_ALREADY_PARTICIPANT,
            HTTPStatus.FORBIDDEN,
        )

    is_participant = project.participants.filter(pk=request.user.pk).exists()

    if is_participant:
        project.participants.remove(request.user)
    else:
        project.participants.add(request.user)

    return JsonResponse(
        {
            JSON_STATUS_KEY: JSON_STATUS_OK,
            JSON_PARTICIPANT_KEY: not is_participant,
        }
    )


def _get_project_for_json_response(pk):
    return Project.objects.filter(pk=pk).first()


def _json_error(detail, status):
    return JsonResponse(
        {
            JSON_STATUS_KEY: JSON_STATUS_ERROR,
            JSON_DETAIL_KEY: detail,
        },
        status=status,
    )