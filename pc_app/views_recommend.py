import random
from django.shortcuts import render
import numpy as np
from .models import *
from django.contrib.auth.decorators import login_required
#from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors
from pc_app.templatetags.custom_filters import convert_to_myr
from django.db.models import Q

# Create your views here
@login_required(login_url='login')
def HomePage(request):
    # Get the rated build by other users
    rated_items = CartItem.objects.filter(is_purchased=True, orderrating__isnull=False).annotate(
        latest_rating=models.Subquery(
            OrderRating.objects.filter(order_item=models.OuterRef(
                'pk')).order_by('-date_added').values('rating')[:1]
        ),
        latest_comment=models.Subquery(
            OrderRating.objects.filter(order_item=models.OuterRef(
                'pk')).order_by('-date_added').values('comment')[:1]
        )
    )[:9] # Only get 9 ratings displayed

    users = User.objects.all()
    recommended_builds = []
    current_user = request.user

    # KNN for component Metadata
    if request.method == 'POST':
        use_case = request.POST.get('preferred', 'gaming')
        total_budget = request.POST.get('max_budget', 99999)
        build_type = request.POST.get('build_type', 'AMD')

        total_budget = float(total_budget) / 2

        budget_cpu = float(float(total_budget) * 0.2)
        budget_gpu = float(float(total_budget) * 0.3)
        budget_motherboard = float(float(total_budget) * 0.1)
        budget_ram = float(float(total_budget) * 0.1)
        budget_psu = float(float(total_budget) * 0.1)
        budget_storage = float(float(total_budget) * 0.1)
        budget_case = float(float(total_budget) * 0.1)
        
        print('total budget', total_budget)
        print('budget: ', budget_cpu, budget_gpu, budget_motherboard, budget_ram, budget_psu, budget_storage, budget_case)

        try:
            favourited_pc_list = FavouritedPC.objects.filter(user=current_user)
            pc_cart_list = CartItem.objects.filter(user=current_user)
            initial_list = InitialRec.objects.all()

            if pc_cart_list:
                pc = random.choice(pc_cart_list)
            elif favourited_pc_list:
                pc = random.choice(favourited_pc_list)
            else:
                pc = random.choice(initial_list)

        except FavouritedPC.DoesNotExist:
            print('FavouritedPC objects not found for the current user.')
        except CartItem.DoesNotExist:
            print('CartItem objects not found for the current user.')
        except Exception as e:
            print(f'An unexpected error occurred: {str(e)}')
    
        meta_cpus = knn_metadata('cpu', budget_cpu, build_type, pc)
        meta_gpus = knn_metadata('gpu', budget_gpu, build_type, pc)
        meta_mboards = knn_metadata('mboard', budget_motherboard, build_type, pc)
        meta_rams = knn_metadata('ram', budget_ram, build_type, pc)
        meta_psus = knn_metadata('psu', budget_psu, build_type, pc)
        meta_storages = knn_metadata('storage', budget_storage, build_type, pc)
        meta_cases = knn_metadata('case', budget_case, build_type, pc)

        # METADATA RECOMMENDATION
        for mboard in meta_mboards:
            for cpu in meta_cpus:
                for gpu in meta_gpus:
                    for ram in meta_rams:
                        for psu in meta_psus:
                            for storage in meta_storages:
                                for case in meta_cases:
                                    recommended_builds.append({'cpu': cpu, 'gpu': gpu, 'mboard': mboard, 'ram': ram, 'psu':psu ,
                                                               'storage': storage,'case': case})
            
        metadata_builds = random.sample(recommended_builds, 2)

        # USE CASE FILTERING
        if use_case == 'gaming': 
            cpu_mincores = 6
            cpu_maxcores = 8
            cpu_coreclock = 3.5
            cpu_mintdp = 65
            cpu_maxtdp = 105
            cpu_integrated = 1 # To exclude it

            gpu_vram = 4 
            gpu_boostclock = 0 #must have
            gpu_mincoreclock = 1500
            gpu_maxcoreclock = 9999   
            
            ram_capacity = 16
            ram_speed = 3000

        elif use_case == 'content_creation': 
            cpu_mincores = 1
            cpu_maxcores = 8
            cpu_coreclock = 3.5
            cpu_mintdp = 105
            cpu_maxtdp = 99999
            cpu_integrated = 1 # To exclude it

            gpu_vram = 8
            gpu_boostclock = 0 #to exclude 0
            gpu_mincoreclock = 1500
            gpu_maxcoreclock = 9999       
            
            ram_capacity = 32
            ram_speed = 3200

        elif use_case == 'general':
            cpu_mincores = 4
            cpu_maxcores = 6
            cpu_coreclock = 3.0
            cpu_mintdp = 0
            cpu_maxtdp = 65
            cpu_integrated = None # To NOT exclude it

            gpu_vram = 2 #lower than 4
            gpu_mincoreclock = 1000
            gpu_boostclock = 1
            gpu_maxcoreclock = 1500

            ram_capacity = 8
            ram_speed = 2000

        # KNN RATING MATRIX 
        cpus = CPU.objects.filter(Q(price__lte=budget_cpu, name__icontains=build_type, 
                                    core_count__gte=cpu_mincores, core_count__lte=cpu_maxcores, 
                                    core_clock__gte=cpu_coreclock, 
                                    tdp__gte=cpu_mintdp, tdp__lte=cpu_maxtdp) | Q(id=pc.cpu.id)).exclude(graphics=cpu_integrated)
        
        gpus = GPU.objects.filter(Q(price__lte=budget_gpu, core_clock__gte=gpu_mincoreclock, core_clock__lte=gpu_maxcoreclock,
                                    memory__gte=gpu_vram) | Q(id=pc.gpu.id)).exclude(boost_clock=gpu_boostclock)
        
        rams = Memory.objects.filter(Q(price__lte=budget_ram, memory_size__gte=ram_capacity, 
                                       speed_mhz__gte=ram_speed) | Q(id=pc.ram.id))

        mboards = Motherboard.objects.filter(Q(price__lte=budget_motherboard) | Q(id=pc.mboard.id))
        psus = PSU.objects.filter(Q(price__lte=budget_psu) | Q(id=pc.psu.id))
        storages = StorageDrive.objects.filter(Q(price__lte=budget_storage, type='SSD') | Q(id=pc.storage.id))
        cases = PCase.objects.filter(Q(price__lte=budget_case) | Q(id=pc.case.id))

        cpu_pivot_rating = CPUPivotTable.objects.filter(cpu__in=cpus)
        gpu_pivot_rating = GPUPivotTable.objects.filter(gpu__in=gpus)
        ram_pivot_rating = RAMPivotTable.objects.filter(ram__in=rams)
        mboard_pivot_rating = MotherboardPivotTable.objects.filter(mboard__in=mboards)
        storage_pivot_rating = StoragePivotTable.objects.filter(storage__in=storages)
        psu_pivot_rating = PSUPivotTable.objects.filter(psu__in=psus)
        case_pivot_rating = PCasePivotTable.objects.filter(case__in=cases)

        knn_cpus = knn_training_rating(users, cpus, cpu_pivot_rating, 'cpu', pc)
        knn_gpus = knn_training_rating(users, gpus, gpu_pivot_rating, 'gpu', pc)
        knn_rams = knn_training_rating(users, rams, ram_pivot_rating, 'ram', pc)
        knn_motherboards = knn_training_rating(users, mboards, mboard_pivot_rating, 'mboard', pc)
        knn_storages = knn_training_rating(users, storages, storage_pivot_rating, 'storage', pc)
        knn_psus = knn_training_rating(users, psus, psu_pivot_rating, 'psu', pc)
        knn_cases = knn_training_rating(users, cases, case_pivot_rating, 'case', pc)

        knn_recommended_builds = []

        if knn_cpus and knn_gpus and knn_rams and knn_motherboards and knn_storages and knn_psus and knn_cases:
            # KNN MODEL FOR COMPONENT METADATA
            # Get component recommendations within their respective budgets
            recommended_cpus = recommend_ratings_components(knn_cpus)
            recommended_gpus = recommend_ratings_components(knn_gpus)
            recommended_motherboards = recommend_ratings_components(knn_motherboards)
            recommended_rams = recommend_ratings_components(knn_rams)
            recommended_storages = recommend_ratings_components(knn_storages)
            recommended_psus = recommend_ratings_components(knn_psus)
            recommended_cases = recommend_ratings_components(knn_cases)

            # RATINGS RECOMMENDATION
            # 3 USE CASE SCENARIO
            for mboard in recommended_motherboards:
                for cpu in recommended_cpus:
                    for gpu in recommended_gpus:
                        for ram in recommended_rams:
                            for storage in recommended_storages:
                                for psu in recommended_psus:
                                    for case in recommended_cases:
                                        recommended_build = {'cpu': cpu, 'gpu': gpu, 'mboard': mboard, 'ram': ram, 'psu':psu ,
                                                                            'storage': storage,'case': case}
                                        knn_recommended_builds.append(recommended_build)

            random.shuffle(knn_recommended_builds)

        else:
            knn_recommended_builds = []

    else:
        metadata_builds = []
        knn_recommended_builds = []

    context = {
        'rated_items': rated_items,
        'metadata_builds': metadata_builds,
        'knn_rating_builds': knn_recommended_builds,
    }

    return render(request, 'pc_app/home.html', context)


def knn_metadata(component_type, user_budget, build_type, pc):

    if component_type == 'cpu':
        component_data = CPU.objects.filter(Q(price__lte=user_budget, name__icontains=build_type) | Q(id=pc.cpu.id)).values('core_count', 'core_clock', 'boost_clock', 'tdp', 'smt')
        selected_features = ['core_count', 'core_clock', 'boost_clock', 'tdp', 'smt']
        pc_attributes = [getattr(pc.cpu, feature) for feature in selected_features]
        model = CPU

    elif component_type == 'gpu':
        component_data = GPU.objects.filter(Q(price__lte=user_budget) | Q(id=pc.gpu.id)).values('memory', 'core_clock', 'boost_clock', 'length')
        selected_features = ['memory', 'core_clock', 'boost_clock', 'length']
        pc_attributes = [getattr(pc.gpu, feature) for feature in selected_features]
        model = GPU

    elif component_type == 'mboard':
        component_data = Motherboard.objects.filter(Q(price__lte=user_budget) | Q(id=pc.mboard.id)).values('max_memory', 'memory_slots')
        selected_features = ['max_memory', 'memory_slots']
        pc_attributes = [getattr(pc.mboard, feature) for feature in selected_features]  # Define relevant attributes for motherboards
        model = Motherboard

    elif component_type == 'ram':
        component_data = Memory.objects.filter(Q(price__lte=user_budget) | Q(id=pc.ram.id)).values('speed_mhz', 'num_modules', 'memory_size')
        selected_features = ['speed_mhz', 'num_modules', 'memory_size']
        pc_attributes = [getattr(pc.ram, feature) for feature in selected_features]  # Define relevant attributes for rams
        model = Memory

    elif component_type == 'psu':
        component_data = PSU.objects.filter(Q(price__lte=user_budget) | Q(id=pc.psu.id)).values('wattage', 'price')
        selected_features = ['wattage', 'price']
        pc_attributes = [getattr(pc.psu, feature) for feature in selected_features]  # Define relevant attributes for motherboards
        model = PSU

    elif component_type == 'storage':
        component_data = StorageDrive.objects.filter(Q(price__lte=user_budget) | Q(id=pc.storage.id)).values('capacity', 'cache')
        selected_features = ['capacity', 'cache']
        pc_attributes = [getattr(pc.storage, feature) for feature in selected_features]  # Define relevant attributes for motherboards
        model = StorageDrive

    elif component_type == 'case':
        component_data = PCase.objects.filter(Q(price__lte=user_budget) | Q(id=pc.case.id)).values('external_525_bays')
        selected_features = ['external_525_bays']
        pc_attributes = [getattr(pc.case, feature) for feature in selected_features]  # Define relevant attributes for motherboards
        model = PCase

    component_matrix = np.array([list(component.values()) for component in component_data])
    #cosine_sim = cosine_similarity(component_matrix, component_matrix)
    knn = NearestNeighbors(n_neighbors=2, algorithm='auto') 
    knn.fit(component_matrix)

    user_features = np.array(pc_attributes, dtype=float).reshape(1, -1)

    distances, indices = knn.kneighbors(user_features)

    #print(component_type, 'metadata: ', indices[0])

    recommended_components = [model.objects.get(pk=index+1) for index in indices[0]]

    return recommended_components

    
def recommend_ratings_components(knn_components):
    # Sort the recommended components by their distance (similarity) scores
    knn_components.sort(key=lambda x: x[1])

    recommended_components = []

    for component, distance in knn_components:
        recommended_components.append(component)
        if len(recommended_components) == 2:
            break

    return recommended_components


def knn_training_rating(users, components, pivot_table_entries, component_type, pc):
    # For creating and inserting data to pivot table initially with ratings of 0
    # for user in users:
    #     for cpu in components:
    #         random_rating = random.randint(0, 5)
    #         CPUPivotTable.objects.get_or_create(user=user, cpu=cpu, ratings=random_rating)

    # Create dictionaries to map user and CPU IDs to their indices
    user_id_to_index = {user.id: i for i, user in enumerate(users)}
    component_id_to_index = {component.id: i for i,
                             component in enumerate(components)}

    # Create a matrix to represent user ratings for CPUs.
    # Each row represents a user, and each column represents a CPU.
    user_count = len(users)
    components_count = len(components)
    ratings_matrix = np.zeros((components_count, user_count))

    # Fill the ratings matrix with ratings from the PivotTable.
    
    for entry in pivot_table_entries:
        user_index = user_id_to_index.get(entry.user.id)
        if component_type == 'cpu':
            component_index = component_id_to_index.get(entry.cpu.id)

        elif component_type == 'gpu':
            component_index = component_id_to_index.get(entry.gpu.id)

        elif component_type == 'mboard':
            component_index = component_id_to_index.get(entry.mboard.id)

        elif component_type == 'ram':
            component_index = component_id_to_index.get(entry.ram.id)

        elif component_type == 'psu':
            component_index = component_id_to_index.get(entry.psu.id)

        elif component_type == 'storage':
            component_index = component_id_to_index.get(entry.storage.id)

        elif component_type == 'case':
            component_index = component_id_to_index.get(entry.case.id)
        
        if user_index is not None and component_index is not None:
            ratings_matrix[component_index][user_index] = entry.ratings

    if component_type == 'cpu':
        comp_preference = component_id_to_index.get(pc.cpu.id)

    elif component_type == 'gpu':
        comp_preference = component_id_to_index.get(pc.gpu.id)

    elif component_type == 'mboard':
        comp_preference = component_id_to_index.get(pc.mboard.id)

    elif component_type == 'ram':
        comp_preference = component_id_to_index.get(pc.ram.id)

    elif component_type == 'psu':
        comp_preference = component_id_to_index.get(pc.psu.id)

    elif component_type == 'storage':
        comp_preference = component_id_to_index.get(pc.storage.id)

    elif component_type == 'case':
        comp_preference = component_id_to_index.get(pc.case.id)

    print(component_type, 'id:', comp_preference)

    # Create a Nearest Neighbors model with cosine similarity metric (you can use other metrics).
    nn_model = NearestNeighbors(metric='cosine', algorithm='brute')
    nn_model.fit(ratings_matrix)

    try:
        distances, indices = nn_model.kneighbors(ratings_matrix[comp_preference].reshape(1, -1), n_neighbors=4)

        # Retrieve the recommended CPU objects using the indices and distances
        recommended_component_indices = [
            int(i) for i in indices.flatten() if i != comp_preference]
        recommended_component_distances = distances.flatten()[1:]

        recommended_components = [(components[index], distance) for index, distance in zip(
            recommended_component_indices, recommended_component_distances)]
    
    except Exception as e:
        print(f'No build found within budget! {str(e)}')
        recommended_components = None

    # Print or return the recommended CPUs.
    # for cpu, distance in recommended_cpus:
    #     print(f"Recommended CPU: {cpu.name}, Distance: {distance}")

    return recommended_components