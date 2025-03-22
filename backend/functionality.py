from fastapi import FastAPI, Query
import requests
import re
from datetime import datetime
from geopy.geocoders import Nominatim

app = FastAPI()

OVERPASS_URL = "http://overpass-api.de/api/interpreter" # Aтракции и хотели
SERPER_API_KEY = "92fa250229ab124510a0d89399f1aa4bc606dced"  # Извлича цени на хотели от Google
SERPAPI_KEY = "30c90bb56b6894a50322c741e9583a7d00de9911eb6e2d70555ee14c98f54054"  # Намира ресторанти в Google Maps

def get_coordinates(city: str):
    geolocator = Nominatim(user_agent="travel_planner")
    location = geolocator.geocode(f"{city}, Bulgaria")
    return (location.latitude, location.longitude) if location else None


def get_restaurant_ratings(location, lowest_rating, highest_rating):
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_maps",
        "q": f"restaurants in {location}",
        "type": "search",
        "api_key": SERPAPI_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()

    restaurants = []

    if "local_results" in data:
        for place in data["local_results"]:
            rating = place.get("rating")
            if rating and (rating < lowest_rating or rating > highest_rating):
                continue 

            restaurants.append({
                "name": place.get("title"),
                "rating": rating,
                "reviews": place.get("reviews", "N/A"),
                "lat": place["gps_coordinates"]["latitude"],
                "lon": place["gps_coordinates"]["longitude"]
            })

    return restaurants


def get_restaurants_and_attractions(city, lowest_rating, highest_rating):
    coords = get_coordinates(city)
    if not coords:
        return {"restaurants": [], "attractions": []}

    lat, lon = coords

    query = f"""
    [out:json];
    node["tourism"="attraction"](around:5000,{lat},{lon});
    out;
    """
    response = requests.get(OVERPASS_URL, params={"data": query})
    attractions = []

    if response.status_code == 200:
        pois = response.json().get("elements", [])
        for poi in pois:
            name = poi.get("tags", {}).get("name")
            if name:
                attractions.append({"name": name, "lat": poi["lat"], "lon": poi["lon"]})

    restaurants = get_restaurant_ratings(city, lowest_rating, highest_rating)

    return {
        "restaurants": restaurants[:8],  
        "attractions": attractions[:8]
    }


def get_hotels_from_osm(lat, lon):
    query = f"""
    [out:json];
    node["tourism"="hotel"](around:10000,{lat},{lon});
    out;
    """
    response = requests.get(OVERPASS_URL, params={"data": query})
    hotels = []
    if response.status_code == 200:
        for poi in response.json().get("elements", []):
            name = poi.get("tags", {}).get("name")
            if name:
                hotels.append({
                    "name": name,
                    "lat": poi["lat"],
                    "lon": poi["lon"]
                })
    return hotels[:10]


def get_hotel_price_from_serper(hotel_name, city):
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "q": f"цена {hotel_name} {city}",
        "hl": "bg",
        "gl": "bg"
    }

    response = requests.post(url, json=data, headers=headers)

    if response.status_code != 200:
        return None

    response_json = response.json()

    for result in response_json.get("organic", []):
        snippet = result.get("snippet", "")
        match = re.search(r'(\d{1,5})\s?(лв|BGN|€|EUR)', snippet)
        if match:
            return f"{match.group(1)} {match.group(2)}"

    return None


def convert_price_to_bgn(price):
    match = re.search(r'(\d+)\s?(лв|BGN|€|EUR)', price)
    if match:
        amount = int(match.group(1))
        currency = match.group(2)
        if currency in ["€", "EUR"]:
            return f"{int(amount * 1.95)} BGN"  # Преобразуваме от EUR към BGN
        return f"{amount} BGN"
    return None


def calculate_total_hotel_cost(price_per_night, start_date, end_date):
    num_nights = (end_date - start_date).days
    return price_per_night * num_nights if num_nights > 0 else 0


@app.get("/plan_route/")
def plan_route(
        city: str = Query(..., description="Града за посещение"),
        budget: int = Query(..., description="Бюджет за хотел общо (в левове)"),
        lowest_rating: float = Query(..., description="Минимален рейтинг на ресторант"),
        highest_rating: float = Query(..., description="Максимален рейтинг на ресторант"),
        start_date: str = Query(..., description="Начална дата (YYYY-MM-DD)"),
        end_date: str = Query(..., description="Крайна дата (YYYY-MM-DD)")
):
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        if start < datetime.today():
            return {"error": "Началната дата трябва да е в бъдещето"}
        if end <= start:
            return {"error": "Крайната дата трябва да е след началната"}
    except ValueError:
        return {"error": "Грешен формат на датата. Използвайте YYYY-MM-DD"}

    coords = get_coordinates(city)
    if not coords:
        return {"error": f"Не намерих координати за {city}"}

    
    lat, lon = coords

    places = get_restaurants_and_attractions(city, lowest_rating, highest_rating)
    hotels = get_hotels_from_osm(lat, lon)

    filtered_hotels = []
    for hotel in hotels:
        price = get_hotel_price_from_serper(hotel["name"], city)
        if price:
            price_bgn = convert_price_to_bgn(price)
            match = re.search(r'(\d+)', price_bgn)
            if match:
                price_per_night = int(match.group(1))
                total_price = calculate_total_hotel_cost(price_per_night, start, end)
                if total_price <= budget:
                    hotel["price_per_night"] = f"{price_per_night} BGN"
                    hotel["total_price"] = f"{total_price} BGN"
                    filtered_hotels.append(hotel)

    response_data = {
        "data": [
            {
              "city": city,
              "places": {
                "attractions": places["attractions"],
                "restaurants": places["restaurants"],
              },
              "hotels": filtered_hotels
            }
        ]
    }
    print(response_data)
    return response_data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")
