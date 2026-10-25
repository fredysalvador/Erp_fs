from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Supplier
from .forms import SupplierForm, CsvUploadForm
from django.core.paginator import Paginator
from django.http import HttpResponse
import csv
import re
import io
from django.db import models
from users.models import UserRole
from django.contrib import messages


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
               supplier.legal_name,
               supplier.name,
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

@login_required
def supplier_bulk_create(request):

    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(max_permission=models.Max('role__suppliers'))['max_permission'] or 0

    if max_permission < 2:
        return redirect('suppliers:suppliers_list')

    if request.method == 'POST':
        form = CsvUploadForm(request.POST,request.FILES)

        if form.is_valid():
            csv_file = request.FILES['csv_file']

            try:
                data_set = csv_file.read().decode('UTF-8')
            except UnicodeDecodeError:
                try:
                    csv_file.seek(0)
                    data_set = csv_file.read().decode('ISO-8859-1')
                except  Exception as e:
                     return render(request, 'supplier/supplier_bulk_upload.html',{'form':form})  
 
            io_string = io.StringIO(data_set)
            reader = csv.DictReader(io_string)
    
            if reader.fieldnames:
                if reader.fieldnames[0].startswith('\ufeff'):
                    reader.fieldnames[0] = reader.fieldnames[0].lstrip('/ufeff')
    
                cleaned_fieldnames = [key.strip().lower() for key in reader.fieldnames]
                reader.fieldnames = cleaned_fieldnames
            successful_records = []
            error_records = []
            suppliers_to_create = []
    
            for i, row in enumerate(reader):
                row_number = i + 2
                form_data = {}
    
                for key,value in row.items():
                    cleaned_value = value.strip() if isinstance(value,str) else value
                    form_data[key] = cleaned_value
    
                form = SupplierForm(form_data)
    
                if form.is_valid():
                    supplier = form.save(commit=False)
                    supplier.created_by = request.user
                    suppliers_to_create.append(supplier)
                    successful_records.append({'row':row_number,'data':form_data})
                else:
                    errors = {
                        field:', '.join(err)
                        for field, err in form.errors.items()
                    }
                    error_records.append({
                        'row': row_number,
                        'data':form_data,
                        'errors':errors
                    })     
                             
            if suppliers_to_create:
                Supplier.objects.bulk_create(suppliers_to_create)

            messages.success(request, f'Process finished. {len(successful_records)} suppliers created succesfully.')
    
            context = {
                'form': form,
                'successful_count': len(successful_records),
                'error_count': len(error_records),
                'total_rows': len(successful_records) + len(error_records),
                'error_records': error_records,
                'succesful_records': successful_records,
                'report_generated': True
            }
    
            return render(request, 'suppliers/supplier_bulk_upload.html', context)            
        
        return render(request, 'suppliers/supplier_bulk_upload.html', {'form':form})
    
    else:
        form = CsvUploadForm()
        return render(request, 'suppliers/supplier_bulk_upload.html', {'form':form})
 
@login_required
def download_template_suppliers(request):

    header_fields = ['id_supplier', 'legal_name', 'name', 'tax_id', 'country', 'state_province', 'city', 'address', 'zip_code', 'phone', 'email', 'contact_name', 'contact_role',
                          'category', 'payment_terms', 'currency', 'payment_method', 'bank_account','status']

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="supplier_template.csv"'

    writer = csv.writer(response)
    writer.writerow(header_fields)

    return response