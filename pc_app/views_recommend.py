import random
from django.shortcuts import render
import numpy as np
from .models import *
from django.contrib.auth.decorators import login_required
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors
from pc_app.templatetags.custom_filters import convert_to_myr
import time

# Create your views here.
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

    # KNN MODEL
    users = User.objects.all()
    cpus = CPU.objects.all()
    gpus = GPU.objects.all()
    mboards = Motherboard.objects.all()
    pivot_table_entries = CPUPivotTable.objects.all()

    knn_cpus = knn_training(users, cpus, pivot_table_entries)
    knn_gpus = knn_training(users, gpus, pivot_table_entries)
    knn_motherboards = knn_training(users, mboards, pivot_table_entries)

    # Retrieve the budget from the request (adjust the default value as needed)
    total_budget = request.GET.get('max_budget', 5000)
    build_type = request.GET.get('build_type', '')

    # Calculate budget allocations for each component
    budget_cpu = float(float(total_budget) * 0.4)
    budget_gpu = float(float(total_budget) * 0.8)
    budget_motherboard = float(float(total_budget) * 0.4)

    print(budget_cpu, budget_gpu, budget_motherboard)
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

    # COSINE SIMILARITY
    use_case = request.GET.get('preferred', '')
    max_budget_str = request.GET.get('max_budget', 10000)

    if max_budget_str:
        max_price = float(max_budget_str)

    favourited_pc_list = FavouritedPC.objects.all()
    in_cart_list = CartItem.objects.all()

    # recommended_cpu_list  = cosine_recommend(favourited_pc_list, in_cart_list, 'cpu', use_case, build_type)
    # recommended_gpu_list  = cosine_recommend(favourited_pc_list, in_cart_list, 'gpu', use_case)
    # recommended_motherboard_list  = cosine_recommend(favourited_pc_list, in_cart_list, 'motherboard')

    # recommended_builds = []

    # for favourited_pc, recommended_cpus in recommended_cpu_list:
    #     for cpu in recommended_cpus:
    #         for favourited_pc, recommended_motherboards in recommended_motherboard_list:
    #             for motherboard in recommended_motherboards:
    #                 # if cpu.socket == motherboard.socket:
    #                 for favourited_pc, recommended_gpus in recommended_gpu_list:
    #                     for gpu in recommended_gpus:
    #                         # Check for compatibility between CPU and GPU (you can add more compatibility checks here)
    #                         if min_price and max_price:
    #                             build_price = cpu.price + gpu.price + motherboard.price
    #                             if build_price >= min_price and build_price <= max_price:
    #                                 # Create a recommended build tuple and add it to the list
    #                                 recommended_build = (motherboard, cpu, gpu)
    #                                 recommended_builds.append(recommended_build)
    #                         else:
    #                             recommended_build = (motherboard, cpu, gpu)
    #                             recommended_builds.append(recommended_build)

    # # Shuffle the recommended builds to randomize the order
    # random.shuffle(recommended_builds)

    # # Select and display the top 3 random builds
    # top_3_random_builds = recommended_builds[:3]
    # recommended_builds = []

    # for recommended_mboard, recommended_cpu, recommended_gpu in top_3_random_builds:
    #     # Create or update the RecommendedBuild to Database
    #     # recommended_build, created = RecommendedBuild.objects.get_or_create(
    #     #     cpu=recommended_cpu, gpu=recommended_gpu, mboard=recommended_mboard
    #     # )

    #     recommended_build = RecommendedBuild(
    #         cpu=recommended_cpu, gpu=recommended_gpu, mboard=recommended_mboard
    #     )

    #     # Calculate and update total_price
    #     recommended_build.total_price = (
    #         recommended_cpu.price + recommended_gpu.price + recommended_mboard.price
    #     )
    #     # recommended_build.save()
    #     recommended_builds.append(recommended_build)

    context = {
        'knn_recommended_builds': knn_recommended_builds,
        'rated_items': rated_items,
        # 'recommended_builds': recommended_builds,
    }

    return render(request, 'pc_app/home.html', context)

    # # Run this function When a user rates a build (CPU, GPU) for all pivot table
    # user_id = 1  # current logged in user from the order model
    # cpu_name = "CPU1"  # this is from the cart order model
    # new_rating = 4.5  # This is from the cart order rating model

    # pivot_record = PivotTable.objects.get(user_id=user_id, cpu__name=cpu_name)
    # pivot_record.rating = new_rating
    # pivot_record.save()


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


def knn_training(users, components, pivot_table_entries):
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


# COSINE HTML
#   <div class="recommended-builds-container">
#     {% if recommended_builds %}
#     {% for recommended_build in recommended_builds %}
#     <div class="recommended-build">
#       <p><strong>Build {{ forloop.counter }}:</strong></p>
#       <p><strong>CPU:</strong> {{ recommended_build.cpu.name }}</p>
#       <p><strong>GPU:</strong> {{ recommended_build.gpu.name }} - {{ recommended_build.gpu.chipset }}</p>
#       <p><strong>Motherboard:</strong> {{ recommended_build.mboard.name }}</p>
#       <p><strong>Total Price:</strong> ${{ recommended_build.total_price }}</p>
#     </div>
#     {% endfor %}
#     {% else %}
#     <p>No Build found within this budget!</p>


def calculate_cosine_similarity(target_component, other_component, component_type):
    # Convert component features to a numerical array
    # favourited_pc_features = [
    #     favourited_pc.cpu.core_count, favourited_pc.cpu.core_clock, favourited_pc.cpu.boost_clock,
    #     favourited_pc.gpu.core_clock, favourited_pc.gpu.boost_clock,
    #     favourited_pc.mboard.max_memory, favourited_pc.mboard.memory_slots
    # ]
    columns_to_encode = None

    if other_component and component_type == 'cpu':
        favourited_pc_features = [target_component.cpu.core_count,
                                  target_component.cpu.core_clock, target_component.cpu.boost_clock]
        other_features = [other_component.core_count,
                          other_component.core_clock, other_component.boost_clock]

    elif other_component and component_type == 'gpu':
        favourited_pc_features = [
            target_component.gpu.core_clock, target_component.gpu.boost_clock]
        other_features = [other_component.core_clock,
                          other_component.boost_clock]

    elif other_component and component_type == 'motherboard':
        favourited_pc_features = [
            target_component.mboard.max_memory, target_component.mboard.memory_slots]
        other_features = [other_component.max_memory,
                          other_component.memory_slots]

    # # Normalize the features
    # scaler = StandardScaler()
    # favourited_pc_features = scaler.fit_transform([favourited_pc_features])
    # other_features = scaler.transform([other_features])

    # if columns_to_encode:
    #     for col_idx in columns_to_encode:
    #         label_encoder = LabelEncoder()

    #         # Fit label encoder on all values
    #         all_values = np.concatenate([favourited_pc_features[:, col_idx], other_features[:, col_idx]])
    #         label_encoder.fit(all_values)

    #         # Transform values to numeric labels for favourited_pc_features
    #         favourited_pc_features[:, col_idx] = label_encoder.transform(favourited_pc_features[:, col_idx])

    #         # Transform values to numeric labels for other_features
    #         other_features[:, col_idx] = label_encoder.transform(other_features[:, col_idx])

    favourited_pc_features = np.array(favourited_pc_features).reshape(1, -1)
    other_features = np.array(other_features).reshape(1, -1)

    # Calculate cosine similarity
    similarity_score = cosine_similarity(
        favourited_pc_features, other_features)

    return columns_to_encode, similarity_score[0][0]


def cosine_recommend(favourited_pc_list, in_cart_list, component_type, use_case=None, build_type=None):

    if component_type == 'cpu':
        all_components = CPU.objects.all()  # CPU.objects.get(id=42)

    elif component_type == 'gpu':
        all_components = GPU.objects.all()  # GPU.objects.get(id=904)

    elif component_type == 'motherboard':
        all_components = Motherboard.objects.all()  # Motherboard.objects.get(id=42)

    recommended_comp_list = []

    # Cosine with cart item & favourited pc
    # for in_cart, favourited_pc in zip(in_cart_list, favourited_pc_list):
    start_time = time.perf_counter()

    for favourited_pc in favourited_pc_list:
        similarity_scores = []

        for comp in all_components:
            if favourited_pc:
                columns_to_encode, similarity = calculate_cosine_similarity(
                    favourited_pc, comp, component_type)
                similarity_scores.append((comp, similarity))
            # if in_cart:
            #     print(in_cart)
            #     columns_to_encode, similarity = calculate_cosine_similarity(in_cart, comp, component_type)
            #     similarity_scores.append((comp, similarity))

        # Sort the components based on similarity scores from most similar to least similar
        if similarity_scores:
            sorted_components = sorted(
                similarity_scores, key=lambda x: x[1], reverse=True)
        else:
            sorted_components = random.sample(all_components, 5)

        # K = 5

        # # Select the top K items as recommendations
        # recommendations = [item for item, _ in similarity_scores[:K]]

        # return recommendations

        top_5_comps = []

        for comp, similarity in sorted_components:

            if len(top_5_comps) == 5:
                break

            if component_type == 'cpu':
                if build_type in comp.name.lower():
                    # Gaming
                    if use_case == 'gaming' and comp.core_count >= 7 and comp.core_count <= 8 and comp.core_clock >= 3.5:
                        # Append CPU that meets the criteria
                        top_5_comps.append(comp)
                    # Content Creation:
                    elif use_case == 'content_creation' and comp.core_count >= 8 and comp.core_clock >= 3.5:
                        # Append CPU that meets the criteria
                        top_5_comps.append(comp)
                    # General
                    elif use_case == 'general' and comp.core_count >= 4 and comp.core_count <= 6 and comp.core_clock <= 3.5:
                        # Append CPU that meets the criteria
                        top_5_comps.append(comp)

            if component_type == 'gpu':
                if use_case == 'gaming' and comp.memory >= 4 and comp.core_clock >= 1500:
                    # Append CPU that meets the criteria
                    top_5_comps.append(comp)
                elif use_case == 'content_creation' and comp.memory >= 8 and comp.core_clock >= 1500:
                    # Append CPU that meets the criteria
                    top_5_comps.append(comp)
                elif use_case == 'general' and comp.memory >= 2 and comp.memory <= 4 and comp.core_clock <= 1500:
                    # Append CPU that meets the criteria
                    top_5_comps.append(comp)

            if component_type == 'motherboard':
                top_5_comps.append(comp)

        recommended_comp_list.append((favourited_pc, top_5_comps))

    end_time = time.perf_counter()
    elapsed_time_ms = (end_time - start_time) * 1000  # Convert to milliseconds
    print(f"Function took {elapsed_time_ms} nanoseconds to execute")

    return recommended_comp_list
