from django.core.paginator import Paginator


PAGE_QUERY_PARAM = "page"
QUERY_PARAMS_SEPARATOR = "&"
EMPTY_STRING = ""


def get_query_prefix(request):
    params = request.GET.copy()
    params.pop(PAGE_QUERY_PARAM, None)

    if params:
        return params.urlencode() + QUERY_PARAMS_SEPARATOR

    return EMPTY_STRING


def paginate_queryset(request, queryset, per_page):
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(request.GET.get(PAGE_QUERY_PARAM))