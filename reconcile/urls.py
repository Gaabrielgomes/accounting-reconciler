from django.urls import path
from . import views


app_name = "reconcile"

urlpatterns = [
    path('', views.reconcile_home, name="reconcile_home"),
    path('process/', views.process_file, name="reconcile_process_file"),
    path('results/', views.results, name="reconcile_results")
]