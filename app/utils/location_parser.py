import re
import pycountry


def get_country_from_text(text):
    if not text:
        return None

    text = text.lower()

    for country in pycountry.countries:
        if country.name.lower() in text:
            return country.name

    if re.search(r"\b(us|usa|united states)\b", text):
        return "United States"

    return None


def is_us_location(location):
    if not location:
        return False

    loc = location.lower()

    country = get_country_from_text(loc)

    if country:
        return country == "United States"

    US_STATES = [
        "al","ak","az","ar","ca","co","ct","de","fl","ga",
        "hi","id","il","in","ia","ks","ky","la","me","md",
        "ma","mi","mn","ms","mo","mt","ne","nv","nh","nj",
        "nm","ny","nc","nd","oh","ok","or","pa","ri","sc",
        "sd","tn","tx","ut","vt","va","wa","wv","wi","wy"
    ]

    if any(re.search(rf"\b{state}\b", loc) for state in US_STATES):
        return True

    US_CITIES = [
        "san francisco", "new york", "seattle", "austin",
        "chicago", "boston", "los angeles", "denver",
        "atlanta", "dallas"
    ]

    if any(city in loc for city in US_CITIES):
        return True

    if "remote" in loc and not country:
        return True

    return False