# vendor/views.py
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from pc_app.models import *  # Import the CartItem model from the main app=
import csv
from django.contrib.auth.decorators import user_passes_test
from .forms import CSVUploadForm
import pandas as pd


def is_vendor(user):
    return user.is_superuser


@user_passes_test(is_vendor, login_url='/login/')
def vendor_completed_order(request):
    # Retrieve all CartItem objects with is_purchased=True
    order_id = request.GET.get('order_id')
    purchased_items = []

    if order_id:
        purchased_items = CartItem.objects.filter(is_completed=1, id=order_id)
    else:
        purchased_items = CartItem.objects.filter(is_completed=1)

    context = {'purchased_items': purchased_items,
               'order_id': order_id}

    return render(request, 'vendor/vendor_completed_order.html', context)


@user_passes_test(is_vendor, login_url='/login/')
def vendor_order_list(request):
    # Retrieve all CartItem objects with is_purchased=True
    order_id = request.GET.get('order_id')
    purchased_items = []

    if order_id:
        purchased_items = CartItem.objects.filter(
            is_purchased=1, is_completed=0, id=order_id)
        if not purchased_items:
            purchased_items = None
    else:
        purchased_items = CartItem.objects.filter(
            is_purchased=1, is_completed=0)

    # You can now use 'purchased_items' in your template to display the purchased items
    context = {'purchased_items': purchased_items,
               'order_id': order_id}

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
def mark_completed(request, order_id):
    try:
        order = CartItem.objects.get(id=order_id)
        order.is_completed = True  # Mark the order as completed
        order.save()

        # Send Email to user for completed confirmation
        if order.user.email:
            subject = f'Your Order #{order.id} is Completed'
            message = f'Hello {order.user.username},\n\nYou have picked up your Order #{order.id} Thank you for choosing us!'
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [order.user.email]

            send_mail(subject, message, from_email, recipient_list)

    except CartItem.DoesNotExist:
        # Handle the case where the order is not found
        pass

    return redirect('vendor_order_list')


@user_passes_test(is_vendor, login_url='/login/')
def mark_ready_pickup(request, order_id):
    try:
        order = CartItem.objects.get(id=order_id)
        order.ready_pickup = True  # Mark the order as completed
        order.save()

        # Inform user order is ready to be picked up through Email
        if order.user.email:
            subject = f'Your Order #{order.id} is Ready for Pickup'
            message = f'Hello {order.user.username},\n\nYour order is now ready for pickup.\n\nThank you for shopping with us!'
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [order.user.email]

            send_mail(subject, message, from_email, recipient_list)

    except CartItem.DoesNotExist:
        # Handle the case where the order is not found
        pass

    return redirect('vendor_order_list')


def upload_csv(request):
    # Retrieve any success messages
    success_messages = messages.get_messages(request)

    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            decoded_file = csv_file.read().decode('utf-8')
            csv_data = csv.reader(decoded_file.splitlines(), delimiter=',')

            # Read the header row to determine the model
            # Define the expected columns for CPU
            cpu_columns = ['name', 'price', 'core_count', 'core_clock',
                           'boost_clock', 'tdp', 'graphics', 'smt', 'socket']

            gpu_columns = ['name', 'price', 'chipset', 'memory',
                           'core_clock', 'boost_clock', 'color', 'length']

            motherboard_column = ['name', 'price', 'socket',
                                  'form_factor', 'max_memory', 'memory_slots', 'color']

            memory_columns = ['name', 'price', 'speed_mhz', 'num_modules', 'memory_size',
                              'price_per_gb', 'color', 'first_word_latency', 'cas_latency']

            storage_columns = ['name', 'price', 'capacity',
                               'price_per_gb', 'type', 'cache', 'form_factor', 'interface']

            psu_columns = ['name', 'price', 'type',
                           'efficiency', 'wattage', 'modular', 'color']

            case_columns = ['name', 'price', 'type', 'color', 'psu',
                            'side_panel', 'external_525_bays', 'internal_35_bays']

            # Cooler Columns

            header = next(csv_data, None)
            try:
                if header:
                    if set(header) == set(cpu_columns):
                        model_class = CPU
                    elif set(header) == set(gpu_columns):
                        model_class = GPU
                    elif set(header) == set(motherboard_column):
                        model_class = Motherboard
                    elif set(header) == set(memory_columns):
                        model_class = Memory
                    elif set(header) == set(storage_columns):
                        model_class = StorageDrive
                    elif set(header) == set(psu_columns):
                        model_class = PSU
                    elif set(header) == set(case_columns):
                        model_class = PCase

                    else:
                        # Handle invalid columns
                        return HttpResponse('Invalid CSV columns! Please upload the CSV based on Model attributes!')

                    # Iterate through the rows and create objects based on the model
                    for row in csv_data:
                        if model_class == GPU:
                            model_class.objects.get_or_create(
                                name=row[0],
                                price=row[1],
                                chipset=row[2],
                                memory=row[3],
                                core_clock=row[4],
                                boost_clock=row[5],
                                color=row[6],
                                # Convert to float for DecimalField
                                length=row[7],
                            )
                        elif model_class == CPU:
                            model_class.objects.create(
                                name=row[0],
                                price=float(row[1]),
                                core_count=int(row[2]),
                                # Convert to float for DecimalField
                                core_clock=float(row[3]),
                                # Convert to float for DecimalField
                                boost_clock=float(row[4]),
                                tdp=int(row[5]),
                                graphics=row[6],
                                # Convert "TRUE" to boolean
                                smt=row[7] == "TRUE",
                                socket=row[8]
                            )
                        elif model_class == Motherboard:
                            Motherboard.objects.get_or_create(
                                name=row[0],
                                price=float(row[1]),
                                socket=row[2],
                                form_factor=row[3],
                                max_memory=int(row[4]),
                                memory_slots=int(row[5]),
                                color=row[6]
                            )
                        elif model_class == Memory:
                            Memory.objects.get_or_create(
                                name=row[0],
                                price=float(row[1]),
                                speed_mhz=int(row[2]),
                                num_modules=int(row[3]),
                                memory_size=int(row[4]),
                                price_per_gb=float(row[5]),
                                color=row[6],
                                first_word_latency=row[7],
                                cas_latency=row[8]
                            )
                        elif model_class == StorageDrive:
                            StorageDrive.objects.get_or_create(
                                name=row[0],
                                price=float(row[1]),
                                capacity=int(row[2]),
                                price_per_gb=float(row[3]),
                                type=row[4],
                                cache=row[5],
                                form_factor=row[6],
                                interface=row[7]
                            )
                        elif model_class == PSU:
                            PSU.objects.get_or_create(
                                name=row[0],
                                price=float(row[1]),
                                type=row[2],
                                efficiency=row[3],
                                wattage=int(row[4]),
                                # Convert "TRUE" to boolean
                                modular=row[5] == "TRUE",
                                color=row[6]
                            )
                        elif model_class == PCase:
                            PCase.objects.get_or_create(
                                name=row[0],
                                price=float(row[1]),
                                type=row[2],
                                color=row[3],
                                psu=row[4],
                                side_panel=row[5],
                                external_525_bays=int(row[6]),
                                internal_35_bays=int(row[7])
                            )

                if model_class == CPU:
                    messages.success(
                        request, 'Successfully imported CPU dataset!')
                elif model_class == GPU:
                    messages.success(
                        request, 'Successfully imported GPU dataset!')
                elif model_class == Motherboard:
                    messages.success(
                    request, 'Successfully imported Motherboard dataset!')
                elif model_class == Memory:
                    messages.success(
                        request, 'Successfully imported Memory dataset!')
                elif model_class == StorageDrive:
                    messages.success(
                        request, 'Successfully imported Storage dataset!')
                elif model_class == PSU:
                    messages.success(
                        request, 'Successfully imported PSU dataset!')
                elif model_class == PCase:
                    messages.success(
                        request, 'Successfully imported Case dataset!')

                return redirect('upload_csv')  # Redirect to a success page

            except Exception as e:
                # Handle any exceptions
                return HttpResponse(f'Error: {str(e)}')

    else:
        form = CSVUploadForm()

    context = {
        'success_messages': success_messages,
        'form': form
    }

    return render(request, 'vendor/upload.html', context)
