from django.core.paginator import EmptyPage, PageNotAnInteger
from django.core.paginator import Paginator as DjangoPaginator
from django.db.models import QuerySet
from django.http import HttpRequest


class Paginator:
    def __init__(
        self,
        request: HttpRequest,
        queryset: QuerySet,
        page_size: int = 10,
    ):
        self.request = request
        self.queryset = queryset
        self.page_size = page_size
        if not isinstance(self.page_size, int) or self.page_size <= 0:
            self.page_size = 10
        self.paginator = DjangoPaginator(self.queryset, self.page_size)

    def get_page(self, page_num: int = 1):
        """ """
        try:
            page_obj = self.paginator.page(page_num)
        except PageNotAnInteger:
            page_obj = self.paginator.page(1)
        except EmptyPage:
            page_obj = self.paginator.page(self.paginator.num_pages)

        query_params = self.request.GET.copy()
        next_url = None
        prev_url = None

        if page_obj.has_next():
            query_params["page"] = page_obj.next_page_number()
            next_url = f"{self.request.path}?{query_params.urlencode()}"

        if page_obj.has_previous():
            query_params["page"] = page_obj.previous_page_number()
            next_url = f"{self.request.path}?{query_params.urlencode()}"

        data = page_obj.object_list
        return {
            "count": self.paginator.count,
            "next": next_url,
            "previous": prev_url,
            "page": page_obj.number,
            "page_size": self.page_size,
            "total_pages": self.paginator.num_pages,
            "data": list(data),
        }
