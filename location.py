import geocoder

def get_location():
    g = geocoder.ip('me')

    if g.ok:
        return {
            "lat": g.latlng[0],
            "lon": g.latlng[1],
            "city": g.city
        }
    else:
        return None