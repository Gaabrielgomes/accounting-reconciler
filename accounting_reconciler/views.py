from django.http import HttpResponse


def index_view(request):
    return HttpResponse("<h1>Welcome</h1>")