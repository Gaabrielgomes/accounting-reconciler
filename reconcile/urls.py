from django.urls import path
from . import views


app_name = "reconcile"

urlpatterns = [
    path('', views.reconcile_home, name="reconcile_home"),
    path('process/', views.reconcile_process, name="reconcile_process"),
    path('results/', views.reconcile_results, name="reconcile_results")
]