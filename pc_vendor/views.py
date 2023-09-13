# vendor/views.py
from django.shortcuts import redirect, render, get_object_or_404
from pc_app.models import CartItem  # Import the CartItem model from the main app=
from .models import GPUData
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
        order.isShipped = True  # Mark the order as shipped
        order.save()
    except CartItem.DoesNotExist:
        # Handle the case where the order is not found
        pass

    return redirect('vendor_order_list') 

def success_page(request):
    return render(request, 'vendor/success.html')

def upload_csv(request):
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            #if csv_file.name.endswith('.csv'):
            csv_file = request.FILES['csv_file']
            decoded_file = csv_file.read().decode('utf-8')
            csv_data = csv.reader(decoded_file.splitlines(), delimiter=',')
            next(csv_data, None)  # Skip the header row if present

            for row in csv_data:
                GPUData.objects.create(
                    name = row[0],
                    price = float(row[1]) , # Convert to float if needed
                    chipset = row[2],
                    memory = int(row[3]) , # Convert to int if needed
                    core_clock = int(row[4]) , # Convert to int if needed
                    boost_clock = int(row[5]),  # Convert to int if needed
                    color = row[6],
                    length = int(row[7]),
                )

            return redirect('success_page')  # Redirect to a success page
    else:
        form = CSVUploadForm()

    return render(request, 'vendor/upload.html', {'form': form})
