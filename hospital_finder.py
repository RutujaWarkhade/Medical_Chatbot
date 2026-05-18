import requests

def find_hospitals_osm(lat, lon, radius=5000):
    """
    Find nearby hospitals using OpenStreetMap Overpass API.
    Returns a list of dicts with 'name', 'lat', 'lon'.
    Falls back to alternate Overpass endpoints if the first fails.
    """

    query = f"""
    [out:json][timeout:25];
    (
      node["amenity"="hospital"](around:{radius},{lat},{lon});
      way["amenity"="hospital"](around:{radius},{lat},{lon});
      node["amenity"="clinic"](around:{radius},{lat},{lon});
    );
    out center;
    """

    # Multiple Overpass API endpoints as fallbacks
    endpoints = [
        "https://overpass-api.de/api/interpreter",
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
    ]

    for url in endpoints:
        try:
            response = requests.get(
                url,
                params={"data": query},
                timeout=20,
                headers={"User-Agent": "MedicalChatbot/1.0"}
            )

            # Check if response is valid
            if response.status_code != 200:
                print(f"Endpoint {url} returned status {response.status_code}, trying next...")
                continue

            if not response.text.strip():
                print(f"Endpoint {url} returned empty response, trying next...")
                continue

            data = response.json()
            hospitals = []

            for element in data.get("elements", []):
                name = element.get("tags", {}).get("name", "Unknown Hospital")

                # Handle both node and way (way has 'center')
                if element["type"] == "node":
                    h_lat = element.get("lat")
                    h_lon = element.get("lon")
                elif element["type"] == "way":
                    center = element.get("center", {})
                    h_lat = center.get("lat")
                    h_lon = center.get("lon")
                else:
                    continue

                if h_lat and h_lon:
                    hospitals.append({
                        "name": name,
                        "lat": h_lat,
                        "lon": h_lon
                    })

            return hospitals

        except requests.exceptions.Timeout:
            print(f"Endpoint {url} timed out, trying next...")
            continue
        except requests.exceptions.ConnectionError:
            print(f"Could not connect to {url}, trying next...")
            continue
        except requests.exceptions.JSONDecodeError:
            print(f"Endpoint {url} returned invalid JSON, trying next...")
            continue
        except Exception as e:
            print(f"Unexpected error with {url}: {e}, trying next...")
            continue

    # All endpoints failed
    print("All Overpass API endpoints failed.")
    return []
