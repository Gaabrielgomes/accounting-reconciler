from django.shortcuts import render
from .forms import ReconcileForm

# Create your views here.
def reconcile_home(request):
    return render(request, 'pages/reconcile_home.html', {'form': ReconcileForm()})


def process_file(request):
    if request.method == 'POST':
        form = ReconcileForm(request.POST, request.FILES)

        if form.is_valid():
            uploaded_file = form.cleaned_data['file']
            return render(
                request,
                  'pages/process_file.html',
                    {'file_name': uploaded_file.name}
            )
    else:
        return render(request, 'pages/reconcile_home.html', {'form': ReconcileForm()})