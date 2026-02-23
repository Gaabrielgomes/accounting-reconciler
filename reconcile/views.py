from django.shortcuts import render
from .forms import ReconcileForm, ManualAddForm, TextAddForm

# Create your views here.
def reconcile_home(request):
    variables = {
        "form": ReconcileForm()
    }
    return render(request, 'pages/reconcile_home.html', variables)


def reconcile_manual_add(request):
    form = ManualAddForm()

    if request.method == "POST":
        form = ManualAddForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            document = form.cleaned_data["document"]

            print(name, document)  # depois você salva no banco

    return render(request, "pages/reconcile_manual_add.html", {"form": form})


def reconcile_text_add(request):
    if request.method == "POST":
        form = TextAddForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.cleaned_data["file"]

            # Exemplo: ler conteúdo do arquivo
            content = uploaded_file.read().decode("utf-8")
            print(content)

    else:
        form = TextAddForm()

    return render(request, "pages/reconcile_text_add.html", {"form": form})