from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from django.contrib.auth import authenticate, login, logout
import json
import uuid
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import *
from .forms import *
from django.contrib import messages
from django.http import JsonResponse
from .helpers import send_forget_password_mail
from django.views.generic import ListView
from pc_app.templatetags.custom_filters import convert_to_myr
from reportlab.lib.pagesizes import letter
from io import BytesIO
from datetime import datetime

# Create your views here.
def rating_detail(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)
    order_rating = OrderRating.objects.filter(order_item=item).first()
    return render(request, 'pc_app/ratings_detail.html', {'item': item, 'order_rating': order_rating})


def get_cpu_info(request, cpu_id):
    cpu = CPU.objects.get(id=cpu_id)

    cpu_info = {
        'name': cpu.name,
        'price': convert_to_myr(cpu.price),
        # Add more fields as needed
    }

    return JsonResponse(cpu_info)


def get_gpu_info(request, gpu_id):
    gpu = GPU.objects.get(id=gpu_id)
    gpu_info = {
        'name': gpu.name,
        'chipset': gpu.chipset,
        'price': convert_to_myr(gpu.price)
        # Add more fields as needed
    }
    return JsonResponse(gpu_info)


def get_mboard_info(request, mboard_id):
    mboard = Motherboard.objects.get(id=mboard_id)
    mboard_info = {
        'name': mboard.name,
        'price': convert_to_myr(mboard.price)
        # Add more fields as needed
    }
    return JsonResponse(mboard_info)


def cart_items(request):
    # Get the favorited PC Builds for the current user
    cart_items = CartItem.objects.filter(user=request.user, is_purchased=False)

    context = {
        'cart_items': cart_items,
    }
    return render(request, 'pc_app/cart-items.html', context)


@login_required(login_url='login')
def add_to_cart(request, build_id=None):
    # Add to cart from Favourite Page
    if request.method == 'POST' and build_id:
        repurchase = request.POST.get('re-purchase-button')

        if repurchase == 'completed':
            build = CartItem.objects.get(
                id=build_id)  # Retrieve the selected build from cart
        elif repurchase is None:
            build = FavouritedPC.objects.get(
                id=build_id)  # Retrieve the selected build from favourite

        # Check if the item is already in the cart
        cpu_id = build.cpu.id
        gpu_id = build.gpu.id
        mboard_id = build.mboard.id

        cpu = CPU.objects.get(id=cpu_id)
        gpu = GPU.objects.get(id=gpu_id)
        mboard = Motherboard.objects.get(id=mboard_id)

        total_price = cpu.price + gpu.price + mboard.price

        created = CartItem.objects.create(
            cpu_id=cpu_id, gpu_id=gpu_id, mboard_id=mboard_id, total_price=total_price, user=request.user)

        if created:
            messages.success(request, "Item added to cart successfully!")
        else:
            messages.info(request, "Item is already in your cart.")

        # Redirect to the cart page or another relevant page
        return redirect('cart_items')

    # Add to cart from Customization
    elif request.method == 'POST':
        data = json.loads(request.body)
        cpu_id = data.get('cpu_id')
        gpu_id = data.get('gpu_id')
        mboard_id = data.get('mboard_id')

        if cpu_id and gpu_id and mboard_id:
            cpu = CPU.objects.get(id=cpu_id)
            gpu = GPU.objects.get(id=gpu_id)
            mboard = Motherboard.objects.get(id=mboard_id)

            total_price = cpu.price + gpu.price + mboard.price

            # Create a new CartItem and save it to the database
            cart_item = CartItem(cpu_id=cpu_id, gpu_id=gpu_id, mboard_id=mboard_id, 
                                 total_price=total_price, user=request.user)
            cart_item.save()

            return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method'})


def remove_from_cart(request, cart_item_id):
    try:
        cart_item = CartItem.objects.get(id=cart_item_id, user=request.user)
        cart_item.delete()

        # Display a success message that the build has been deleted
        messages.success(request, 'The item has been removed from the cart.')
    except FavouritedPC.DoesNotExist:
        # Display an error message if the build does not exist or does not belong to the current user
        messages.error(
            request, 'The item does not exist or does not belong to you.')
    except Exception as e:
        # Display an error message if there was an issue deleting the build
        messages.error(request, f'Error deleting the item: {e}')

    # Redirect back to the favorited_builds page
    return redirect('cart_items')


def checkout(request):
    # Get cart items for the user
    cart_items = CartItem.objects.filter(user=request.user, is_purchased=False)

    # Calculate the total price
    total_price = sum(item.total_price for item in cart_items)

    context = {
        'cart_items': cart_items,
        'total_price': total_price + 5,
    }

    return render(request, 'pc_app/checkout.html', context)

from django.conf import settings

def place_order(request):
    if request.method == 'POST':
        # Update the cart items to mark them as purchased
        cart_items = CartItem.objects.filter(
            user=request.user, is_purchased=False)
        order_datetime = datetime.now()  # Get the current date and time

        # for cart_item in cart_items:
        #     cart_item.is_purchased = True
        #     cart_item.order_date = order_datetime  # Assign the order date and time
        #     cart_item.save()

        # Additional order processing logic can go here

        # Create an in-memory PDF purchase confirmation
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)

        # Create a list to store the content of the PDF
        elements = []

        # Add a title
        title_style = getSampleStyleSheet()['Title']
        elements.append(Paragraph('Order Confirmation', title_style))

        # Add a spacer
        elements.append(Spacer(1, 12))

        # Create a table for order summary
        for cart_item in cart_items:
            data = [[f"Order #{cart_item.id}", 'Build'],
                    ['CPU', cart_item.cpu.name],
                    ['GPU', cart_item.gpu.name],
                    ['Total Price', cart_item.total_price]]

            # Create the table style
            table_style = [('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                           ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                           ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                           ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                           ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                           ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                           ('GRID', (0, 0), (-1, -1), 1, colors.black)]

            # Create the table and add it to elements
            order_summary_table = Table(data, colWidths=[150, 200, 150])
            order_summary_table.setStyle(TableStyle(table_style))
            elements.append(order_summary_table)

            elements.append(Spacer(1, 20))

        # Build the PDF document
        doc.build(elements)

        # Close the buffer and return the PDF as a response
        buffer.seek(0)

        #Remove below: 
        # Create an HttpResponse with the PDF content
        response = HttpResponse(buffer.read(), content_type='application/pdf')

        # Set the content-disposition header to prompt for download
        response['Content-Disposition'] = 'attachment; filename="purchase_confirmation.pdf"'

        return response

        # Send the PDF as an email attachment
        # subject = 'Purchase Confirmation'
        # message = 'Thank you for your purchase. Please find your purchase confirmation attached.'
        # from_email = settings.EMAIL_HOST_USER #'your_email@example.com' Replace with your email
        # recipient_list = [request.user.email]  # Use the user's email

        # email = EmailMessage(subject, message, from_email, recipient_list)
        # email.attach('purchase_confirmation.pdf', buffer.read(),
        #              'application/pdf')  # Attach the in-memory PDF
        # email.send()

        # Redirect to an order confirmation page
        return render(request, 'pc_app/order_confirmation.html')


def completed_order_view(request):
    shipped_items = CartItem.objects.filter(
        user=request.user, is_completed=True).order_by('-order_date')
    # Render the purchased_items in the purchase history template
    return render(request, 'pc_app/completed-order.html', {'shipped_items': shipped_items})

from win10toast import ToastNotifier

def ongoing_order_view(request):
    purchased_items = CartItem.objects.filter(
        user=request.user, is_purchased=True, is_completed=False).order_by('-order_date')
    
    send_notification = any(item.ready_pickup for item in purchased_items)

    # If 'ready_pickup' is True, send a Windows notification
    if send_notification:
        notification_message = "One or more of your order(s) is ready for pickup!"
        
        # Create a ToastNotifier instance and send the notification
        toaster = ToastNotifier()
        toaster.show_toast("ORDER READY TO PICK UP", notification_message, duration=5)

    return render(request, 'pc_app/ongoing-order.html', {'purchased_items': purchased_items})


def rate_order(request, item_id):
    item = CartItem.objects.get(id=item_id)

    if request.method == 'POST':
        rating = request.POST.get('orderRating')
        comment = request.POST.get('comment')

        order_rating = OrderRating.objects.create(
            order_item=item,
            user=request.user,
            rating=rating,
            comment=comment
        )

        item.order_rating = order_rating
        item.save()

    return redirect('completed_order')


# Favourite Build
@login_required(login_url='login')
def toggle_favorite(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        cpu_id = data.get('cpu_id')
        gpu_id = data.get('gpu_id')
        mboard_id = data.get('mboard_id')

        if cpu_id and gpu_id and mboard_id:
            cpu = CPU.objects.get(id=cpu_id)
            gpu = GPU.objects.get(id=gpu_id)
            mboard = Motherboard.objects.get(id=mboard_id)

            total_price = cpu.price + gpu.price + mboard.price

            pc_build, created = FavouritedPC.objects.get_or_create(
                user=request.user, cpu=cpu, gpu=gpu, mboard=mboard, total_price=total_price,
            )

            if created:
                response_data = {'success': True,
                                 'message': 'Build has been favorited.'}
            else:
                pc_build.delete()
                response_data = {'success': False,
                                 'message': 'Build has been unfavorited.'}

            return JsonResponse(response_data)

        return JsonResponse({'success': False})


def favorited_builds(request):
    # Get the favorited PC Builds for the current user
    favorited_builds = FavouritedPC.objects.filter(user=request.user)

    context = {
        'favorited_builds': favorited_builds,
    }
    return render(request, 'pc_app/favorited_builds.html', context)


def delete_favorited_build(request, build_id):
    try:
        # Get the favorited build to delete
        favorited_build = FavouritedPC.objects.get(
            id=build_id, user=request.user)
        favorited_build.delete()

        # Display a success message that the build has been deleted
        messages.success(
            request, 'The build has been removed from your favorites.')
    except FavouritedPC.DoesNotExist:
        # Display an error message if the build does not exist or does not belong to the current user
        messages.error(
            request, 'The build does not exist or does not belong to you.')
    except Exception as e:
        # Display an error message if there was an issue deleting the build
        messages.error(request, f'Error deleting the build: {e}')

    # Redirect back to the favorited_builds page
    return redirect('favorited_builds')


from django.db.models import ExpressionWrapper, F, FloatField, Value

# CPU
class CPUListView(ListView):
    model = CPU
    template_name = 'pc_app/cpu/cpu_list.html'
    context_object_name = 'cpus'
    paginate_by = 30  # Adjust the number of CPUs displayed per page as needed

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search_query')
        min_clock_speed = self.request.GET.get('min_clock_speed')
        min_core_count = self.request.GET.get('min_core_count')
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')

        if search_query:
            # Filter CPUs by name containing the search query (case-insensitive)
            queryset = queryset.filter(name__icontains=search_query)

        # Filter CPUs by minimum clock speed
        if min_clock_speed:
            queryset = queryset.filter(core_clock__gte=float(min_clock_speed))

        if min_price:
            min_price = float(min_price)
            min_price /= 4.55  # Divide by 4.55 as in your original code
            queryset = queryset.filter(price__gte=min_price)

        if max_price:
            max_price = float(max_price)
            max_price /= 4.55  # Divide by 4.55 as in your original code
            queryset = queryset.filter(price__lte=max_price)

        # Filter CPUs by minimum core count
        if min_core_count:
            queryset = queryset.filter(core_count__gte=int(min_core_count))

        return queryset

        return queryset


def cpu_detail(request, pk):
    cpu = CPU.objects.get(pk=pk)
    other_cpus = CPU.objects.exclude(pk=pk)

    if request.method == 'POST':
        form = CPUComparisonForm(request.POST)
        if form.is_valid():
            selected_cpu = form.cleaned_data['cpu']
            # Redirect to the comparison view with the selected CPUs
            return HttpResponseRedirect(f'/cpu/{cpu.pk}/{selected_cpu.pk}')
            # return HttpResponseRedirect(f'cpu/{cpu.pk}/{selected_cpu.pk}')
    else:
        form = CPUComparisonForm()

    return render(request, 'pc_app/cpu/cpu_detail.html', {'cpu': cpu, 'other_cpus': other_cpus, 'form': form})


def cpu_comparison(request, pk1, pk2):
    cpu1 = CPU.objects.get(pk=pk1)
    cpu2 = CPU.objects.get(pk=pk2)
    all_cpus = CPU.objects.exclude(pk__in=[pk1, pk2])

    return render(request, 'pc_app/cpu/cpu_comparison.html', {'cpu1': cpu1, 'cpu2': cpu2, 'all_cpus': all_cpus})


# GPU
class GPUListView(ListView):
    model = GPU
    template_name = 'pc_app/gpu/gpu_list.html'
    context_object_name = 'gpus'
    paginate_by = 30  # Adjust the number of CPUs displayed per page as needed

    def get_queryset(self):
        queryset = super().get_queryset()
        # sort_by = self.request.GET.get(
        #     'sort_by', 'name')  # Default sorting by name
        # return queryset.order_by(sort_by)
        search_query = self.request.GET.get('search_query')

        # Check if a search query is provided
        if search_query:
            # Filter GPUs by name containing the search query (case-insensitive)
            queryset = queryset.filter(name__icontains=search_query)

        return queryset


def gpu_detail(request, pk):
    gpu = GPU.objects.get(pk=pk)

    if request.method == 'POST':
        form = GPUComparisonForm(request.POST)
        if form.is_valid():
            selected_gpu = form.cleaned_data['gpu']
            # Redirect to the comparison view with the selected GPUs
            return HttpResponseRedirect(f'{selected_gpu.pk}')
    else:
        form = GPUComparisonForm()

    return render(request, 'pc_app/gpu/gpu_detail.html', {'gpu': gpu, 'form': form})


def gpu_comparison(request, pk1, pk2):
    gpu1 = GPU.objects.get(pk=pk1)
    gpu2 = GPU.objects.get(pk=pk2)

    return render(request, 'pc_app/gpu/gpu_comparison.html', {'gpu1': gpu1, 'gpu2': gpu2})


# Motherboard
class MBoardListView(ListView):
    model = Motherboard
    template_name = 'pc_app/motherboard/mboard_list.html'
    context_object_name = 'mboards'
    # paginate_by = 30  # Adjust the number of Motherboard displayed per page as needed

    # def get_queryset(self):
    #     queryset = super().get_queryset()
    #     # sort_by = self.request.GET.get(
    #     #     'sort_by', 'name')  # Default sorting by name
    #     # return queryset.order_by(sort_by)
    #     search_query = self.request.GET.get('search_query')

    #     # Check if a search query is provided
    #     if search_query:
    #         # Filter Motherboard by name containing the search query (case-insensitive)
    #         queryset = queryset.filter(name__icontains=search_query)


def mboard_detail(request, pk):
    mboard = Motherboard.objects.get(pk=pk)

    if request.method == 'POST':
        form = MBoardComparisonForm(request.POST)
        if form.is_valid():
            selected_mboard = form.cleaned_data['mboard']
            # Redirect to the comparison view with the selected GPUs
            return HttpResponseRedirect(f'{selected_mboard.pk}')
    else:
        form = MBoardComparisonForm()

    return render(request, 'pc_app/motherboard/mboard_detail.html', {'mboard': mboard, 'form': form})


def mboard_comparison(request, pk1, pk2):
    mboard1 = Motherboard.objects.get(pk=pk1)
    mboard2 = Motherboard.objects.get(pk=pk2)

    return render(request, 'pc_app/motherboard/mboard_compare.html', {'mboard1': mboard1, 'mboard2': mboard2})


# Authentication
def SignupPage(request):
    if request.method == 'POST':
        uname = request.POST.get('username')
        email = request.POST.get('email')
        pass1 = request.POST.get('password1')
        pass2 = request.POST.get('password2')

        if not uname or not email or not pass1 or not pass2:
            messages.error(request, "Please fill in all the fields!")
        else:
            if pass1 != pass2:
                messages.error(request, "Password does not match!")
            else:
                my_user = User.objects.create_user(uname, email, pass1)
                my_user.save()
                return redirect('login')

    return render(request, 'pc_app/signup.html')


def LoginPage(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('pass')

        if not username or not password:
            # Check if either username or password is empty
            messages.error(request, "Both username and password are required.")
        else:
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)

                # Clear browser history using JavaScript
                clear_history_script = """
                <script>
                    if (window.history.replaceState) {
                        window.history.replaceState(null, null, window.location.href);
                    }
                </script>
                """
                response = HttpResponse(clear_history_script)
                
                # Check if the user is a superuser
                if user.is_superuser:
                    # Redirect to the vendor dashboard for superusers
                    return redirect('vendor_order_list')
                else:
                    # Redirect to the home page for non-superusers
                    return redirect('home')
            else:
                messages.error(request, "Incorrect Username or Password!")

    # Set cache-control headers to prevent caching
    response = render(request, 'pc_app/login.html')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


def LogoutPage(request):
    logout(request)
    return redirect('login')


def update_profile_picture(request):
    if request.method == "POST":
        profile = request.user.profile
        profile.profile_picture = request.FILES.get("profile_picture")
        profile.save()
        return JsonResponse({"message": "Profile picture updated successfully."})
    return JsonResponse({"error": "Invalid request method."}, status=400)


@login_required(login_url='login')
def profile(request):
    user = request.user
    profile = user.profile

    # Password Change
    if request.method == 'POST':
        password_change_form = PasswordChangeForm(
            user=user, data=request.POST)
        if password_change_form.is_valid():
            password_change_form.save()
            messages.success(request, 'Password changed successfully!')
        else:
            messages.error(
                request, 'Password change failed! Please correct the errors below!')
    else:
        password_change_form = PasswordChangeForm(user=user)

    # Phone Number Update
    if request.method == 'POST' and not password_change_form.is_valid():
        phone_number_form = PhoneNumberForm(request.POST)

        if phone_number_form.is_valid():
            phone_number = phone_number_form.cleaned_data['phone_number']

            # Check if the phone number is in the +60 format
            if not phone_number.startswith('+60'):
                phone_number = '+60' + phone_number

            # Update or create the phone number in the profile
            profile.phone_number = phone_number
            profile.save()

            messages.success(request, 'Phone number updated successfully!')
        else:
            messages.error(
                request, 'Phone number update failed! Please correct the errors below.')

    else:
        phone_number_form = PhoneNumberForm(
            initial={'phone_number': profile.phone_number})

    return render(request, 'pc_app/profile.html', {
        'password_change_form': password_change_form,
        'phone_number_form': phone_number_form,
    })


def reset_password(request, token):
    context = {}
    try:
        profile_obj = Profile.objects.filter(
            forgot_password_token=token).first()

        if not profile_obj:
            messages.error(request, 'Invalid or expired password reset link.')
            return redirect('/forgot-password/')

        if profile_obj.is_password_reset_token_used:
            messages.error(
                request, 'This password reset link has already been used.')
            return redirect('/forgot-password/')

        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            user_id = request.POST.get('user_id')

            if user_id is None:
                messages.success(request, 'No user id found!')
                return redirect(f'/reset-password/{token}/')

            if new_password != confirm_password:
                messages.success(request, 'Password does not match!')
                return redirect(f'/reset-password/{token}/')

            user_obj = profile_obj.user
            user_obj.set_password(new_password)
            user_obj.save()

            # Mark the token as used
            profile_obj.is_password_reset_token_used = True
            profile_obj.save()

            messages.success(
                request, 'Password reset successful. You can now log in with your new password.')
            return redirect('/login/')

        context = {'user_id': profile_obj.user.id}

    except Exception as e:
        print(e)
    return render(request, 'pc_app/reset-password.html', context)


def ForgotPassword(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        # Check if a user with the given email address exists
        try:
            user_obj = User.objects.get(email=email)
            print(user_obj)
        except User.DoesNotExist:
            messages.error(request, 'No user found with this email address!')
            return redirect('/forgot-password/')

        # Generate a unique token for password reset
        token = str(uuid.uuid4())

        # Update the user's profile with the token
        profile_obj, created = Profile.objects.get_or_create(user=user_obj)
        profile_obj.forgot_password_token = token

        # Set is_password_reset_token_used to False for the new token
        profile_obj.is_password_reset_token_used = False
        profile_obj.save()

        # Send an email with the password reset link
        send_forget_password_mail(email, token)

        messages.success(
            request, 'An email has been sent with instructions to reset your password.')
        return redirect('/forgot-password/')

    return render(request, 'pc_app/forgot-password.html')
