from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Customer
from core.models import Status, Country, Currency
from .forms import CustomerForm, CsvUploadForm
from django.core.paginator import Paginator
from django.http import HttpResponse
import csv
import re
import io
from django.db import models
from users.models import UserRole
from django.contrib import messages


@login_required
def customers_list(request):
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(max_permission=models.Max('role__customers'))['max_permission'] or 0

    if max_permission == 0:
        return redirect('dashboard')
    
    customers_list = Customer.objects.all()

    id_customer = request.GET.get('id_customer')
    name = request.GET.get('name')
    country = request.GET.get('country')
    status = request.GET.get('status')

    if id_customer:
       customers_list = customers_list.filter(id_customer__icontains=id_customer)
    if name:
       customers_list = customers_list.filter(name__icontains=name)
    if country:
           try:
               country_obj = Country.objects.get(name__iexact=country)
               customers_list = customers_list.filter(material_type=country_obj)
           except Country.DoesNotExist:
               customers_list = customers_list.none()
    if status:
          try:
              status_obj = Status.objects.get(name__iexact=status)
              customers_list = customers_list.filter(status=status_obj)
          except Status.DoesNotExist:
              customers_list = customers_list.none()

    if request.GET.get('export')  == 'csv':
       response = HttpResponse(content_type='text/csv')
       response['Content-Disposition'] = 'attachment; filename="customers.csv"'

       response.write('\ufeff'.encode('utf-8'))
       writer = csv.writer(response, delimiter=';')

       writer.writerow(['ID customer','Legal Name','Name','Tax ID','Country','State/Province','City'
                        ,'Address','Zip Code','Phone','Email','Contact name','Contact role','Category',
                        'Payment terms','Currency','Payment method','Bank account','Status',
                        'Created_by','Created At','Updated At'])
       
       for customer in customers_list:
           writer.writerow([
               customer.id_customer,
               customer.legal_name,
               customer.name,
               customer.tax_id,
               customer.country,
               customer.state_province,
               customer.city,
               customer.address,
               customer.zip_code,
               customer.phone,
               customer.email,
               customer.contact_name,
               customer.contact_role,
               customer.category,
               customer.payment_terms,
               customer.currency,
               customer.payment_method,
               customer.bank_account,
               customer.status,
               customer.created_by.username if customer.created_by else 'N/A',
               customer.created_at.strftime('%Y-%m-%d %H:%M:%S'),
               customer.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            ])
       return response

    paginator = Paginator(customers_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    try:
        all_statuses = Status.objects.all().order_by('name')
    except NameError:
        all_statuses = []

    try:
        all_countries = Country.objects.all().order_by('name')
    except NameError:
        all_countries = []

    context = {
        'page_obj': page_obj,
        'all_statuses': all_statuses,
        'all_countries': all_countries,
    }

    return render(request, 'customers/customers_list.html', context)



@login_required
def customer_create(request):
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(max_permission=models.Max('role__customers'))['max_permission'] or 0
    
    if max_permission in [0, 1]:
        # redirige según permiso
        return redirect('dashboard' if max_permission == 0 else 'customers')

    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.created_by = request.user
            customer.save()
            return redirect('customers:customer_create')
    else:
        form = CustomerForm()

    return render(request, 'customers/customer_form.html', {'form': form})

@login_required
def customer_edit(request,pk):
    customer = get_object_or_404(Customer,pk=pk)

    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(max_permission=models.Max('role__customers'))['max_permission'] or 0
    
    if max_permission == 1:
        return redirect('customers')
    if max_permission == 0:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return redirect('customers:customers_list')
    else:
        form = CustomerForm(instance=customer)
        
    context = {
        'form': form,
        'customer': customer,
    }

    return render(request, 'customers/customer_form.html', context)

@login_required
def customer_delete(request,pk):

    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(max_permission=models.Max('role__customers'))['max_permission'] or 0

    if max_permission < 2:
        return redirect('customers:customers_list')
    customer = get_object_or_404(Customer,pk=pk)

    if request.method == 'POST':
        customer.delete()
        return redirect('customers:customers_list')
    return redirect('customers:customers_list')

@login_required
def customer_bulk_create(request):

    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(max_permission=models.Max('role__customers'))['max_permission'] or 0

    if max_permission < 2:
        return redirect('customers:customers_list')

    if request.method == 'POST':
        form = CsvUploadForm(request.POST,request.FILES)

        if form.is_valid():
            csv_file = request.FILES['csv_file']
            status_map = {
            status.name.strip().lower(): status_map
            for status in Status.object.all()
        }
            currency_map = {
                currency.symbol.strip().lower: unit
                for currency in Currency.objects.all()
            }
            currency_map.update({currency.name.strip().lower(): currency
                for currency in Currency.objects.all()           
            })
            country_map = {
                country.symbol.strip().lower: country
                for country in Country.objects.all()
            }
            country_map.update({country.name.strip().lower(): country
                for country in Country.objects.all()           
            })

            try:
                data_set = csv_file.read().decode('UTF-8')
            except UnicodeDecodeError:
                try:
                    csv_file.seek(0)
                    data_set = csv_file.read().decode('ISO-8859-1')
                except  Exception as e:
                     return render(request, 'customer/customer_bulk_upload.html',{'form':form})  
 
            io_string = io.StringIO(data_set)
            reader = csv.DictReader(io_string)
    
            if reader.fieldnames:
                if reader.fieldnames[0].startswith('\ufeff'):
                    reader.fieldnames[0] = reader.fieldnames[0].lstrip('/ufeff')
    
                cleaned_fieldnames = [key.strip().lower() for key in reader.fieldnames]
                reader.fieldnames = cleaned_fieldnames
            successful_records = []
            error_records = []
            customers_to_create = []
    
            for i, row in enumerate(reader):
                row_number = i + 2
                form_data = {}
    
                for key,value in row.items():
                    cleaned_value = value.strip() if isinstance(value,str) else value
                    form_data[key] = cleaned_value

                currency_value = form_data.get('unit','').sreip().lower()
                currency_obj = currency_map.get(currency_value)
                if currency_obj:
                    form_data['unit'] = currency_obj.pk
                else:
                    error_records.append({
                        'row':row_number,
                        'data': row,
                        'errors':{'unit':f'Unit "{currency_value}" not found or invalid.'}
                    })
                    continue


                country_value = form_data.get('country','').sreip().lower()
                country_obj = country_map.get(country_value)

                if country_obj:
                    form_data['country'] = country_obj.pk
                else:
                    error_records.append({
                        'row':row_number,
                        'data': row,
                        'errors':{'country':f'Country "{country_value}" not found or invalid.'}
                    })
                    continue


                status_value = form_data.get('status','').sreip().lower()
                status_obj = status_map.get(status_value)

                if status_obj:
                    form_data['status'] = status_obj.pk
                else:
                    error_records.append({
                        'row':row_number,
                        'data': row,
                        'errors':{'status':f'Status "{status_value}" not found or invalid.'}
                    })
                    continue

    
                form = CustomerForm(form_data)
    
                if form.is_valid():
                    customer = form.save(commit=False)
                    customer.created_by = request.user
                    customers_to_create.append(customer)
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
                             
            if customers_to_create:
                Customer.objects.bulk_create(customers_to_create)

            messages.success(request, f'Process finished. {len(successful_records)} customers created succesfully.')
    
            context = {
                'form': form,
                'successful_count': len(successful_records),
                'error_count': len(error_records),
                'total_rows': len(successful_records) + len(error_records),
                'error_records': error_records,
                'succesful_records': successful_records,
                'report_generated': True
            }
    
            return render(request, 'customers/customer_bulk_upload.html', context)            
        
        return render(request, 'customers/customer_bulk_upload.html', {'form':form})
    
    else:
        form = CsvUploadForm()
        return render(request, 'customers/customer_bulk_upload.html', {'form':form})
 
@login_required
def download_template_customers(request):

    header_fields = ['id_customer', 'legal_name', 'name', 'tax_id', 'country', 'state_province', 'city', 'address', 'zip_code', 'phone', 'email', 'contact_name', 'contact_role',
                          'category', 'payment_terms', 'currency', 'payment_method', 'bank_account','status']

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="customer_template.csv"'

    writer = csv.writer(response)
    writer.writerow(header_fields)

    return response