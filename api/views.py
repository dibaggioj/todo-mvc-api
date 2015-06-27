import json
from django.forms import model_to_dict
from django.http import HttpResponse
from django.views.generic import View

from api.models import Todo

RESPONSE_SCHEMA = {
    'data': {},
    'code': "OK",
    'status': 200,
    'errors': [],
}

class TodoService(View):
    def get(self, request, pk=None):
        response = get_todos(pk)
        return HttpResponse(json.dumps(response), content_type="application/json")

    def post(self, request, pk=None):
        pass


def get_todos(pk=None):
    def serialize_todo(obj):
        todo_dct = model_to_dict(obj, fields=['id', 'title', 'isCompleted', 'dateTime'])
        todo_dct['isCompleted'] = getattr(obj, 'is_completed')
        todo_dct['dateTime'] = str(getattr(obj, 'date_time'))

        return todo_dct

    response = RESPONSE_SCHEMA
    if pk is not None:
        todos = Todo.objects.filter(id=pk)
    else:
        todos = Todo.objects.all()

    todo_dct = map(serialize_todo, todos)
    response['data'] = todo_dct

    return response
