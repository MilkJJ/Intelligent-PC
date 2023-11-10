import random
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import *
import pythoncom
from win32com.client import GetObject
import wmi

def upgrade(request):    
    budget = 9999

    if request.method == 'POST':
        budget = request.POST.get('budget', 9999)
        budget = float(budget)
        
    print('User Budget:', budget)

    # Define weightages for CPU, GPU, and RAM
    cpu_weightage = 0.4
    gpu_weightage = 0.3
    ram_weightage = 0.3

    # Calculate component budgets based on weightages
    cpu_budget = budget * cpu_weightage
    gpu_budget = budget * gpu_weightage
    ram_budget = budget * ram_weightage

    print('CPU:', cpu_budget, '\nGPU:', gpu_budget, '\nRAM:', ram_budget)

    pythoncom.CoInitialize()
    computer = wmi.WMI()
    # computer_info = computer.Win32_ComputerSystem()[0]
    # os_info = computer.Win32_OperatingSystem()[0]
    proc_info = computer.Win32_Processor()[0]
    gpu_info = computer.Win32_VideoController()[0]
    ram_info = computer.Win32_PhysicalMemory()

    # os_name = os_info.Name.encode('utf-8').split(b'|')[0]
    # os_version = ' '.join([os_info.Version, os_info.BuildNumber])
    # system_ram = round(
    #     float(os_info.TotalVisibleMemorySize) / 1048576)  # KB to GB
    # system_ram1 = int(computer_info.TotalPhysicalMemory)

    gpu_upgrade = find_gpu_upgrade(gpu_info, gpu_budget)
    cpu_upgrade = find_cpu_upgrade(request, proc_info, cpu_budget)

    ram_count = 0

    for ram in ram_info:
        ram_upgrade = find_ram_upgrade(ram, ram_budget)  # ram_info.Speed
        ram_count += 1
        ram_capacity = int(int(ram.Capacity) / 1048576 / 1000) # in GB

    context = {
        #CPU MODEL
        'proc_info': proc_info.Name,
        'gpu_info': gpu_info.Name,
        'ram_gb': ram_capacity,
        'ram_count': ram_count,
        'ram_speed': ram.Speed,
        
        'cpu_upgrade': cpu_upgrade,
        'gpu_upgrade': gpu_upgrade,
        'ram_upgrade': ram_upgrade,
    }

    return render(request, 'pc_app/upgrade.html', context)


def find_cpu_upgrade(request, proc_info, cpu_budget):
    device_cpu_name = proc_info.Name
    device_cpu_speed = proc_info.MaxClockSpeed
    device_socket = proc_info.SocketDesignation

    # Check if it is laptop, if it is notify user about laptop incompatible
    if device_socket.startswith("LGA") or device_socket.startswith("AM"):
        # Variable starts with "LGA" or "AM"
        messages.success(request, "You're on Desktop!")
    else:
        # Variable does not start with either "LGA" or "AM"
        messages.info(
            request, "You are using laptop, it may not recommend accurate upgrades!")

    try:
        # Extract the brand and model name from the retrieved CPU name
        # Split the string by whitespace
        if 'Intel' in device_cpu_name:
            device_cpu_brand = 'Intel'
        elif 'AMD' in device_cpu_name:
            device_cpu_brand = 'AMD'


        better_cpu_upgrades = CPU.objects.filter(
            name__icontains=device_cpu_brand,  # Partial string matching
            core_clock__gt=device_cpu_speed / 1000,
            #socket__icontains=device_socket, #Remove for laptop compatible
            price__lte=cpu_budget,
            # socket__icontains=device_socket,
        )  # .order_by('-core_clock')

        if better_cpu_upgrades:
            random_index = random.randint(0, better_cpu_upgrades.count() - 1)
            return better_cpu_upgrades[random_index] # Return the CPU with the highest core clock # Return the CPU with the highest core clock
        else:
            return None  # No compatible CPU upgrade found
    except CPU.DoesNotExist:
        return None  # CPU not found in the database


def find_ram_upgrade(ram_info, ram_budget):

    device_ram_size = int(ram_info.Capacity) / 1048576 / 1000
    device_ram_speed = ram_info.Speed
    device_ram_ddr = ram_info.MemoryType
    #print('DDR', device_ram_ddr)

    try:
        better_ram_upgrades = Memory.objects.filter(
            memory_size__icontains=int(device_ram_size),
            # ddr_type__icontains = device_ram_ddr,
            speed_mhz__gt=device_ram_speed,
            price__lte=ram_budget,
        )  # .order_by('-speed_mhz')

        if better_ram_upgrades:
            random_index = random.randint(0, better_ram_upgrades.count() - 1)
            return better_ram_upgrades[random_index]
        else:
            return None  # No compatible RAM upgrade found
    except Memory.DoesNotExist:
        return None  # RAM not found in the database


def find_gpu_upgrade(gpu_info, gpu_budget):
    # device_gpu_name = gpu_info.VideoProcessor
    device_gpu_vram = gpu_info.AdapterRAM
    device_gpu_vram = int((device_gpu_vram * -4095) / 1073479680)

    try:
        # Extract the brand and model name from the retrieved GPU name
        # Split the string by whitespace
        if 'GeForce' in gpu_info.VideoProcessor:
            device_gpu_brand = 'GeForce'
        elif 'Radeon' in gpu_info.VideoProcessor:
            device_gpu_brand = 'Radeon'

        better_gpu_upgrades = GPU.objects.filter(
            chipset__icontains=device_gpu_brand,  # Partial string matching
            memory__gt=device_gpu_vram,
            price__lte=gpu_budget,
        ).order_by('-core_clock')

        if better_gpu_upgrades:
            random_index = random.randint(0, better_gpu_upgrades.count() - 1)
            return better_gpu_upgrades[random_index]
            # return better_gpu_upgrades.first()  # Return the GPU with the highest core clock
        else:
            return None  # No compatible GPU upgrade found
    except GPU.DoesNotExist:
        return None  # GPU not found in the database