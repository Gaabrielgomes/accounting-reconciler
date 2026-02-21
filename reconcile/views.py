from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def reconcile_home(request):
    variables = {
        "name":"name"
    }
    return render(request, 'reconcile/home.html', variables)

def reconcile_add(request):
    return HttpResponse('Reconcile add')