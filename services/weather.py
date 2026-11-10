import json
from urllib.parse import quote

import requests


_WEATHER_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Rime fog", 51: "Light drizzle", 53: "Drizzle",
    55: "Heavy drizzle", 56: "Freezing drizzle", 57: "Heavy freezing drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain", 66: "Light freezing rain",
    67: "Heavy freezing rain", 71: "Light snow", 73: "Snow", 75: "Heavy snow",
    77: "Snow grains", 80: "Light rain showers", 81: "Rain showers",
    82: "Heavy rain showers", 85: "Snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with light hail", 99: "Thunderstorm with hail",
}


class IndianWeather:
    """Finds Indian locations and obtains current conditions from public APIs."""

    def __init__(self, timeout: int = 12):
        self.timeout = timeout

    def report(self, city: str) -> str:
        name = city.strip()
        if not name:
            return "Tell me the name of an Indian city and I'll look up its weather."

        try:
            matches = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": name, "count": 10, "countryCode": "IN", "language": "en"},
                timeout=self.timeout,
            ).json().get("results", [])
        except (requests.RequestException, ValueError):
            return "I can't reach the city search service right now. Please try again shortly."

        place = next((entry for entry in matches if entry.get("country_code") == "IN"), None)
        if not place:
            return f"I couldn't find an Indian city called {name}. Check the spelling and try again."

        conditions = self._open_meteo(place)
        if conditions is None:
            conditions = self._wttr(place["name"])
        if conditions is None:
            return f"Live weather for {place['name']} is temporarily unavailable. Please try again shortly."

        area = ", ".join(part for part in (place["name"], place.get("admin1")) if part)
        return json.dumps({"location": area, **conditions})

    def _open_meteo(self, place: dict) -> dict | None:
        try:
            result = requests.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": place["latitude"],
                    "longitude": place["longitude"],
                    "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
                    "temperature_unit": "celsius",
                },
                timeout=self.timeout,
            ).json()["current"]
            return {
                "temperature_celsius": result["temperature_2m"],
                "condition": _WEATHER_CODES.get(result["weather_code"], "Current conditions"),
                "humidity_percent": result["relative_humidity_2m"],
                "wind_speed_kmh": result["wind_speed_10m"],
                "source": "Open-Meteo",
            }
        except (requests.RequestException, KeyError, TypeError, ValueError):
            return None

    def _wttr(self, city: str) -> dict | None:
        try:
            current = requests.get(
                f"https://wttr.in/{quote(city)}",
                params={"format": "j1"},
                headers={"User-Agent": "IndiaWeatherMoviesAssistant/1.0"},
                timeout=self.timeout,
            ).json()["current_condition"][0]
            return {
                "temperature_celsius": float(current["temp_C"]),
                "condition": current["weatherDesc"][0]["value"],
                "humidity_percent": int(current["humidity"]),
                "wind_speed_kmh": float(current["windspeedKmph"]),
                "source": "wttr.in",
            }
        except (requests.RequestException, KeyError, IndexError, TypeError, ValueError):
            return None
