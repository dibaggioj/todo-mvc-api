import json
import simplejson

from django.forms import model_to_dict
from django.http import HttpResponse
from django.views.generic import View
from django.conf import settings

from api.models import Todo

base_url = getattr(settings, "BASE_URL", None)

PATH_TODO = '/api/v1/todos/'

RESPONSE_SCHEMA = {
    'jsonapi': {
        'version': "1.0"
    },
    'meta': {
        'name': 'Todo MVC API',
        'year': '2015',
        'authors': [
            "John DiBaggio"
        ]
    },
    'links': {},
    'data': {},
    # 'code': "OK",
    # 'status': 200,
    'errors': [],
}

class TodoService(View):
    def get(self, request, pk=None):
        response = get_todos(pk)
        return HttpResponse(json.dumps(response), content_type="application/json")

    def post(self, request, pk=None):
        print(request)
        print(request.POST)
        print(dict(request.POST.iterlists()))
        post_json = request.POST.get('data', "")
        print(post_json)
        dct = json.loads(post_json)

        print(dct)

        response = update_or_create_todo(dct)

        return HttpResponse(json.dumps(response), content_type="application/json")


def get_todos(pk=None):
    def serialize_todo(obj):
        todo_dct = {
            'type': 'todos',
            'id': getattr(obj, 'id')
        }
        attr_dct = model_to_dict(obj, fields=['title', 'is_completed', 'date_time'])
        attr_dct['date_time'] = str(getattr(obj, 'date_time'))
        todo_dct['attributes'] = attr_dct
        # todo_dct = model_to_dict(obj, fields=['id', 'title', 'is_completed', 'date_time'])
        # todo_dct['date_time'] = str(getattr(obj, 'date_time'))
        # todo_dct['type'] = "todos"
        return todo_dct

    response = RESPONSE_SCHEMA
    if pk is not None:
        todos = Todo.objects.filter(id=pk)
        response['links']['self'] = base_url + PATH_TODO + str(pk)
        response['links']['next'] = base_url + PATH_TODO + str(int(pk) + 1)
        response['links']['last'] = base_url + PATH_TODO + str(getattr(Todo.objects.latest('id'), 'id'))
    else:
        todos = Todo.objects.all()

    todo_dct = map(serialize_todo, todos)

    response['data'] = todo_dct

    # TODO: check for success
    response.pop("errors", None)

    return response


def update_or_create_todo(json_resp):
    response = RESPONSE_SCHEMA
    if json_resp.get('id'):
        response = update_todo(json_resp, response)
    else:
        response = create_todo(json_resp, response)
    return response


def update_todo(json_resp, response):
    todo_id = json_resp.get('id')
    try:
        updated_todo = Todo.objects.get(id=todo_id)
    except Todo.DoesNotExist:
        # response['status'] = 404
        # response['code'] = "Failed"
        response.pop('data', None)
        reason = "Todo with id: %d does not exist." % todo_id
        error_obj = build_error_obj(status=404, code="Failed", title="Location does not exist", detail=reason)
        response['errors'].append(error_obj)
        return response

    # TODO: handle delete todo

    for key in json_resp:
        if hasattr(updated_todo, key):
            response['data'][key] = json_resp[key]
            setattr(updated_todo, key, json_resp[key])
            try:
                updated_todo.save()
            except ValueError:
                # response['status'] = 400
                reason = "Cannot set %s as: %s" % (key, json_resp[key])
                error_obj = build_error_obj(status=404, code="Failed", title="Invalid value", detail=reason)
                response['errors'].append(error_obj)
        else:
            # response['status'] = 400
            reason = "Todo does not have attribute: %s" % key
            error_obj = build_error_obj(status=404, code="Failed", title="Invalid attribute", detail=reason)
            response['errors'].append(error_obj)

        success = True
        try:
            updated_todo.dave()
        except:
            success = False
            # response['status'] = 500
            # response['code'] = "Failed"
            reason = "Unable to update todo"
            error_obj = build_error_obj(status=404, code="Failed", title="Unable to update", detail=reason)
            response['errors'].append(error_obj)

        if success:
            # response['status'] = 200
            response.pop("errors", None)
        else:
            response.pop('data', None)


def create_todo(json_resp, response):
    valid = True
    success = True
    new_todo = Todo()
    for key in json_resp:
        if hasattr(new_todo, key):
            setattr(new_todo, key, json_resp[key])
        else:
            valid = False
            # response['status'] = 400
            reason = "Todo does not have attribute: %s" % key
            error_obj = build_error_obj(status=404, code="Failed", title="Invalid attribute", detail=reason)
            response['errors'].append(error_obj)

    if valid:
        valid, response = validate_new_todo(new_todo, response)

    if valid:
        try:
            new_todo.save()
        except:
            success = False
            reason = "Unable to create todo"
            error_obj = build_error_obj(status=404, code="Failed", title="Unable to create", detail=reason)
            response['errors'].append(error_obj)

        if success:
            # response['status'] = 201
            for key in json_resp:
                response['data'][key] = json_resp[key]
            response.pop("errors", None)
        else:
            # response['status'] = 500
            response['code'] = "Failed"
            response.pop('data', None)
    else:
        # response['status'] = 400
        response['code'] = "Failed"
        response.pop("data", None)

    return response


def validate_new_todo(todo, response):
    valid = True
    if not hasattr(todo, 'title'):
        # response['status'] = 400
        response['code'] = "Failed"
        valid = False

    return valid, response


def build_error_obj(identifier=None, href=None, status=None, code=None, title=None, detail=None, links=None,
                       paths=None):
    error_obj = dict()
    if identifier is not None:
        error_obj['id'] = identifier
    if href is not None:
        error_obj['href'] = href
    if status is not None:
        error_obj['status'] = status
    if code is not None:
        error_obj['code'] = code
    if title is not None:
        error_obj['title'] = title
    if detail is not None:
        error_obj['detail'] = detail
    if links is not None:
        error_obj['links'] = links
    if paths is not None:
        error_obj['paths'] = paths
    return error_obj