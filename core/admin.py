from django.contrib import admin
from django.apps import apps


def register_all_models(app_name):
    app = apps.get_app_config(app_name)
    for model in app.get_models():
        try:
            admin.site.register(model)
        except admin.sites.AlreadyRegistered:
            pass
