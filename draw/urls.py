"""Define URL patterns for draw app."""
from django.urls import path

from . import views

app_name = 'draw'
urlpatterns = [
    path('', views.index, name='index'),
    path('get_departs', views.get_departments, name='get_departs'),
    path('get_sz', views.get_sz, name='get_sz'),
    path('tasks/', views.tasks, name='tasks'),
]
