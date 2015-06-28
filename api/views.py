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
        post_json = request.POST.get("json", "")
        dct = json.loads(post_json)

        response = update_or_create_todo(dct)

        return HttpResponse(json.dumps(response), content_type="application/json")


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
        response['status'] = 404
        response['code'] = "Failed"
        response.pop('data', None)
        reason = "Todo with id: %d does not exist." % todo_id
        error_obj = build_error_obj(status=404, code="Failed", title="Location does not exist", detail=reason)
        response['errors'].append(error_obj)
        return response

    for key in json_resp:
        if hasattr(updated_todo, key):
            response['data'][key] = json_resp[key]
            setattr(updated_todo, key, json_resp[key])
            try:
                updated_todo.save()
            except ValueError:
                response['status'] = 400
                reason = "Cannot set %s as: %s" % (key, json_resp[key])
                error_obj = build_error_obj(status=404, code="Failed", title="Invalid value", detail=reason)
                response['errors'].append(error_obj)
        else:
            response['status'] = 400
            reason = "Todo does not have attribute: %s" % key
            error_obj = build_error_obj(status=404, code="Failed", title="Invalid attribute", detail=reason)
            response['errors'].append(error_obj)

        success = True
        try:
            updated_todo.dave()
        except:
            success = False
            response['status'] = 500
            response['code'] = "Failed"
            reason = "Unable to update todo"
            error_obj = build_error_obj(status=404, code="Failed", title="Unable to update", detail=reason)
            response['errors'].append(error_obj)

        if success:
            response['status'] = 200
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
            response['status'] = 400
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
            response['status'] = 201
            for key in json_resp:
                response['data'][key] = json_resp[key]
        else:
            response['status'] = 500
            response['code'] = "Failed"
            response.pop('data', None)
    else:
        response['status'] = 400
        response['code'] = "Failed"
        response.pop("data", None)

    return response


def validate_new_todo(todo, response):
    valid = True
    if not hasattr(todo, 'title'):
        response['status'] = 400
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