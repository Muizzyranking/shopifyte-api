from django.contrib import admin
from .models import User, Vendor

# Register your models here.
models = [User, Vendor]
for model in models:
    admin.site.register(model)
