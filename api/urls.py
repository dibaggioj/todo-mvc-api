from django.conf.urls import patterns, url
from django.contrib import admin
from django.views.decorators.csrf import csrf_exempt


from views import TodoService


admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^todos(\/(?P<pk>\d+))?', csrf_exempt(TodoService.as_view()), name='todo_service'),
)
