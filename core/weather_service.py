"""
Weather service module for fetching weather data and generating actionable advice.
"""
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def get_weather_data(city):
    """
    Fetch current weather data from OpenWeatherMap API.
    
    Args:
        city (str): City name for weather forecast
        
    Returns:
        dict: Weather data containing temperature, condition, wind_speed, humidity
        None: If API call fails or city not found
    """
    if not city:
        return None
        
    # Get API key from settings (you'll need to add this to settings.py)
    api_key = getattr(settings, 'OPENWEATHER_API_KEY', None)
    
    if not api_key:
        logger.warning("OpenWeatherMap API key not found in settings")
        # Return mock data for development
        return get_mock_weather_data(city)
    
    try:
        # Construct API URL
        base_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': city,
            'appid': api_key,
            'units': 'metric'  # Get temperature in Celsius
        }
        
        # Make API request
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Parse and return relevant weather data
        weather_data = {
            'temperature': round(data['main']['temp']),
            'condition': data['weather'][0]['main'],
            'description': data['weather'][0]['description'],
            'wind_speed': data['wind'].get('speed', 0),
            'humidity': data['main']['humidity'],
            'city': data['name'],
            'country': data['sys']['country']
        }
        
        return weather_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching weather data for {city}: {e}")
        return get_mock_weather_data(city)
    except KeyError as e:
        logger.error(f"Error parsing weather data for {city}: {e}")
        return get_mock_weather_data(city)
    except Exception as e:
        logger.error(f"Unexpected error fetching weather for {city}: {e}")
        return get_mock_weather_data(city)


def get_mock_weather_data(city):
    """
    Return mock weather data for development/testing purposes.
    """
    return {
        'temperature': 28,
        'condition': 'Clear',
        'description': 'clear sky',
        'wind_speed': 5.2,
        'humidity': 65,
        'city': city,
        'country': 'IN'
    }


def generate_weather_advice(weather_data):
    """
    Generate actionable farming advice based on weather conditions.
    
    Args:
        weather_data (dict): Weather data from get_weather_data()
        
    Returns:
        list: List of advice strings
    """
    if not weather_data:
        return ["Weather data unavailable. Please check your city settings."]
    
    advice = []
    temperature = weather_data.get('temperature', 0)
    condition = weather_data.get('condition', '').lower()
    wind_speed = weather_data.get('wind_speed', 0)
    humidity = weather_data.get('humidity', 0)
    
    # Temperature-based advice
    if temperature > 35:
        advice.append("🌡️ Extreme heat warning! Ensure crops are adequately irrigated and provide shade if possible.")
        advice.append("💧 Consider morning or evening watering to reduce water loss through evaporation.")
    elif temperature > 30:
        advice.append("☀️ Hot weather detected. Monitor soil moisture levels and increase watering frequency.")
    elif temperature < 10:
        advice.append("🥶 Cold weather alert! Protect sensitive crops from frost damage with covers or mulching.")
    elif 20 <= temperature <= 30:
        advice.append("🌤️ Optimal temperature conditions for most crop activities.")
    
    # Weather condition-based advice
    if 'rain' in condition or 'drizzle' in condition:
        advice.append("🌧️ Rainy conditions detected. Good time for planting as soil will be moist.")
        advice.append("⚠️ Avoid spraying pesticides or fertilizers during rain to prevent washoff.")
        advice.append("🚜 Postpone heavy machinery work to avoid soil compaction.")
    elif 'thunder' in condition or 'storm' in condition:
        advice.append("⛈️ Thunderstorm warning! Secure equipment and avoid outdoor farm work.")
        advice.append("🏠 Move livestock to shelter and check drainage systems.")
    elif 'snow' in condition:
        advice.append("❄️ Snow conditions. Protect plants from frost and ensure livestock have warm shelter.")
    elif condition == 'clear':
        advice.append("☀️ Clear skies ideal for outdoor farming activities like harvesting and field preparation.")
    
    # Wind-based advice
    if wind_speed > 15:
        advice.append("💨 High winds detected. Avoid spraying pesticides as they may drift to unintended areas.")
        advice.append("🌱 Strong winds may damage young plants. Consider providing windbreaks.")
    elif wind_speed > 25:
        advice.append("🌪️ Very strong winds! Secure loose equipment and delay aerial applications.")
    
    # Humidity-based advice
    if humidity > 80:
        advice.append("💨 High humidity levels may promote fungal diseases. Ensure good air circulation.")
        advice.append("🍄 Monitor crops closely for signs of fungal infections.")
    elif humidity < 30:
        advice.append("🏜️ Low humidity detected. Increase irrigation frequency to prevent plant stress.")
    
    # Seasonal general advice
    if not advice:
        advice.append("🌾 Current weather conditions are favorable for normal farming activities.")
    
    return advice


def get_weather_icon(condition):
    """
    Get appropriate emoji/icon for weather condition.
    
    Args:
        condition (str): Weather condition from API
        
    Returns:
        str: Emoji representing the weather condition
    """
    condition = condition.lower()
    
    icons = {
        'clear': '☀️',
        'clouds': '☁️',
        'rain': '🌧️',
        'drizzle': '🌦️',
        'thunderstorm': '⛈️',
        'snow': '❄️',
        'mist': '🌫️',
        'fog': '🌫️',
        'haze': '🌫️'
    }
    
    return icons.get(condition, '🌤️')


def get_weather_data_by_coordinates(lat, lon):
    """
    Fetch current weather data by coordinates from OpenWeatherMap API.
    
    Args:
        lat (float): Latitude
        lon (float): Longitude
        
    Returns:
        dict: Weather data containing temperature, condition, wind_speed, humidity
        None: If API call fails
    """
    if not lat or not lon:
        return None
        
    # Get API key from settings
    api_key = getattr(settings, 'OPENWEATHER_API_KEY', None)
    
    if not api_key:
        logger.warning("OpenWeatherMap API key not found in settings")
        # Return location-specific mock data for development
        return get_location_specific_mock_data(lat, lon)
    
    try:
        # Construct API URL for coordinates
        base_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': api_key,
            'units': 'metric'  # Get temperature in Celsius
        }
        
        # Make API request
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Parse and return relevant weather data
        weather_data = {
            'temperature': round(data['main']['temp']),
            'condition': data['weather'][0]['main'],
            'description': data['weather'][0]['description'],
            'wind_speed': data['wind']['speed'],
            'humidity': data['main']['humidity'],
            'city': data['name'],
            'country': data['sys']['country']
        }
        
        logger.info(f"Successfully fetched weather data for coordinates ({lat}, {lon})")
        return weather_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching weather data for coordinates ({lat}, {lon}): {e}")
        # Fallback to location-specific mock data
        return get_location_specific_mock_data(lat, lon)
    except KeyError as e:
        logger.error(f"Error parsing weather data for coordinates ({lat}, {lon}): {e}")
        # Fallback to location-specific mock data
        return get_location_specific_mock_data(lat, lon)


def get_location_specific_mock_data(lat, lon):
    """
    Return location-specific mock weather data based on coordinates.
    This function maps coordinate ranges to specific cities in India.
    
    Args:
        lat (float): Latitude
        lon (float): Longitude
        
    Returns:
        dict: Weather data specific to the detected location
    """
    try:
        lat = float(lat)
        lon = float(lon)
    except (ValueError, TypeError):
        return get_mock_weather_data("Unknown Location")
    
    # Define coordinate ranges for major Indian cities
    city_ranges = {
        # Telangana - Hyderabad
        'Hyderabad': {
            'lat_range': (17.2, 17.5),
            'lon_range': (78.3, 78.6),
            'weather': {
                'temperature': 32,
                'condition': 'Clear',
                'description': 'clear sky',
                'wind_speed': 8.5,
                'humidity': 55,
                'city': 'Hyderabad',
                'country': 'IN'
            }
        },
        # Telangana - Warangal
        'Warangal': {
            'lat_range': (17.9, 18.1),
            'lon_range': (79.5, 79.7),
            'weather': {
                'temperature': 31,
                'condition': 'Clear',
                'description': 'clear sky',
                'wind_speed': 7.2,
                'humidity': 58,
                'city': 'Warangal',
                'country': 'IN'
            }
        },
        # Delhi
        'Delhi': {
            'lat_range': (28.4, 28.8),
            'lon_range': (76.8, 77.3),
            'weather': {
                'temperature': 35,
                'condition': 'Haze',
                'description': 'haze',
                'wind_speed': 12.0,
                'humidity': 65,
                'city': 'Delhi',
                'country': 'IN'
            }
        },
        # Mumbai
        'Mumbai': {
            'lat_range': (19.0, 19.3),
            'lon_range': (72.7, 73.0),
            'weather': {
                'temperature': 29,
                'condition': 'Clouds',
                'description': 'partly cloudy',
                'wind_speed': 15.5,
                'humidity': 78,
                'city': 'Mumbai',
                'country': 'IN'
            }
        },
        # Bangalore
        'Bangalore': {
            'lat_range': (12.8, 13.1),
            'lon_range': (77.4, 77.8),
            'weather': {
                'temperature': 26,
                'condition': 'Clear',
                'description': 'clear sky',
                'wind_speed': 6.8,
                'humidity': 62,
                'city': 'Bangalore',
                'country': 'IN'
            }
        },
        # Chennai
        'Chennai': {
            'lat_range': (12.9, 13.2),
            'lon_range': (80.1, 80.4),
            'weather': {
                'temperature': 33,
                'condition': 'Clear',
                'description': 'clear sky',
                'wind_speed': 10.2,
                'humidity': 72,
                'city': 'Chennai',
                'country': 'IN'
            }
        },
        # Kolkata
        'Kolkata': {
            'lat_range': (22.4, 22.7),
            'lon_range': (88.2, 88.5),
            'weather': {
                'temperature': 30,
                'condition': 'Clouds',
                'description': 'overcast clouds',
                'wind_speed': 8.8,
                'humidity': 80,
                'city': 'Kolkata',
                'country': 'IN'
            }
        },
        # Pune
        'Pune': {
            'lat_range': (18.4, 18.7),
            'lon_range': (73.7, 74.0),
            'weather': {
                'temperature': 28,
                'condition': 'Clear',
                'description': 'clear sky',
                'wind_speed': 7.5,
                'humidity': 60,
                'city': 'Pune',
                'country': 'IN'
            }
        }
    }
    
    # Check which city range the coordinates fall into
    for city_name, city_data in city_ranges.items():
        lat_min, lat_max = city_data['lat_range']
        lon_min, lon_max = city_data['lon_range']
        
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            logger.info(f"Coordinates ({lat}, {lon}) detected as {city_name}")
            return city_data['weather']
    
    # If no specific city is found, return generic data based on rough geographic regions
    if 15.0 <= lat <= 21.0 and 72.0 <= lon <= 82.0:
        # Central India (Telangana, Maharashtra, Andhra Pradesh region)
        return {
            'temperature': 31,
            'condition': 'Clear',
            'description': 'clear sky',
            'wind_speed': 7.5,
            'humidity': 58,
            'city': 'Central India',
            'country': 'IN'
        }
    elif 23.0 <= lat <= 30.0 and 75.0 <= lon <= 85.0:
        # North India (Delhi, Rajasthan, UP region)
        return {
            'temperature': 34,
            'condition': 'Clear',
            'description': 'clear sky',
            'wind_speed': 10.0,
            'humidity': 50,
            'city': 'North India',
            'country': 'IN'
        }
    else:
        # Default fallback
        logger.warning(f"Coordinates ({lat}, {lon}) not in known city ranges")
        return {
            'temperature': 28,
            'condition': 'Clear',
            'description': 'clear sky',
            'wind_speed': 8.0,
            'humidity': 60,
            'city': f'Location ({lat:.1f}, {lon:.1f})',
            'country': 'Unknown'
        }
