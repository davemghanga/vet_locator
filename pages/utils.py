import logging
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from django.conf import settings

logger = logging.getLogger(__name__)

def get_location_name(coordinates):
    """
    Reverse geocode coordinates to get a human-readable location name.
    """
    logger.debug("Received coordinates for geocoding: %s", coordinates)
    geolocator = Nominatim(user_agent="vet_locator",timeout=10)
    try:
        location = geolocator.reverse(coordinates, exactly_one=True)
        return location.address if location else "Unknown Location"
    except GeocoderTimedOut:
        logger.error("Geocoding timed out for coordinates: %s", coordinates)
        return "Unknown Location"
    except Exception as e:
        logger.error("Error fetching location name: %s", e)
        return "Unknown Location"
    


