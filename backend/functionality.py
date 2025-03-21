from fastapi import FastAPI, Query
import requests
import time
import random
import re
from datetime import datetime
from geopy.geocoders import Nominatim

app = FastAPI()

OVERPASS_URL = "http://overpass-api.de/api/interpreter"
SERPAPI_KEY = "b93e39d0d85b812b63d79145d1dc3f29ea3fa958b81a00b65a14c9a3de7d0cbc"  # Замени с реален SerpAPI ключ

def get_coordinates(city: str):
    """Взима GPS координати за града чрез OpenStreetMap."""
    geolocator = Nominatim(user_agent="travel_planner")
    location = geolocator.geocode(f"{city}, Bulgaria")
    return (location.latitude, location.longitude) if location else None

def get_places(lat, lon):
    """Извлича ресторанти, забележителности и хотели от OpenStreetMap."""
    query = f"""
    [out:json];
    (
        node["tourism"="attraction"](around:5000,{lat},{lon});
        node["amenity"="restaurant"](around:5000,{lat},{lon});
        node["tourism"="hotel"](around:5000,{lat},{lon});
    );
    out;
    """
    response = requests.get(OVERPASS_URL, params={"data": query})
    if response.status_code != 200:
        return {"restaurants": [], "attractions": [], "hotels": []}
    pois = response.json().get("elements", [])
    restaurants, attractions, hotels = [], [], []
    for poi in pois:
        name = poi.get("tags", {}).get("name")
        if not name:
            continue  # Пропуска места без име
        place = {"name": name, "lat": poi["lat"], "lon": poi["lon"]}
        tags = poi.get("tags", {})
        if "restaurant" in tags.get("amenity", ""):
            restaurants.append(place)
        else:
            attractions.append(place)
    return {
        "restaurants": restaurants[:5],
        "attractions": attractions[:5]
    }

def get_hotels_from_osm(lat, lon):
    """Извлича хотели от OpenStreetMap."""
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
    return hotels[:6]

def get_hotel_price_from_serpapi(hotel_name, city):
    """Извлича цена за конкретен хотел от Google чрез SerpAPI."""
    url = "https://serpapi.com/search"
    params = {
        "engine": "google",
        "q": f"цена {hotel_name} {city}",
        "hl": "bg",
        "gl": "bg",
        "api_key": SERPAPI_KEY
    }
    response = requests.get(url, params=params).json()
    for result in response.get("organic_results", []):
        snippet = result.get("snippet", "")
        match = re.search(r'(\d{1,5})\s?(лв|BGN|€|EUR)', snippet)
        if match:
            return f"{match.group(1)} {match.group(2)}"
    return None  # Ако няма цена, връща None

@app.get("/plan_route/")
def plan_route(
        cities: str = Query(..., description="Списък с градове, разделени със запетая"),
        start_date: str = Query(..., description="Начална дата (YYYY-MM-DD)"),
        end_date: str = Query(..., description="Крайна дата (YYYY-MM-DD)")
):
    """Генерира маршрут с атракции, ресторанти и хотели (с реални или фиктивни цени)."""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        if start < datetime.today():
            return {"error": "Началната дата трябва да е в бъдещето"}
        if end <= start:
            return {"error": "Крайната дата трябва да е след началната"}
    except ValueError:
        return {"error": "Грешен формат на датата. Използвайте YYYY-MM-DD"}
    city_list = [city.strip() for city in cities.split(",")]
    route = []
    for city in city_list:
        coords = get_coordinates(city)
        if not coords:
            continue  # Пропуска града, ако не е намерен
        lat, lon = coords
        places = get_places(lat, lon)
        hotels = get_hotels_from_osm(lat, lon)
        filtered_hotels = []
        for hotel in hotels:
            price = get_hotel_price_from_serpapi(hotel["name"], city)
            if price:
                hotel["price"] = price
                filtered_hotels.append(hotel)  # Добавяме само хотели с цена
        route.append({
            "city": city,
            "places": places,
            "hotels": filtered_hotels
        })
    return {"route": route}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")