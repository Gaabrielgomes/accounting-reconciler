from django.urls import path
from . import views

app_name = "reconcile"

urlpatterns = [
    path('', views.reconcile_home, name="reconcile_home"),
    path('process/', views.reconcile_process, name="reconcile_process"),
    path('filter/', views.filter_by_period, name="filter_by_period"),
    path('export/', views.export_csv, name='export_csv'),
    path('process-again/', views.process_again, name='process_again')
]