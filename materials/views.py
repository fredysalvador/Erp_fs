from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Material
from .forms import MaterialForm
from django.core.paginator import Paginator
from django.db import models
from users.models import UserRole


@login_required
def material_list(request):

    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(max_permission=models.Max('role_materials'))['max_permission'] or 0

    if max_permission == 0:
        return redirect('dashboard')
    
    materials_list = Material.objects.all()

    id_material = request.Get.get('id_material')
    name = request.Get.get('name')
    material_type = request.Get.get('material_type')
    status = request.Get.get('status')

    if id_material:
        materials_list = materials_list.filter(id_material__icontains=id_material)
    if name:
        materials_list = materials_list.filter(name__icontains=name)
    if material_type:
        materials_list = materials_list.filter(material_type__icontains=material_type)
    if status is not None and status != '':
        materials_list = materials_list.filter(status=status)
    

    paginator = Paginator(materials_list,10)
    page_number = request.Get.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'materials/materials_list.html',{'page_obj':page_obj})

@login_required
def material_create(request):
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(max_permission=models.Max('role_materials'))['max_permission'] or 0
    

    if max_permission == 1:
        return redirect('materials')
    if max_permission == 0:
        return redirect('dashboard')
    

    if request.method == 'POST':
        form = MaterialForm(request.POST)
        if form.is_valid():
            material = form.save(commit=False)
            material.created_by= request.user
            material.save()

            return redirect('materials:material_create')
        else:
            form = MaterialForm()

        return render(request, 'materials/material_form.html',{'form':form})
    