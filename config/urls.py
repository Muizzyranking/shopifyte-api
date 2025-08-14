from django.conf import settings
from django.contrib import admin
from django.urls import path
from core.api import api
from core.exception_handler import APIExceptionHandler

api_exception_handler = APIExceptionHandler(api, debug=settings.DEBUG)


def custom_page_not_found_view(request, _):
    return api_exception_handler.create_error_response(
        request=request, message="Resource not found", status=404
    )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]
handler404 = custom_page_not_found_view
