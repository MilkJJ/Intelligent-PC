from django.contrib.auth import authenticate, login
import json, uuid
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import *
from .forms import *
from django.contrib import messages
from django.http import JsonResponse
from .helpers import send_forget_password_mail
from django.views.generic import ListView
from pc_app.templatetags.custom_filters import convert_to_myr
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.core.mail import EmailMessage
from io import BytesIO
from datetime import datetime

# Create your views here.
def rating_detail(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)
    order_rating = OrderRating.objects.filter(order_item=item).first()
    return render(request, 'pc_app/ratings_detail.html', {'item': item, 'order_rating': order_rating})

@login_required(login_url='login')
def HomePage(request):
    rated_items = CartItem.objects.filter(is_purchased=True, orderrating__isnull=False).annotate(
        latest_rating=models.Subquery(
            OrderRating.objects.filter(order_item=models.OuterRef('pk')).order_by('-date_added').values('rating')[:1]
        ),
        latest_comment=models.Subquery(
            OrderRating.objects.filter(order_item=models.OuterRef('pk')).order_by('-date_added').values('comment')[:1]
        )
    )

    context = {
        'rated_items': rated_items
    }

    return render(request, 'pc_app/home.html', context)


def find_compatible_cpu_upgrade(device_cpu_name, device_cpu_speed, device_socket):
    try:
        # Extract the brand and model name from the retrieved CPU name
        # Split the string by whitespace
        parts = device_cpu_name.split()

        # Extract the desired portion (assuming it's always at index 2)
        device_cpu_brand = ' '.join(parts[0:1]).strip('(R)')
        device_cpu_speed = device_cpu_speed / 1000
        # desired_cpu_core = ' '.join(parts[1:2]).strip('(TM)')
        # desired_cpu_model = ' '.join(parts[2:3])

        # cpu_model = desired_cpu_brand + ' ' + desired_cpu_core + ' ' + desired_cpu_model
        # current_cpu = CPU.objects.get(name=cpu_model)

        better_cpu_upgrades = CPU.objects.filter(
            name__icontains=device_cpu_brand,  # Partial string matching
            core_clock__gt=device_cpu_speed,
            socket__icontains=device_socket,
        ).order_by('-core_clock') 

        if better_cpu_upgrades:
            return better_cpu_upgrades.first() # Return the CPU with the highest core clock
        else:
            return None  # No compatible CPU upgrade found
    except CPU.DoesNotExist:
        return None  # CPU not found in the database
    

def upgrade(request):
    import wmi

    computer = wmi.WMI()
    computer_info = computer.Win32_ComputerSystem()[0]
    os_info = computer.Win32_OperatingSystem()[0]
    proc_info = computer.Win32_Processor()[0]
    gpu_info = computer.Win32_VideoController()[0]

    os_name = os_info.Name.encode('utf-8').split(b'|')[0]
    os_version = ' '.join([os_info.Version, os_info.BuildNumber])
    system_ram = round(
        float(os_info.TotalVisibleMemorySize) / 1048576)  # KB to GB
    system_ram1 = int(computer_info.TotalPhysicalMemory)

    print(gpu_info)

    suggested_cpu_upgrade = find_compatible_cpu_upgrade(proc_info.Name, proc_info.MaxClockSpeed, proc_info.SocketDesignation)

    context = {
        'os_name': os_name,
        'os_version': os_version,
        'proc_info': proc_info.Name,
        'system_ram': system_ram,
        'gpu_info': gpu_info.Name,
        'suggested_cpu_upgrade': suggested_cpu_upgrade,
    }

    return render(request, 'pc_app/upgrade.html', context)


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
        build = FavouritedPC.objects.get(
            id=build_id)  # Retrieve the selected build
        # Check if the item is already in the cart
        cpu_id = build.cpu.id
        gpu_id = build.gpu.id

        cpu = CPU.objects.get(id=cpu_id)
        gpu = GPU.objects.get(id=gpu_id)

        total_price = cpu.price + gpu.price

        created = CartItem.objects.create(
            cpu_id=cpu_id, gpu_id=gpu_id, total_price=total_price, user=request.user)

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

        if cpu_id and gpu_id:
            cpu = CPU.objects.get(id=cpu_id)
            gpu = GPU.objects.get(id=gpu_id)

            total_price = cpu.price + gpu.price

            # Create a new CartItem and save it to the database
            cart_item = CartItem(cpu_id=cpu_id, gpu_id=gpu_id,
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


def place_order(request):
    if request.method == 'POST':
        # Update the cart items to mark them as purchased
        cart_items = CartItem.objects.filter(
            user=request.user, is_purchased=False)
        order_datetime = datetime.now()  # Get the current date and time

        for cart_item in cart_items:
            cart_item.is_purchased = True
            cart_item.order_date = order_datetime  # Assign the order date and time
            cart_item.save()

        # Additional order processing logic can go here

        # Create an in-memory PDF purchase confirmation
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        p.drawString(100, 750, 'Purchase Confirmation!!')
        for cart_item in cart_items:
            p.drawString(100, 720, 'Order Summary')
            p.drawString(100, 700, f'CPU: {cart_item.cpu.name}')
            p.drawString(100, 650, f'GPU: {cart_item.gpu.name}')
            p.drawString(100, 600, f'Total Price: {cart_item.total_price}')
            p.drawString(100, 600, f'Buyer: {cart_item.user}')

        # Add more content to the PDF as needed

        p.showPage()  # Create the PDF
        p.save()  # Clean UP the library usage
        buffer.seek(0)  # Move the buffer's cursor to the beginning

        # Send the PDF as an email attachment
        subject = 'Purchase Confirmation'
        message = 'Thank you for your purchase. Please find your purchase confirmation attached.'
        from_email = 'your_email@example.com'  # Replace with your email
        recipient_list = [request.user.email]  # Use the user's email

        email = EmailMessage(subject, message, from_email, recipient_list)
        email.attach('purchase_confirmation.pdf', buffer.read(),
                     'application/pdf')  # Attach the in-memory PDF
        # email.send()

        # Redirect to an order confirmation page
        return render(request, 'pc_app/order_confirmation.html')


def completed_order_view(request):
    shipped_items = CartItem.objects.filter(
        user=request.user, is_completed=True).order_by('-order_date')
    # Render the purchased_items in the purchase history template
    return render(request, 'pc_app/completed-order.html', {'shipped_items': shipped_items})


def ongoing_order_view(request):
    purchased_items = CartItem.objects.filter(
        user=request.user, is_purchased=True, is_completed=False).order_by('-order_date')
    # Render the purchased_items in the purchase history template
    return render(request, 'pc_app/ongoing-order.html', {'purchased_items': purchased_items})


def rate_order(request, item_id):
    item = CartItem.objects.get(id=item_id)
    
    if request.method == 'POST':
        rating = request.POST.get('order_rating')
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

        if cpu_id and gpu_id:
            cpu = CPU.objects.get(id=cpu_id)
            gpu = GPU.objects.get(id=gpu_id)

            total_price = cpu.price + gpu.price

            pc_build, created = FavouritedPC.objects.get_or_create(
                user=request.user, cpu=cpu, gpu=gpu, total_price=total_price,
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


# CPU
class CPUListView(ListView):
    model = CPU
    template_name = 'pc_app/cpu/cpu_list.html'
    context_object_name = 'cpus'

    def get_queryset(self):
        queryset = super().get_queryset()
        sort_by = self.request.GET.get(
            'sort_by', 'name')  # Default sorting by name
        return queryset.order_by(sort_by)


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

    def get_queryset(self):
        queryset = super().get_queryset()
        sort_by = self.request.GET.get(
            'sort_by', 'name')  # Default sorting by name
        return queryset.order_by(sort_by)


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
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)

            # Check if the user is a superuser
            if user.is_superuser:
                # Redirect to the vendor dashboard for superusers
                return redirect('vendor_order_list')
            else:
                # Redirect to the home page for non-superusers
                return redirect('home')
        else:
            messages.error(request, "Incorrect Username/Password!")

    return render(request, 'pc_app/login.html')


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
    if request.method == 'POST':
        password_change_form = PasswordChangeForm(
            user=request.user, data=request.POST)
        if password_change_form.is_valid():
            password_change_form.save()
            messages.success(request, 'Password changed successfully!')
        else:
            messages.error(
                request, 'Password change failed! Please correct the errors below!')

    password_change_form = PasswordChangeForm(user=request.user)
    return render(request, 'pc_app/profile.html', {'password_change_form': password_change_form})


def ChangePassword(request, token):
    context = {}
    try:
        profile_obj = Profile.objects.filter(
            forgot_password_token=token).first()
        context = {'user_id': profile_obj.user.id}

        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            user_id = request.POST.get('user_id')

            if user_id is None:
                messages.success(request, 'No user id found!')
                return redirect(f'/change-password/{token}/')

            if new_password != confirm_password:
                messages.success(request, 'Password does not match!')
                return redirect(f'/change-password/{token}/')

            user_obj = User.objects.get(id=user_id)
            user_obj.set_password(new_password)
            user_obj.save()
            return redirect('/login/')

    except Exception as e:
        print(e)
    return render(request, 'pc_app/change-password.html', context)


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
        profile_obj.save()

        # Send an email with the password reset link
        send_forget_password_mail(email, token)

        messages.success(
            request, 'An email has been sent with instructions to reset your password.')
        return redirect('/forgot-password/')

    return render(request, 'pc_app/forgot-password.html')
