from django.urls import path
from . import views

app_name = 'materials'

urlpatterns = [
    path('', views.materials_list, name='material_list'),
    path('create/', views.material_create, name='material_create'),
    path('<int:pk>/edit/', views.material_edit, name="material_edit"),
    path('<int:pk>/delete/', views.material_delete, name="material_delete"),
    path('bulk-create/', views.material_bulk_create, name='material_bulk_create'),
    path('bulk/template/', views.download_template_materials, name='download_template_materials'),
]
