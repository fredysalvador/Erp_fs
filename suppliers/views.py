from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Supplier
from .forms import SupplierForm
from django.core.paginator import Paginator
from django.http import HttpResponse
import csv
from django.db import models
from users.models import UserRole


@login_required
def suppliers_list(request):
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(max_permission=models.Max('role__suppliers'))['max_permission'] or 0

    if max_permission == 0:
        return redirect('dashboard')
    
    suppliers_list = Supplier.objects.all()

    id_supplier = request.GET.get('id_supplier')
    name = request.GET.get('name')
    country = request.GET.get('country')
    status = request.GET.get('status')

    if id_supplier:
       suppliers_list = suppliers_list.filter(id_supplier__icontains=id_supplier)
    if name:
       suppliers_list = suppliers_list.filter(name__icontains=name)
    if country:
       suppliers_list = suppliers_list.filter(country__icontains=country)
    if status:
       suppliers_list = suppliers_list.filter(status=status)

    if request.GET.get('export')  == 'csv':
       response = HttpResponse(content_type='text/csv')
       response['Content-Disposition'] = 'attachment; filename="suppliers.csv"'

       response.write('\ufeff'.encode('utf-8'))
       writer = csv.writer(response, delimiter=';')

       writer.writerow(['ID supplier','Legal Name','Name','Tax ID','Country','State/Province','City'
                        ,'Address','Zip Code','Phone','Email','Contact name','Contact role','Category',
                        'Payment terms','Currency','Payment method','Bank account','Status',
                        'Created_by','Created At','Updated At'])
       
       for supplier in suppliers_list:
           writer.writerow([
               supplier.id_supplier,
               supplier.name,
               supplier.legal_name,
               supplier.tax_id,
               supplier.country,
               supplier.state_province,
               supplier.city,
               supplier.address,
               supplier.zip_code,
               supplier.phone,
               supplier.email,
               supplier.contact_name,
               supplier.contact_role,
               supplier.category,
               supplier.payment_terms,
               supplier.currency,
               supplier.payment_method,
               supplier.bank_account,
               supplier.status,
               supplier.created_by.username if supplier.created_by else 'N/A',
               supplier.created_at.strftime('%Y-%m-%d %H:%M:%S'),
               supplier.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            ])
       return response

    paginator = Paginator(suppliers_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'suppliers/suppliers_list.html', {'page_obj': page_obj})


@login_required
def supplier_create(request):
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(max_permission=models.Max('role__suppliers'))['max_permission'] or 0
    
    if max_permission in [0, 1]:
        # redirige según permiso
        return redirect('dashboard' if max_permission == 0 else 'suppliers')

    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save(commit=False)
            supplier.created_by = request.user
            supplier.save()
            return redirect('suppliers:supplier_create')
    else:
        form = SupplierForm()

    return render(request, 'suppliers/supplier_form.html', {'form': form})

@login_required
def supplier_edit(request,pk):
    supplier = get_object_or_404(Supplier,pk=pk)

    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(max_permission=models.Max('role__suppliers'))['max_permission'] or 0
    
    if max_permission == 1:
        return redirect('suppliers')
    if max_permission == 0:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            return redirect('suppliers:suppliers_list')
    else:
        form = SupplierForm(instance=supplier)
        
    context = {
        'form': form,
        'supplier': supplier,
    }

    return render(request, 'suppliers/supplier_form.html', context)

@login_required
def supplier_delete(request,pk):

    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(max_permission=models.Max('role__suppliers'))['max_permission'] or 0

    if max_permission < 2:
        return redirect('suppliers:suppliers_list')
    supplier = get_object_or_404(Supplier,pk=pk)

    if request.method == 'POST':
        supplier.delete()
        return redirect('suppliers:suppliers_list')
    return redirect('suppliers:suppliers_list')