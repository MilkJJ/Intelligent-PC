# vendor/views.py
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from pc_app.models import CartItem  # Import the CartItem model from the main app=
from .models import GPUData, CPUData
import csv
from django.contrib.auth.decorators import user_passes_test
from .forms import CSVUploadForm
import pandas as pd

def is_vendor(user):
    return user.is_superuser

@user_passes_test(is_vendor, login_url='/login/')
def vendor_order_list(request):
    # Retrieve all CartItem objects with is_purchased=True
    purchased_items = CartItem.objects.filter(is_purchased=1)

    # You can now use 'purchased_items' in your template to display the purchased items
    context = {'purchased_items': purchased_items}
    return render(request, 'vendor/order_list.html', context)

    # vendor = Vendor.objects.get(user=request.user)
    # orders = VendorOrder.objects.filter(vendor=vendor)

@user_passes_test(is_vendor, login_url='/login/')
def vendor_order_detail(request, order_id):
    order = CartItem.objects.get(pk=order_id)
    # vendor = Vendor.objects.get(user=request.user)
    # order = get_object_or_404(VendorOrder, id=order_id, vendor=vendor)

    return render(request, 'vendor/order_detail.html', {'order': order})

@user_passes_test(is_vendor, login_url='/login/')
def mark_shipped(request, order_id):
    try:
        order = CartItem.objects.get(id=order_id)
        order.is_completed = True  # Mark the order as completed
        order.save()

        # Send Email to user for completed confirmation
        
    except CartItem.DoesNotExist:
        # Handle the case where the order is not found
        pass

    return redirect('vendor_order_list') 

def success_page(request):
    # Retrieve any success messages
    success_messages = messages.get_messages(request)
    
    context = {
        'success_messages': success_messages,
        # Your other context data here
    }
    
    return render(request, 'vendor/success.html', context)

# def upload_csv(request):
#     if request.method == 'POST':
#         form = CSVUploadForm(request.POST, request.FILES)
#         if form.is_valid():
#             #if csv_file.name.endswith('.csv'):
#             csv_file = request.FILES['csv_file']
#             decoded_file = csv_file.read().decode('utf-8')
#             csv_data = csv.reader(decoded_file.splitlines(), delimiter=',')
#             next(csv_data, None)  # Skip the header row if present

#             for row in csv_data:
#                 GPUData.objects.create(
#                     name = row[0],
#                     price = float(row[1]) , # Convert to float if needed
#                     chipset = row[2],
#                     memory = int(row[3]) , # Convert to int if needed
#                     core_clock = int(row[4]) , # Convert to int if needed
#                     boost_clock = int(row[5]),  # Convert to int if needed
#                     color = row[6],
#                     length = int(row[7]),
#                 )

#             return redirect('success_page')  # Redirect to a success page
#     else:
#         form = CSVUploadForm()

#     return render(request, 'vendor/upload.html', {'form': form})

def upload_csv(request):
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            decoded_file = csv_file.read().decode('utf-8')
            csv_data = csv.reader(decoded_file.splitlines(), delimiter=',')
            
            # Read the header row to determine the model (GPU or CPU)
            # Define the expected columns for GPUData
            gpu_columns = ['name', 'price', 'chipset', 'memory', 'core_clock', 'boost_clock', 'color', 'length']
                
            # Define the expected columns for CPUData
            cpu_columns = ['name', 'price', 'core_count', 'core_clock', 'boost_clock', 'tdp', 'graphics', 'smt', 'socket']

            header = next(csv_data, None)  
            try:
                if header:
                    if set(header) == set(gpu_columns):
                        model_class = GPUData
                        print('U GOT GPU')
                    elif set(header) == set(cpu_columns):
                        model_class = CPUData
                        print('U GOT CPU')
                    else:
                        return HttpResponse('Invalid CSV columns')  # Handle invalid columns

                    # Iterate through the rows and create objects based on the model
                    for row in csv_data:
                        if model_class == GPUData:
                            model_class.objects.create(
                                name=row[0],
                                price=row[1],
                                chipset=row[2],
                                memory=row[3],
                                core_clock=row[4],
                                boost_clock=row[5],
                                color=row[6],
                                length=row[7],  # Convert to float for DecimalField
                            )
                        elif model_class == CPUData:
                            model_class.objects.create(
                                name=row[0],
                                price=float(row[1]),
                                core_count=int(row[2]),
                                core_clock=float(row[3]),  # Convert to float for DecimalField
                                boost_clock=float(row[4]),  # Convert to float for DecimalField
                                tdp=int(row[5]),
                                graphics=row[6],
                                smt=row[7] == "TRUE",  # Convert "TRUE" to boolean
                                socket=row[8]
                            )
            
                if model_class == CPUData:
                    messages.success(request, 'Successfully imported CPU dataset')
            
                return redirect('success_page')  # Redirect to a success page
            
            except Exception as e:
                return HttpResponse(f'Error: {str(e)}')  # Handle any exceptions
            
    else:
        form = CSVUploadForm()

    return render(request, 'vendor/upload.html', {'form': form})

