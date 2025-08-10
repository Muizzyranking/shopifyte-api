from django.contrib import admin
from django.apps import apps

app = apps.get_app_config("users")

# automatically register all models in the app
for models in app.get_models():
    try:
        admin.site.register(models)
    except Exception:
        pass
