from django.db import models
from django.utils import timezone


class Todo(models.Model):
    title = models.CharField(max_length=200, blank=True, default="")
    is_completed = models.BooleanField(blank=True, default=False)
    date_time = models.DateTimeField(default=timezone.now)
