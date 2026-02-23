from django.urls import path
from . import views


app_name = "reconcile"

urlpatterns = [
    path('', views.reconcile_home),
    path('manual-add/', views.reconcile_manual_add, name="manual_add"),
    path('text-add/', views.reconcile_text_add, name="text_add")
]