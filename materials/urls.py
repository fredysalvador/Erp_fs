from django.urls import path
from . import views

app_name = 'materials'

urlpatterns = [
    path('', views.materials_list, name='materials_list'),
    path('create/', views.material_create, name='material_create'),
    path('bulk-create/', views.material_bulk_create, name='material_bulk_create'),
]
