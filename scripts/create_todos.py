from django.contrib.auth.models import User
from api.models import Todo

# usr = User.objects.get(id=1)

todo_1 = Todo(title="First things first")
todo_1.save()

todo_2 = Todo(title="Finish first thing", is_complete=True)
todo_2.save()

todo_3 = Todo(title="Do other things")
todo_3.save()