from django.shortcuts import render
from .forms import ReconcileForm

# Create your views here.
def reconcile_home(request):
    variables = {
        "form": ReconcileForm()
    }
    return render(request, 'pages/reconcile_home.html', variables)