import random
from django.shortcuts import render
import numpy as np
from .models import *
from django.contrib.auth.decorators import login_required
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors
from pc_app.templatetags.custom_filters import convert_to_myr
import time
from django.http import JsonResponse
from sklearn.model_selection import train_test_split

# Create your views here
def knn_training(component_type, current_user):
    try:
        favourited_pc_list = FavouritedPC.objects.filter(user=current_user)
        pc_cart_list = CartItem.objects.filter(user=current_user)

        if favourited_pc_list:
            pc = random.choice(favourited_pc_list)
        else:
            pc = random.choice(pc_cart_list)
    except (FavouritedPC.DoesNotExist, CartItem.DoesNotExist):
                    print('NO FAVOURITE AND CART')


    if component_type == 'cpu':
        component_data = CPU.objects.all().values('core_count', 'core_clock', 'boost_clock', 'tdp', 'smt')  # CPU.objects.get(id=42)
        selected_features = ['core_count', 'core_clock', 'boost_clock', 'tdp', 'smt']
        pc_attributes = [getattr(pc.cpu, feature) for feature in selected_features]

    elif component_type == 'gpu':
        component_data = GPU.objects.all().values('memory', 'core_clock', 'boost_clock', 'length')
        # Extract user's GPU features from the form
        selected_features = ['memory', 'core_clock', 'boost_clock', 'length']
        pc_attributes = [getattr(pc.gpu, feature) for feature in selected_features]

    elif component_type == 'motherboard':
        component_data = Motherboard.objects.all()

    # Create a numpy array from the data
    component_matrix = np.array([list(component.values()) for component in component_data])

    # Calculate cosine similarity
    cosine_sim = cosine_similarity(component_matrix, component_matrix)

    # Initialize KNN model
    knn = NearestNeighbors(n_neighbors=10, algorithm='auto') # metric='cosine'
    knn.fit(component_matrix)

    # If the form is empty, use the attributes from FavouritedPC
    user_features = []

    user_features.extend(pc_attributes)

    user_features = np.array(user_features, dtype=float).reshape(1, -1)

    # Find K-nearest neighbors
    distances, indices = knn.kneighbors(user_features)

    print('Distancs for', component_type, distances)

    # Get recommended GPUs based on indices
    if component_type == 'cpu':
        recommended_component = [CPU.objects.get(pk=index) for index in indices[0]]

    elif component_type == 'gpu':
        recommended_component = [GPU.objects.get(pk=index) for index in indices[0]]

    
    return recommended_component

    #return render(request, 'pc_app/recommend_gpu.html', {'recommendations': recommendations})  # Create a template for the recommendation form


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

    # KNN FOR COMPONENT ATTRIBUTES
    recommended_builds = []
    current_user = request.user
    if request.method == 'GET':
        kn_cpus = knn_training('cpu', current_user)
        kn_gpus = knn_training('gpu', current_user)

        total_budget = request.GET.get('max_budget', 5000)
        build_type = request.GET.get('build_type', '')

        budget_cpu = float(float(total_budget) * 0.5)
        budget_gpu = float(float(total_budget) * 0.8)
        budget_motherboard = float(float(total_budget) * 0.4)

        for cpu in kn_cpus:
            if convert_to_myr(cpu.price) <= budget_cpu:
                if build_type in cpu.name.lower():
                    for gpu in kn_gpus:
                        recommended_builds.append({'cpu': cpu, 'gpu': gpu})
            
        selected_builds = random.sample(recommended_builds, 2)


    # KNN MODEL FOR RATING
    users = User.objects.all()
    cpus = CPU.objects.all()
    gpus = GPU.objects.all()
    mboards = Motherboard.objects.all()
    pivot_table_entries = CPUPivotTable.objects.all()

    knn_cpus = knn_training_rating(users, cpus, pivot_table_entries)
    knn_gpus = knn_training_rating(users, gpus, pivot_table_entries)
    knn_motherboards = knn_training_rating(users, mboards, pivot_table_entries)

    # Get component recommendations within their respective budgets
    recommended_cpus = recommend_components(knn_cpus, budget_cpu, build_type)
    recommended_gpus = recommend_components(knn_gpus, budget_gpu)
    recommended_motherboards = recommend_components(knn_motherboards, budget_motherboard)

    knn_recommended_builds = []

    # Loop through budget and compatibility filtered components
    for cpu in recommended_cpus:
        for gpu in recommended_gpus:
            for mboard in recommended_motherboards:
                recommended_build = {'cpu': cpu, 'mboard': mboard, 'gpu': gpu}
                knn_recommended_builds.append(recommended_build)

    random.shuffle(knn_recommended_builds)

    context = {
        'rated_items': rated_items,
        'recommended_builds': selected_builds,
        'knn_recommended_builds': knn_recommended_builds,
    }

    return render(request, 'pc_app/home.html', context)


def recommend_components(knn_components, budget, build_type=None):
    # Sort the recommended components by their distance (similarity) scores
    knn_components.sort(key=lambda x: x[1])

    recommended_components = []

    for component, distance in knn_components:
        if build_type is None:
            if convert_to_myr(component.price) <= budget:
                recommended_components.append(component)
                if len(recommended_components) == 2:
                    break
        else:
            if build_type in component.name.lower():
                if convert_to_myr(component.price) <= budget:
                    recommended_components.append(component)
                    if len(recommended_components) == 2:
                        break

    return recommended_components


def knn_training_rating(users, components, pivot_table_entries):
    # For creating and inserting data to pivot table initially with ratings of 0
    # if type == 'cpu':
    #     for user in users:
    #         for cpu in components:
    #             random_rating = random.randint(0, 5)
    #             CPUPivotTable.objects.get_or_create(user=user, cpu=cpu, ratings=random_rating)

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
        component_index = component_id_to_index.get(entry.cpu.id)

        if user_index is not None and component_index is not None:
            ratings_matrix[component_index][user_index] = entry.ratings

    # Create a Nearest Neighbors model with cosine similarity metric (you can use other metrics).
    nn_model = NearestNeighbors(metric='cosine', algorithm='brute')
    nn_model.fit(ratings_matrix)

    # Choose a user for whom you want to recommend CPUs.
    # You can change this index to the desired user.
    user_index_to_recommend = 3

    # Get the nearest neighbors (similar users) for the chosen user.
    num_recommendations = 492

    distances, indices = nn_model.kneighbors(
        ratings_matrix[user_index_to_recommend].reshape(1, -1), n_neighbors=num_recommendations+1)

    # Retrieve the recommended CPU objects using the indices and distances
    recommended_component_indices = [
        int(i) for i in indices.flatten() if i != user_index_to_recommend]
    recommended_component_distances = distances.flatten()[1:]

    recommended_components = [(components[index], distance) for index, distance in zip(
        recommended_component_indices, recommended_component_distances)]

    # Print or return the recommended CPUs.
    # for cpu, distance in recommended_cpus:
    #     print(f"Recommended CPU: {cpu.name}, Distance: {distance}")

    return recommended_components