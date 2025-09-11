from typing import Union
from django.apps import apps
from django.contrib import admin
from ninja import Schema


def register_all_models(app_name):
    app = apps.get_app_config(app_name)
    for model in app.get_models():
        try:
            admin.site.register(model)
        except admin.sites.AlreadyRegistered:
            pass


def response_message(msg):
    return {"message": str(msg)}


def response_with_data(msg, data):
    return {"message": str(msg), "data": data}


def error_message(msg):
    return response_message(f"Error: {str(msg)}")


def get_seconds(hours: float = 0, minutes: float = 0, seconds: float = 0) -> int:
    return int((hours * 3600) + (minutes * 60) + seconds)


def schema_to_dict(schema: Union[Schema, dict, None]) -> dict:
    if not schema:
        return {}
    elif hasattr(schema, "dict"):
        return schema.dict(exclude_unset=True)
    elif isinstance(schema, dict):
        return schema
    else:
        return {}
