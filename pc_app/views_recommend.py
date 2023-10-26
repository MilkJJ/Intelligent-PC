import random
from django.shortcuts import render
import numpy as np
from .models import *
from django.contrib.auth.decorators import login_required
#from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors
from pc_app.templatetags.custom_filters import convert_to_myr

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
    )[:9]

    users = User.objects.all()
    recommended_builds = []
    current_user = request.user

    # KNN for component Metadata
    if request.method == 'POST':
        use_case = request.POST.get('preferred', '')
        total_budget = request.POST.get('max_budget', 99999)
        build_type = request.POST.get('build_type', '')

        total_budget = float(total_budget) / 4.55

        budget_cpu = float(float(total_budget) * 0.2)
        budget_gpu = float(float(total_budget) * 0.3)
        budget_motherboard = float(float(total_budget) * 0.1)
        budget_ram = float(float(total_budget) * 0.1)
        budget_psu = float(float(total_budget) * 0.1)
        budget_storage = float(float(total_budget) * 0.1)
        budget_case = float(float(total_budget) * 0.1)

        meta_cpus = knn_metadata('cpu', current_user, budget_cpu, build_type)
        meta_gpus = knn_metadata('gpu', current_user, budget_gpu, build_type)
        meta_mboards = knn_metadata('mboard', current_user, budget_motherboard, build_type)

        # METADATA RECOMMENDATION
        for mboard in meta_mboards:
            for cpu in meta_cpus:
                for gpu in meta_gpus:
                    recommended_builds.append({'cpu': cpu, 'gpu': gpu, 'mboard': mboard})
            
        metadata_builds = random.sample(recommended_builds, 2)
    
        cpus = CPU.objects.filter(price__lte=total_budget, name__icontains=build_type)
        gpus = GPU.objects.filter(price__lte=budget_gpu)
        mboards = Motherboard.objects.filter(price__lte=budget_motherboard)
        rams = Memory.objects.filter(price__lte=budget_ram)
        psus = PSU.objects.filter(price__lte=budget_psu)
        storages = StorageDrive.objects.filter(price__lte=budget_storage)
        cases = PCase.objects.filter(price__lte=budget_case)

        cpu_pivot_rating = CPUPivotTable.objects.filter(cpu__in=cpus)
        gpu_pivot_rating = GPUPivotTable.objects.filter(gpu__in=gpus)
        ram_pivot_rating = RAMPivotTable.objects.filter(ram__in=rams)
        mboard_pivot_rating = MotherboardPivotTable.objects.filter(mboard__in=mboards)
        storage_pivot_rating = StoragePivotTable.objects.filter(storage__in=storages)
        psu_pivot_rating = PSUPivotTable.objects.filter(psu__in=psus)
        case_pivot_rating = PCasePivotTable.objects.filter(case__in=cases)

        knn_cpus = knn_training_rating(users, cpus, cpu_pivot_rating, current_user, 'cpu')
        knn_gpus = knn_training_rating(users, gpus, gpu_pivot_rating, current_user, 'gpu')
        knn_motherboards = knn_training_rating(users, mboards, mboard_pivot_rating, current_user, 'mboard')

        # KNN MODEL FOR COMPONENT METADATA
        # Get component recommendations within their respective budgets
        recommended_cpus = recommend_ratings_components(knn_cpus)
        recommended_gpus = recommend_ratings_components(knn_gpus)
        recommended_motherboards = recommend_ratings_components(knn_motherboards)

        knn_recommended_builds = []

        # RATINGS RECOMMENDATION
        for cpu in recommended_cpus:
            for gpu in recommended_gpus:
                for mboard in recommended_motherboards:
                    recommended_build = {'cpu': cpu, 'gpu': gpu, 'mboard': mboard}
                    knn_recommended_builds.append(recommended_build)

        random.shuffle(knn_recommended_builds)

    else:
        metadata_builds = []
        knn_recommended_builds = []
    
    context = {
        'rated_items': rated_items,
        'metadata_builds': metadata_builds,
        'knn_rating_builds': knn_recommended_builds,
    }

    return render(request, 'pc_app/home.html', context)


def knn_metadata(component_type, current_user, user_budget, build_type):

    favourited_pc_list = FavouritedPC.objects.filter(user=current_user)
    pc_cart_list = CartItem.objects.filter(user=current_user)

    if pc_cart_list:
        pc = random.choice(pc_cart_list)
    else:
        pc = random.choice(favourited_pc_list)

    if component_type == 'cpu':
        component_data = CPU.objects.filter(price__lte=user_budget, name__icontains=build_type).values('core_count', 'core_clock', 'boost_clock', 'tdp', 'smt')
        selected_features = ['core_count', 'core_clock', 'boost_clock', 'tdp', 'smt']
        pc_attributes = [getattr(pc.cpu, feature) for feature in selected_features]
        model = CPU
    elif component_type == 'gpu':
        component_data = GPU.objects.filter(price__lte=user_budget).values('memory', 'core_clock', 'boost_clock', 'length')
        selected_features = ['memory', 'core_clock', 'boost_clock', 'length']
        pc_attributes = [getattr(pc.gpu, feature) for feature in selected_features]
        model = GPU
    elif component_type == 'mboard':
        component_data = Motherboard.objects.filter(price__lte=user_budget).values('max_memory', 'memory_slots')
        selected_features = ['max_memory', 'memory_slots']
        pc_attributes = [getattr(pc.mboard, feature) for feature in selected_features]  # Define relevant attributes for motherboards
        model = Motherboard

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


def knn_training_rating(users, components, pivot_table_entries, current_user, component_type):
    # For creating and inserting data to pivot table initially with ratings of 0
    # for user in users:
    #     for cpu in components:
    #         random_rating = random.randint(0, 5)
    #         CPUPivotTable.objects.get_or_create(user=user, cpu=cpu, ratings=random_rating)
    
    try:
        favourited_pc_list = FavouritedPC.objects.filter(user=current_user)
        pc_cart_list = CartItem.objects.filter(user=current_user)

        if pc_cart_list:
            pc = random.choice(pc_cart_list)
        else:
            pc = random.choice(favourited_pc_list)

    except FavouritedPC.DoesNotExist:
        print('FavouritedPC objects not found for the current user.')
    except CartItem.DoesNotExist:
        print('CartItem objects not found for the current user.')
    except Exception as e:
        print(f'An unexpected error occurred: {str(e)}')

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
        
        if user_index is not None and component_index is not None:
            ratings_matrix[component_index][user_index] = entry.ratings

    if component_type == 'cpu':
        comp_preference = pc.cpu.id

    elif component_type == 'gpu':
        comp_preference = pc.gpu.id

    elif component_type == 'mboard':
        comp_preference = pc.mboard.id

    # Create a Nearest Neighbors model with cosine similarity metric (you can use other metrics).
    nn_model = NearestNeighbors(metric='cosine', algorithm='brute')
    nn_model.fit(ratings_matrix)

    distances, indices = nn_model.kneighbors(
        ratings_matrix[comp_preference].reshape(1, -1), n_neighbors=3)

    # Retrieve the recommended CPU objects using the indices and distances
    recommended_component_indices = [
        int(i) for i in indices.flatten() if i != comp_preference]
    recommended_component_distances = distances.flatten()[1:]

    recommended_components = [(components[index], distance) for index, distance in zip(
        recommended_component_indices, recommended_component_distances)]

    # Print or return the recommended CPUs.
    # for cpu, distance in recommended_cpus:
    #     print(f"Recommended CPU: {cpu.name}, Distance: {distance}")

    return recommended_components