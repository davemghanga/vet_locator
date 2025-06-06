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
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
import google.generativeai as genai
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Avg
from vets.models import Rating 

def contact_view(request):
    return render(request, 'contact.html')


def services(request):
    return render(request, 'services.html')

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

    vet = get_object_or_404(CustomUser, id=vet_id, user_type='vet')

    # Ensure the user has location data
    user = request.user
    if user.location is None:
        return render(request, "vets/vet_details.html", {"error": "User location not set."})

    # Coordinates
    lat = user.location.y
    lon = user.location.x
    vet_coordinates = (vet.location.y, vet.location.x)
    distance = round(geodesic((lat, lon), vet_coordinates).km, 2)
    location_name = get_location_name(vet_coordinates)

    # Ratings
    ratings = Rating.objects.filter(vet=vet)
    average_rating = ratings.aggregate(Avg('rating'))['rating__avg'] or 0
    rating_count = ratings.count()

    context = {
        "vet": vet,
        "distance": distance,
        "coordinates": f"{vet_coordinates[0]}, {vet_coordinates[1]}",
        "location_name": location_name,
        "average_rating": round(average_rating, 1),
        "rating_count": rating_count,
    }

    # Cache the result for 5 minutes
    cache.set(cache_key, context, timeout=300)

    return render(request, "vets/vet_details.html", context)



@login_required(login_url='login')
def vet_reviews(request, vet_id):
    vet = get_object_or_404(CustomUser, id=vet_id, user_type='vet')
    reviews = Rating.objects.filter(vet=vet).select_related('pet_owner', 'appointment')  # Get reviews with related pet_owner and appointment

    return render(request, 'vets/vet_reviews.html', {'vet': vet, 'reviews': reviews})








