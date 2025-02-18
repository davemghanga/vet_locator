from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from geopy.geocoders import Nominatim
from .models import DogProfile
from .forms import DogProfileForm
from accounts.models import CustomUser
from geopy.distance import geodesic
from django.http import JsonResponse
from django.core.cache import cache
from .utils import get_location_name
import logging

@login_required(login_url='login')
def dog_profile_detail(request, id):
    profile = get_object_or_404(DogProfile, id=id, owner=request.user)
    return render(request, 'dog_profiles/details.html', {'profile': profile})

@login_required(login_url='login')
def dog_profile_create(request):
    if request.method == 'POST':
        form = DogProfileForm(request.POST, request.FILES)
        if form.is_valid():
            dog_profile = form.save(commit=False)
            dog_profile.owner = request.user
            dog_profile.save()
            return redirect('owner_dashboard')
    else:
        form = DogProfileForm()
    return render(request, 'dog_profiles/create.html', {'form': form})

@login_required(login_url='login')
def dog_profile_update(request, id):
    profile = get_object_or_404(DogProfile, id=id, owner=request.user)
    if request.method == 'POST':
        form = DogProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('dog_profile_detail', id=profile.id)
    else:
        form = DogProfileForm(instance=profile)
    return render(request, 'dog_profiles/update.html', {'form': form})

@login_required(login_url='login')
def dog_profile_delete(request, id):
    profile = get_object_or_404(DogProfile, id=id, owner=request.user)
    if request.method == 'POST':
        profile.delete()
        return redirect('owner_dashboard')
    return render(request, 'dog_profiles/confirm_delete.html', {'profile': profile})


logger = logging.getLogger(__name__)

@login_required(login_url='login')
def find_vets(request):
    """
    Find vets near the logged-in user's location.
    """
    user = request.user

    # Check if the user has a location set
    if user.location is None:
        return render(request, "vets/find_vet.html", {"error": "User location not set."})

    # Extract latitude and longitude from the user's location
    lat = user.location.y  # Latitude
    lon = user.location.x  # Longitude

    logger.debug("Using user's coordinates: lat=%s, lon=%s", lat, lon)

    # Create a unique cache key based on the coordinates
    cache_key = f"vets_near_{lat}_{lon}"
    
    # Try to get the cached result
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        logger.debug("Returning cached result for coordinates: %s", cache_key)
        return render(request, "vets/find_vet.html", cached_result)

    # Create a Point object for GeoDjango (lon, lat) - Correct order for GeoDjango
    user_point = Point(lon, lat, srid=4326)
    logger.debug("Searching for vets near point: %s", user_point)

    # Query vets near the user's location
    vets = CustomUser.objects.filter(
        user_type="vet",
        location__isnull=False
    ).annotate(
        distance=Distance("location", user_point)
    ).order_by("distance")

    logger.debug("Found %d vets in database", vets.count())

    if not vets.exists():
        logger.info("No vets found near user location: %s", user_point)
        return render(request, "vets/find_vet.html", {
            "user_location": get_location_name((lat, lon)),
            "user_coordinates": f"{lat}, {lon}",
            "nearest_vet": None,
            "other_vets": []
        })

    # Prepare the list of vets with distances
    vet_list = []
    for vet in vets:
        logger.debug("Processing vet: id=%s, coordinates=(%s, %s)", 
                   vet.id, vet.location.y, vet.location.x)

        # Calculate distance in kilometers using geodesic (lat, lon)
        vet_distance = geodesic(
            (lat, lon),  # User coordinates (latitude, longitude)
            (vet.location.y, vet.location.x)  # Vet coordinates (latitude, longitude)
        ).km

        logger.debug("Distance to vet %s: %s km", vet.id, vet_distance)

        vet_list.append({
            "id": vet.id,
            "name": f"{vet.first_name} {vet.last_name}",
            "coordinates": f"{vet.location.y}, {vet.location.x}",
            "location_name": get_location_name((vet.location.y, vet.location.x)),
            "distance_km": round(vet_distance, 2)
        })

    # Prepare context for the template
    context = {
        "user_location": get_location_name((lat, lon)),
        "user_coordinates": f"{lat}, {lon}",
        "nearest_vet": vet_list[0] if vet_list else None,
        "other_vets": vet_list[1:] if len(vet_list) > 1 else []
    }

    # Cache the result for future requests
    cache.set(cache_key, context, timeout=300)  # Cache for 5 minutes

    logger.debug("Rendering template with context: %s", context)
    return render(request, "vets/find_vet.html", context)



@login_required(login_url='login')
def vet_details(request, vet_id):
    # Create a unique cache key for the vet details
    cache_key = f"vet_details_{vet_id}"
    cached_vet_details = cache.get(cache_key)

    if cached_vet_details is not None:
        return render(request, "vets/vet_details.html", cached_vet_details)

    vet = get_object_or_404(CustomUser , id=vet_id, user_type='vet')  # Ensure it's a vet

    # Get the user's location
    user = request.user
    if user.location is None:
        return render(request, "vets/vet_details.html", {"error": "User  location not set."})

    lat = user.location.y  # User's latitude
    lon = user.location.x  # User's longitude

    # Calculate distance to the vet
    vet_coordinates = (vet.location.y, vet.location.x)  # Vet's coordinates
    distance = round(geodesic((lat, lon), vet_coordinates).km, 2)

    # Get the location name for the vet
    location_name = get_location_name(vet_coordinates)

    # Prepare the context for rendering
    context = {
        "vet": vet,
        "distance": distance,
        "coordinates": f"{vet_coordinates[0]}, {vet_coordinates[1]}",
        "location_name": location_name
    }

    # Cache the result for future requests
    cache.set(cache_key, context, timeout=300)  # Cache for 5 minutes

    return render(request, "vets/vet_details.html", context)

