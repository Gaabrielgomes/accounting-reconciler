from django.urls import path
from . import views


app_name = "reconcile"

urlpatterns = [
    path('', views.reconcile_home),
    path('add/', views.reconcile_add, name="add")
]