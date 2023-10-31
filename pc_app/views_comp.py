from django.shortcuts import render
from .models import *
from .forms import *
from django.views.generic import ListView
from io import BytesIO
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from io import BytesIO
import base64
from django.contrib import messages

# Create your views here.
# CPU
class CPUListView(ListView):
    model = CPU
    template_name = 'pc_app/cpu/cpu_list.html'
    context_object_name = 'cpus'
    paginate_by = 30

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

def cpu_detail(request, pk):
    cpu = CPU.objects.get(pk=pk)
    other_cpus = CPU.objects.exclude(pk=pk)
    user = request.user
    
    pivot_table, created = CPUPivotTable.objects.get_or_create(user=user, cpu=cpu)

    if(pivot_table.ratings != 0):
        rates = pivot_table.ratings
    else:
        rates = 0

    if request.method == 'POST':
        if 'cpu_rating_form' in request.POST:
            #if request.POST.get('name') == 'cpu_rating_form':
            rating_form = CPUPivotTableForm(request.POST)

            if rating_form.is_valid():
                rating = rating_form.cleaned_data['cpuRating']

                try:
                    cart_item = CartItem.objects.filter(user=user, cpu=cpu, is_purchased=True).first()

                    if cart_item:
                        if cart_item.is_purchased:
                            pivot_table, created = CPUPivotTable.objects.get_or_create(user=user, cpu=cpu)
                            if pivot_table:
                                pivot_table.ratings = rating
                                pivot_table.save()
                                rates = pivot_table.ratings
                                messages.success(request, 'Sucessfully rated this CPU!')
                            else:
                                messages.info(request, 'CPU already reated!')
                        else:
                            messages.info(request, 'Purchase CPU before Rating!')
                    else:
                        messages.info(request, 'Purchase CPU before Rating!')
                except CartItem.DoesNotExist:
                    messages.info(request, 'Purchase CPU before Rating!')

    else:
        rating_form = CPUPivotTableForm()

    return render(request, 'pc_app/cpu/cpu_detail.html', {'cpu': cpu, 'other_cpus': other_cpus, 'rating_form': rating_form, 'rate': int(rates)})


def cpu_comparison(request, pk1, pk2):
    cpu1 = CPU.objects.get(pk=pk1)
    cpu2 = CPU.objects.get(pk=pk2)
    all_cpus = CPU.objects.exclude(pk__in=[pk1, pk2])
    
# Prepare data for the chart
    attributes = ['CoreCount', 'CoreClock', 'BoostClock']
    values_cpu1 = [cpu1.core_count, cpu1.core_clock, cpu1.boost_clock]
    values_cpu2 = [cpu2.core_count, cpu2.core_clock, cpu2.boost_clock]

    # Create a horizontal bar chart
    num_attributes = len(attributes)
    height = 0.35
    y = range(num_attributes)

    fig, ax = plt.subplots()
    ax.barh(y, values_cpu1, height, label=cpu1.name)
    ax.barh([yi + height for yi in y], values_cpu2, height, label=cpu2.name)

    ax.set_ylabel('Attributes')
    ax.set_xlabel('Values')
    ax.set_title('CPU Comparison')
    ax.set_yticks([yi + height/2 for yi in y])
    ax.set_yticklabels(attributes)
    ax.invert_yaxis()
    ax.legend()

    # Save the chart as an image
    canvas = FigureCanvasAgg(fig)
    buffer = BytesIO()
    canvas.print_png(buffer)
    buffer.seek(0)
    chart = base64.b64encode(buffer.read()).decode('utf-8')
    buffer.close()

    # Render the chart in the template
    context = {
        'chart': chart,
        'cpu1': cpu1,
        'cpu2': cpu2,
        'all_cpus': all_cpus,
    }

    return render(request, 'pc_app/cpu/cpu_comparison.html', context)



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
    other_gpus = GPU.objects.exclude(pk=pk)
    user = request.user
    
    pivot_table, created = GPUPivotTable.objects.get_or_create(user=user, gpu=gpu)

    if(pivot_table.ratings != 0):
        rates = pivot_table.ratings
    else:
        rates = 0

    if request.method == 'POST':
        if 'gpu_rating_form' in request.POST:
        #if request.POST.get('name') == 'gpu_rating_form':
            rating_form = GPUPivotTableForm(request.POST)
            if rating_form.is_valid():
                rating = rating_form.cleaned_data['gpuRating']
    
                try:
                    cart_item = CartItem.objects.filter(user=user, gpu=gpu, is_purchased=True).first()

                    if cart_item:
                        if cart_item.is_purchased:
                            pivot_table, created = GPUPivotTable.objects.get_or_create(user=user, gpu=gpu)
                            if pivot_table:
                                pivot_table.ratings = rating
                                pivot_table.save()
                                rates = pivot_table.ratings
                            else:
                                print('CPU already rated!')
                        else:
                            print('Purchase CPU before Rating!')
                    else:
                        print('Add to cart CPU before Rating!')
                except CartItem.DoesNotExist:
                    print('Add to cart CPU before Rating!')

    else:
        rating_form = GPUPivotTableForm()

    return render(request, 'pc_app/gpu/gpu_detail.html', {'gpu': gpu, 'other_gpus': other_gpus, 'rating_form': rating_form, 'rate': int(rates)})


def gpu_comparison(request, pk1, pk2):
    gpu1 = GPU.objects.get(pk=pk1)
    gpu2 = GPU.objects.get(pk=pk2)
    all_gpus = GPU.objects.exclude(pk__in=[pk1, pk2])
    
# Prepare data for the chart
    attributes = ['CoreClock', 'BoostClock', 'Memory']
    values_gpu1 = [gpu1.core_clock, gpu1.boost_clock, gpu1.memory]
    values_gpu2 = [gpu2.core_clock, gpu2.boost_clock, gpu2.memory]

    # Create a horizontal bar chart
    num_attributes = len(attributes)
    height = 0.35
    y = range(num_attributes)

    fig, ax = plt.subplots()
    ax.barh(y, values_gpu1, height, label=gpu1.name)
    ax.barh([yi + height for yi in y], values_gpu2, height, label=gpu2.name)

    ax.set_ylabel('Attributes')
    ax.set_xlabel('Values')
    ax.set_title('GPU Comparison')
    ax.set_yticks([yi + height/2 for yi in y])
    ax.set_yticklabels(attributes)
    ax.invert_yaxis()
    ax.legend()

    # Save the chart as an image
    canvas = FigureCanvasAgg(fig)
    buffer = BytesIO()
    canvas.print_png(buffer)
    buffer.seek(0)
    chart = base64.b64encode(buffer.read()).decode('utf-8')
    buffer.close()

    # Render the chart in the template
    context = {
        'chart': chart,
        'gpu1': gpu1,
        'gpu2': gpu2,
        'all_gpus': all_gpus,
    }

    return render(request, 'pc_app/gpu/gpu_comparison.html', context)


# Motherboard
class MBoardListView(ListView):
    model = Motherboard
    template_name = 'pc_app/mboard/mboard_list.html'
    context_object_name = 'mboards'
    paginate_by = 30  # Adjust the number of Motherboard displayed per page as needed

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


def mboard_detail(request, pk):
    mboard = Motherboard.objects.get(pk=pk)
    other_mboards = Motherboard.objects.exclude(pk=pk)
    user = request.user

    pivot_table, created = MotherboardPivotTable.objects.get_or_create(user=user, mboard=mboard)

    if(pivot_table.ratings != 0):
        rates = pivot_table.ratings
    else:
        rates = 0

    if request.method == 'POST':
        if 'mboard_rating_form' in request.POST:
        #if request.POST.get('name') == 'mboard_rating_form':
            rating_form = MotherboardPivotTableForm(request.POST)
            if rating_form.is_valid():
                rating = rating_form.cleaned_data['mboardRating']

                try:
                    cart_item = CartItem.objects.filter(user=user, mboard=mboard, is_purchased=True).first()

                    if cart_item:
                        if cart_item.is_purchased:
                            pivot_table, created = MotherboardPivotTable.objects.get_or_create(user=user, mboard=mboard)
                            if pivot_table:
                                pivot_table.ratings = rating
                                pivot_table.save()
                                rates = pivot_table.ratings
                            else:
                                print('CPU already rated!')
                        else:
                            print('Purchase CPU before Rating!')
                    else:
                        print('Add to cart CPU before Rating!')
                except CartItem.DoesNotExist:
                    print('Add to cart CPU before Rating!')

    else:
        rating_form = MotherboardPivotTableForm()

    return render(request, 'pc_app/mboard/mboard_detail.html', {'mboard': mboard, 'other_mboards': other_mboards, 'rating_form': rating_form, 'rate': int(rates)})


def mboard_comparison(request, pk1, pk2):
    mboard1 = Motherboard.objects.get(pk=pk1)
    mboard2 = Motherboard.objects.get(pk=pk2)
    all_mboards = Motherboard.objects.exclude(pk__in=[pk1, pk2])
    
# Prepare data for the chart
    attributes = ['MaxMemory', 'MemorySlots']
    values_mboard1 = [mboard1.max_memory, mboard1.memory_slots]
    values_mboard2 = [mboard2.max_memory, mboard2.memory_slots]

    # Create a horizontal bar chart
    num_attributes = len(attributes)
    height = 0.35
    y = range(num_attributes)

    fig, ax = plt.subplots()
    ax.barh(y, values_mboard1, height, label=mboard1.name)
    ax.barh([yi + height for yi in y], values_mboard2, height, label=mboard2.name)

    ax.set_ylabel('Attributes')
    ax.set_xlabel('Values')
    ax.set_title('Motherboard Comparison')
    ax.set_yticks([yi + height/2 for yi in y])
    ax.set_yticklabels(attributes)
    ax.invert_yaxis()
    ax.legend()

    # Save the chart as an image
    canvas = FigureCanvasAgg(fig)
    buffer = BytesIO()
    canvas.print_png(buffer)
    buffer.seek(0)
    chart = base64.b64encode(buffer.read()).decode('utf-8')
    buffer.close()

    # Render the chart in the template
    context = {
        'chart': chart,
        'mboard1': mboard1,
        'mboard2': mboard2,
        'all_mboards': all_mboards,
    }

    return render(request, 'pc_app/mboard/mboard_comparison.html', context)


#RAM
class RAMListView(ListView):
    model = Memory
    template_name = 'pc_app/ram/ram_list.html'
    context_object_name = 'rams'
    paginate_by = 30

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search_query')

        if search_query:
            # Filter RAM by name containing the search query (case-insensitive)
            queryset = queryset.filter(name__icontains=search_query)

        return queryset
    
def ram_detail(request, pk):
    ram = Memory.objects.get(pk=pk)
    other_rams = Memory.objects.exclude(pk=pk)
    user = request.user

    pivot_table, created = RAMPivotTable.objects.get_or_create(user=user, ram=ram)

    if(pivot_table.ratings != 0):
        rates = pivot_table.ratings
    else:
        rates = 0

    if request.method == 'POST':
        if 'ram_rating_form' in request.POST:
        #if request.POST.get('name') == 'ram_rating_form':
            rating_form = RAMPivotTableForm(request.POST)
            if rating_form.is_valid():
                rating = rating_form.cleaned_data['ramRating']

                try:
                    cart_item = CartItem.objects.filter(user=user, ram=ram, is_purchased=True).first()

                    if cart_item:
                        if cart_item.is_purchased:
                            pivot_table, created = RAMPivotTable.objects.get_or_create(user=user, ram=ram)
                            if pivot_table:
                                pivot_table.ratings = rating
                                pivot_table.save()
                                rates = pivot_table.ratings
                            else:
                                print('CPU already rated!')
                        else:
                            print('Purchase CPU before Rating!')
                    else:
                        print('Add to cart CPU before Rating!')
                except CartItem.DoesNotExist:
                    print('Add to cart CPU before Rating!')

    else:
        rating_form = RAMPivotTableForm()

    return render(request, 'pc_app/ram/ram_detail.html', {'ram': ram, 'other_rams': other_rams, 'rating_form': rating_form, 'rate': int(rates)})


def ram_comparison(request, pk1, pk2):
    ram1 = Memory.objects.get(pk=pk1)
    ram2 = Memory.objects.get(pk=pk2)
    all_rams = Memory.objects.exclude(pk__in=[pk1, pk2])
    
# Prepare data for the chart
    attributes = ['Speed_Mhz', 'MemorySize']
    values_ram1 = [ram1.speed_mhz, ram1.memory_size]
    values_ram2 = [ram2.speed_mhz, ram2.memory_size]

    # Create a horizontal bar chart
    num_attributes = len(attributes)
    height = 0.35
    y = range(num_attributes)

    fig, ax = plt.subplots()
    ax.barh(y, values_ram1, height, label=ram1.name)
    ax.barh([yi + height for yi in y], values_ram2, height, label=ram2.name)

    ax.set_ylabel('Attributes')
    ax.set_xlabel('Values')
    ax.set_title('RAM Comparison')
    ax.set_yticks([yi + height/2 for yi in y])
    ax.set_yticklabels(attributes)
    ax.invert_yaxis()
    ax.legend()

    # Save the chart as an image
    canvas = FigureCanvasAgg(fig)
    buffer = BytesIO()
    canvas.print_png(buffer)
    buffer.seek(0)
    chart = base64.b64encode(buffer.read()).decode('utf-8')
    buffer.close()

    # Render the chart in the template
    context = {
        'chart': chart,
        'ram1': ram1,
        'ram2': ram2,
        'all_rams': all_rams,
    }

    return render(request, 'pc_app/ram/ram_comparison.html', context)


#Storage Drive
class StorageListView(ListView):
    model = StorageDrive
    template_name = 'pc_app/storage/storage_list.html'
    context_object_name = 'storages'
    paginate_by = 30  # Adjust the number of CPUs displayed per page as needed

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search_query')

        if search_query:
            # Filter CPUs by name containing the search query (case-insensitive)
            queryset = queryset.filter(name__icontains=search_query)

        return queryset
    
def storage_detail(request, pk):
    storage = StorageDrive.objects.get(pk=pk)
    other_storages = StorageDrive.objects.exclude(pk=pk)
    user = request.user

    pivot_table, created = StoragePivotTable.objects.get_or_create(user=user, storage=storage)

    if(pivot_table.ratings != 0):
        rates = pivot_table.ratings
    else:
        rates = 0

    if request.method == 'POST':
        if 'storage_rating_form' in request.POST:
        #if request.POST.get('name') == 'storage_rating_form':
            rating_form = StoragePivotTableForm(request.POST)
            if rating_form.is_valid():
                rating = rating_form.cleaned_data['storageRating']

                try:
                    cart_item = CartItem.objects.filter(user=user, storage=storage, is_purchased=True).first()

                    if cart_item:
                        if cart_item.is_purchased:
                            pivot_table, created = StoragePivotTable.objects.get_or_create(user=user, storage=storage)
                            if pivot_table:
                                pivot_table.ratings = rating
                                pivot_table.save()
                                rates = pivot_table.ratings
                            else:
                                print('CPU already rated!')
                        else:
                            print('Purchase CPU before Rating!')
                    else:
                        print('Add to cart CPU before Rating!')
                except CartItem.DoesNotExist:
                    print('Add to cart CPU before Rating!')

    else:
        rating_form = StoragePivotTableForm()

    return render(request, 'pc_app/storage/storage_detail.html', {'storage': storage, 'other_storages': other_storages, 'rating_form': rating_form, 'rate': int(rates)})


def storage_comparison(request, pk1, pk2):
    storage1 = StorageDrive.objects.get(pk=pk1)
    storage2 = StorageDrive.objects.get(pk=pk2)
    all_storages = StorageDrive.objects.exclude(pk__in=[pk1, pk2])
    
# Prepare data for the chart
    attributes = ['Capacity']
    values_storage1 = [storage1.capacity]
    values_storage2 = [storage2.capacity]

    # Create a horizontal bar chart
    num_attributes = len(attributes)
    height = 0.35
    y = range(num_attributes)

    fig, ax = plt.subplots()
    ax.barh(y, values_storage1, height, label=storage1.name)
    ax.barh([yi + height for yi in y], values_storage2, height, label=storage2.name)

    ax.set_ylabel('Attributes')
    ax.set_xlabel('Values')
    ax.set_title('Storage Comparison')
    ax.set_yticks([yi + height/2 for yi in y])
    ax.set_yticklabels(attributes)
    ax.invert_yaxis()
    ax.legend()

    # Save the chart as an image
    canvas = FigureCanvasAgg(fig)
    buffer = BytesIO()
    canvas.print_png(buffer)
    buffer.seek(0)
    chart = base64.b64encode(buffer.read()).decode('utf-8')
    buffer.close()

    # Render the chart in the template
    context = {
        'chart': chart,
        'storage1': storage1,
        'storage2': storage2,
        'all_storages': all_storages,
    }

    return render(request, 'pc_app/storage/storage_comparison.html', context)


#PSU
class PSUListView(ListView):
    model = PSU
    template_name = 'pc_app/psu/psu_list.html'
    context_object_name = 'psus'
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

        return queryset
    
def psu_detail(request, pk):
    psu = PSU.objects.get(pk=pk)
    other_psus = PSU.objects.exclude(pk=pk)
    user = request.user

    pivot_table, created = PSUPivotTable.objects.get_or_create(user=user, psu=psu)

    if(pivot_table.ratings != 0):
        rates = pivot_table.ratings
    else:
        rates = 0
    
    if request.method == 'POST':
        if 'psu_rating_form' in request.POST:
        #if request.POST.get('name') == 'psu_rating_form':
            rating_form = PSUPivotTableForm(request.POST)
            if rating_form.is_valid():
                rating = rating_form.cleaned_data['psuRating']

                try:
                    cart_item = CartItem.objects.filter(user=user, psu=psu, is_purchased=True).first()

                    if cart_item:
                        if cart_item.is_purchased:
                            pivot_table, created = PSUPivotTable.objects.get_or_create(user=user, psu=psu)
                            if pivot_table:
                                pivot_table.ratings = rating
                                pivot_table.save()
                                rates = pivot_table.ratings
                            else:
                                print('CPU already rated!')
                        else:
                            print('Purchase CPU before Rating!')
                    else:
                        print('Add to cart CPU before Rating!')
                except CartItem.DoesNotExist:
                    print('Add to cart CPU before Rating!')

    else:
        rating_form = PSUPivotTableForm()

    return render(request, 'pc_app/psu/psu_detail.html', {'psu': psu, 'other_psus': other_psus, 'rating_form': rating_form, 'rate': int(rates)})


def psu_comparison(request, pk1, pk2):
    psu1 = PSU.objects.get(pk=pk1)
    psu2 = PSU.objects.get(pk=pk2)
    all_psus = PSU.objects.exclude(pk__in=[pk1, pk2])
    
# Prepare data for the chart
    attributes = ['Wattage']
    values_psu1 = [psu1.wattage]
    values_psu2 = [psu2.wattage]

    # Create a horizontal bar chart
    num_attributes = len(attributes)
    height = 0.35
    y = range(num_attributes)

    fig, ax = plt.subplots()
    ax.barh(y, values_psu1, height, label=psu1.name)
    ax.barh([yi + height for yi in y], values_psu2, height, label=psu2.name)

    ax.set_ylabel('Attributes')
    ax.set_xlabel('Values')
    ax.set_title('PSU Comparison')
    ax.set_yticks([yi + height/2 for yi in y])
    ax.set_yticklabels(attributes)
    ax.invert_yaxis()
    ax.legend()

    # Save the chart as an image
    canvas = FigureCanvasAgg(fig)
    buffer = BytesIO()
    canvas.print_png(buffer)
    buffer.seek(0)
    chart = base64.b64encode(buffer.read()).decode('utf-8')
    buffer.close()

    # Render the chart in the template
    context = {
        'chart': chart,
        'psu1': psu1,
        'psu2': psu2,
        'all_psus': all_psus,
    }

    return render(request, 'pc_app/psu/psu_comparison.html', context)


#Case
class CaseListView(ListView):
    model = PCase
    template_name = 'pc_app/case/case_list.html'
    context_object_name = 'cases'
    paginate_by = 30  # Adjust the number of CPUs displayed per page as needed

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search_query')

        if search_query:
            # Filter CPUs by name containing the search query (case-insensitive)
            queryset = queryset.filter(name__icontains=search_query)

        return queryset
    
def case_detail(request, pk):
    case = PCase.objects.get(pk=pk)
    other_cases = PCase.objects.exclude(pk=pk)
    user = request.user

    pivot_table, created = PCasePivotTable.objects.get_or_create(user=user, case=case)

    if(pivot_table.ratings != 0):
        rates = pivot_table.ratings
    else:
        rates = 0

    if request.method == 'POST':
        if 'case_rating_form' in request.POST:
        #if request.POST.get('name') == 'case_rating_form':
            rating_form = PCasePivotTableForm(request.POST)
            if rating_form.is_valid():
                rating = rating_form.cleaned_data['caseRating']

                try:
                    cart_item = CartItem.objects.filter(user=user, case=case, is_purchased=True).first()

                    if cart_item:
                        if cart_item.is_purchased:
                            pivot_table, created = PCasePivotTable.objects.get_or_create(user=user, case=case)
                            if pivot_table:
                                pivot_table.ratings = rating
                                pivot_table.save()
                                rates = pivot_table.ratings
                            else:
                                print('CPU already rated!')
                        else:
                            print('Purchase CPU before Rating!')
                    else:
                        print('Add to cart CPU before Rating!')
                except CartItem.DoesNotExist:
                    print('Add to cart CPU before Rating!')

    else:
        rating_form = PCasePivotTableForm()

    return render(request, 'pc_app/case/case_detail.html', {'case': case, 'other_cases': other_cases, 'rating_form': rating_form, 'rate': int(rates)})


def case_comparison(request, pk1, pk2):
    case1 = PCase.objects.get(pk=pk1)
    case2 = PCase.objects.get(pk=pk2)
    all_cases = PCase.objects.exclude(pk__in=[pk1, pk2])
    
# Prepare data for the chart
    attributes = ['ExternalBay', 'InternalBay']
    values_case1 = [case1.external_525_bays, case1.internal_35_bays]
    values_case2 = [case2.external_525_bays, case2.internal_35_bays]

    # Create a horizontal bar chart
    num_attributes = len(attributes)
    height = 0.35
    y = range(num_attributes)

    fig, ax = plt.subplots()
    ax.barh(y, values_case1, height, label=case1.name)
    ax.barh([yi + height for yi in y], values_case2, height, label=case2.name)

    ax.set_ylabel('Attributes')
    ax.set_xlabel('Values')
    ax.set_title('Case Comparison')
    ax.set_yticks([yi + height/2 for yi in y])
    ax.set_yticklabels(attributes)
    ax.invert_yaxis()
    ax.legend()

    # Save the chart as an image
    canvas = FigureCanvasAgg(fig)
    buffer = BytesIO()
    canvas.print_png(buffer)
    buffer.seek(0)
    chart = base64.b64encode(buffer.read()).decode('utf-8')
    buffer.close()

    # Render the chart in the template
    context = {
        'chart': chart,
        'case1': case1,
        'case2': case2,
        'all_cases': all_cases,
    }

    return render(request, 'pc_app/case/case_comparison.html', context)