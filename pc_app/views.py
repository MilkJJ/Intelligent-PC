import json, uuid
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from .models import CPU, GPU, FavouritedPC, Profile
from .forms import CPUComparisonForm, GPUComparisonForm, PasswordChangeForm
from django.contrib import messages
from django.http import JsonResponse
from .helpers import send_forget_password_mail
from django.views.generic import ListView
from pc_app.templatetags.custom_filters import convert_to_myr


# Create your views here.
def upgrade(request):
    import wmi

    computer = wmi.WMI()
    computer_info = computer.Win32_ComputerSystem()[0]
    os_info = computer.Win32_OperatingSystem()[0]
    proc_info = computer.Win32_Processor()[0]
    gpu_info = computer.Win32_VideoController()[0]

    os_name = os_info.Name.encode('utf-8').split(b'|')[0]
    os_version = ' '.join([os_info.Version, os_info.BuildNumber])
    system_ram = round(float(os_info.TotalVisibleMemorySize) / 1048576)  # KB to GB
    system_ram1 = int(computer_info.TotalPhysicalMemory)

    context = {
        'os_name': os_name,
        'os_version': os_version,
        'proc_info': proc_info,
        'system_ram': system_ram,
        'gpu_info': gpu_info,
    }

    return render(request, 'upgrade.html', context)

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
        password_change_form = PasswordChangeForm(user=request.user, data=request.POST)
        if password_change_form.is_valid():
            password_change_form.save()
            messages.success(request, 'Password changed successfully!')
        else:
            messages.error(request, 'Password change failed! Please correct the errors below!')

    password_change_form = PasswordChangeForm(user=request.user)
    return render(request, 'profile.html', {'password_change_form': password_change_form})


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
                response_data = {'success': True}
            else:
                pc_build.delete()
                response_data = {'success': False}
            
            return JsonResponse(response_data)
            
        return JsonResponse({'success': False})
    
@login_required(login_url='login')
def HomePage(request):
    cpu_id = request.POST.get('cpu')
    gpu_id = request.POST.get('gpu')

    if request.method == 'POST':
        pc_build = FavouritedPC.objects.filter(cpu_id=cpu_id, gpu_id=gpu_id, user=request.user).first()

        if pc_build:
            #Change the heart shape color based on if the build is already favorited
            messages.info(request, 'This build is already in your favorites!')
            #pc_build.delete()
        else:
            try:
                #FavouritedPC.objects.create(cpu_id=cpu_id, gpu_id=gpu_id, user=request.user)
                favourited_pc = FavouritedPC(cpu_id=cpu_id, gpu_id=gpu_id, user=request.user)
                favourited_pc.save()
            except Exception as e:
                print(f"Error saving to database: {e}")
                
    cpu_list = CPU.objects.all()
    gpu_list = GPU.objects.all()

    context = {
        'cpu_list': cpu_list,
        'gpu_list': gpu_list,
    }

    return render(request, 'home.html', context)


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
    
def favorited_builds(request):
    # Get the favorited PC Builds for the current user
    favorited_builds = FavouritedPC.objects.filter(user=request.user)

    context = {
        'favorited_builds': favorited_builds,
    }
    return render(request, 'favorited_builds.html', context)


def delete_favorited_build(request, build_id):
    try:
        # Get the favorited build to delete
        favorited_build = FavouritedPC.objects.get(id=build_id, user=request.user)
        favorited_build.delete()

        # Display a success message that the build has been deleted
        messages.success(request, 'The build has been removed from your favorites.')
    except FavouritedPC.DoesNotExist:
        # Display an error message if the build does not exist or does not belong to the current user
        messages.error(request, 'The build does not exist or does not belong to you.')
    except Exception as e:
        # Display an error message if there was an issue deleting the build
        messages.error(request, f'Error deleting the build: {e}')

    # Redirect back to the favorited_builds page
    return redirect('favorited_builds')
    
# CPU
class CPUListView(ListView):
    model = CPU
    template_name = 'cpu_list.html'
    context_object_name = 'cpus'

def cpu_detail(request, pk):
    cpu = CPU.objects.get(pk=pk)
    other_cpus = CPU.objects.exclude(pk=pk)

    if request.method == 'POST':
        form = CPUComparisonForm(request.POST)
        if form.is_valid():
            selected_cpu = form.cleaned_data['cpu']
            # Redirect to the comparison view with the selected CPUs
            return HttpResponseRedirect(f'/cpu/{cpu.pk}/{selected_cpu.pk}')
            #return HttpResponseRedirect(f'cpu/{cpu.pk}/{selected_cpu.pk}')
    else:
        form = CPUComparisonForm()

    return render(request, 'cpu_detail.html', {'cpu': cpu, 'other_cpus': other_cpus, 'form': form})

def cpu_comparison(request, pk1, pk2):
    cpu1 = CPU.objects.get(pk=pk1)
    cpu2 = CPU.objects.get(pk=pk2)
    all_cpus = CPU.objects.exclude(pk__in=[pk1, pk2])

    return render(request, 'cpu_comparison.html', {'cpu1': cpu1, 'cpu2': cpu2, 'all_cpus': all_cpus})



# GPU
class GPUListView(ListView):
    model = GPU
    template_name = 'gpu_list.html'
    context_object_name = 'gpus'

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

    return render(request, 'gpu_detail.html', {'gpu': gpu, 'form': form})


def gpu_comparison(request, pk1, pk2):
    gpu1 = GPU.objects.get(pk=pk1)
    gpu2 = GPU.objects.get(pk=pk2)

    return render(request, 'gpu_comparison.html', {'gpu1': gpu1, 'gpu2': gpu2})


def SignupPage(request):
    if request.method=='POST':
        uname=request.POST.get('username')
        email=request.POST.get('email')
        pass1=request.POST.get('password1')
        pass2=request.POST.get('password2')

        if not uname  or not email or not pass1 or not pass2:
            messages.error(request, "Please fill in all the fields!")
        else:
            if pass1!=pass2:
                messages.error(request, "Password does not match!")
            else:
                my_user=User.objects.create_user(uname,email,pass1)
                my_user.save()
                return redirect('login')
        
    return render (request,'signup.html')


def LoginPage(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('pass')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Username/Password Incorrect!")
    
    return render(request, 'login.html')



def LogoutPage(request):
    logout(request)
    return redirect('login')


def ChangePassword(request, token):
    context = {}
    try:
        profile_obj = Profile.objects.filter(forgot_password_token = token).first()
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
            
            user_obj = User.objects.get(id = user_id)
            user_obj.set_password(new_password)
            user_obj.save()
            return redirect('/login/')

    except Exception as e:
        print(e)
    return render(request, 'change-password.html', context)


def ForgotPassword(request):
    try:
        if request.method == 'POST':
            username = request.POST.get('username')

            if not User.objects.filter(username=username).first():
                messages.success(request, 'No user found with this username!')
                return redirect('/forgot-password/')

            user_obj = User.objects.get(username = username)
            token = str(uuid.uuid4())
            profile_obj = Profile.objects.get(user = user_obj)
            profile_obj.forgot_password_token = token
            profile_obj.save()
            send_forget_password_mail(user_obj, token)
            messages.success(request, 'An email is sent!')
            return redirect('/forgot-password/')

    except Exception as e:
        print(e)
    return render(request, 'forgot-password.html')
