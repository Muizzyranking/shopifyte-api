from django.contrib import admin
from .models import User, Store

# Register your models here.
models = [User, Store]
for model in models:
    admin.site.register(model)
