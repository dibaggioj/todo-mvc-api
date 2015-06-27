from django.contrib import admin

# Register your models here.
from api.models import Todo

admin.site.register(Todo)
