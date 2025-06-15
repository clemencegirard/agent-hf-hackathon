from typing import Any, Optional
from smolagents.tools import Tool
import requests
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv
import anthropic

class WeatherTool(Tool):
    name = "weather_forecast"
    description = "Obtient les prévisions météorologiques intelligentes pour un pays/ville avec recommandations basées sur le type de destination et les activités prévues."
    inputs = {
        'location': {'type': 'string', 'description': 'Le nom de la ville ou du pays pour lequel obtenir la météo (ex: "Paris", "London", "Tokyo")'},
        'date': {'type': 'string', 'description': 'La date pour laquelle obtenir la météo au format YYYY-MM-DD (optionnel, par défaut aujourd\'hui)', 'nullable': True},
        'activity_type': {'type': 'string', 'description': 'Type d\'activité/destination: "plage", "ski", "ville", "randonnee", "camping", "festival" (optionnel)', 'nullable': True},
        'api_key': {'type': 'string', 'description': 'Clé API OpenWeatherMap (optionnel si définie dans les variables d\'environnement)', 'nullable': True}
    }
    output_type = "string"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        # Charger les variables d'environnement depuis le fichier .env
        load_dotenv()
        
        # Utiliser la clé API fournie, sinon celle du .env
        self.api_key = api_key or os.getenv('OPENWEATHER_API_KEY')
        self.base_url = "http://api.openweathermap.org/data/2.5"
        
        # Initialiser le client Claude pour les recommandations intelligentes
        try:
            self.claude_client = anthropic.Anthropic(api_key=os.getenv('ANTROPIC_KEY'))
        except:
            self.claude_client = None

    def forward(self, location: str, date: Optional[str] = None, activity_type: Optional[str] = None, api_key: Optional[str] = None) -> str:
        try:
            # Utiliser la clé API fournie ou celle par défaut
            used_api_key = api_key or self.api_key
            
            if not used_api_key:
                return "Erreur: Clé API OpenWeatherMap requise. Ajoutez OPENWEATHER_API_KEY dans votre fichier .env ou obtenez une clé gratuite sur https://openweathermap.org/api"

            # Parser la date si fournie
            target_date = None
            if date:
                try:
                    target_date = datetime.strptime(date, "%Y-%m-%d")
                except ValueError:
                    return f"Erreur: Format de date invalide. Utilisez YYYY-MM-DD (ex: 2024-01-15)"

            # Obtenir les coordonnées de la localisation
            geo_url = f"http://api.openweathermap.org/geo/1.0/direct"
            geo_params = {
                'q': location,
                'limit': 1,
                'appid': used_api_key
            }
            
            geo_response = requests.get(geo_url, params=geo_params, timeout=10)
            geo_response.raise_for_status()
            geo_data = geo_response.json()
            
            if not geo_data:
                return f"Erreur: Localisation '{location}' non trouvée. Essayez avec le nom d'une ville ou d'un pays plus précis."
            
            lat = geo_data[0]['lat']
            lon = geo_data[0]['lon']
            country = geo_data[0].get('country', '')
            city_name = geo_data[0]['name']

            # Utiliser l'API gratuite
            weather_data = self._get_weather(lat, lon, city_name, country, target_date, used_api_key)
            
            # Ajouter des recommandations intelligentes si Claude est disponible
            if self.claude_client:
                # Utiliser le type d'activité fourni ou essayer de le détecter automatiquement
                detected_activity = activity_type or self._detect_activity_from_location(location)
                
                if detected_activity:
                    recommendation = self._get_intelligent_recommendation(weather_data, detected_activity, location, target_date)
                    if recommendation:
                        if not activity_type:  # Si détecté automatiquement, l'indiquer
                            weather_data += f"\n\n💡 *Activité détectée: {detected_activity}*"
                        weather_data += f"\n\n{recommendation}"
            
            return weather_data

        except requests.exceptions.Timeout:
            return "Erreur: Délai d'attente dépassé. Veuillez réessayer."
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                return "Erreur 401: Clé API invalide ou non activée. Vérifiez votre clé API OpenWeatherMap et assurez-vous qu'elle est activée (peut prendre quelques heures après création)."
            elif e.response.status_code == 429:
                return "Erreur 429: Limite de requêtes dépassée. Attendez avant de refaire une requête."
            else:
                return f"Erreur HTTP {e.response.status_code}: {str(e)}"
        except requests.exceptions.RequestException as e:
            return f"Erreur de requête: {str(e)}"
        except Exception as e:
            return f"Erreur inattendue: {str(e)}"

    def _get_weather(self, lat: float, lon: float, city_name: str, country: str, target_date: Optional[datetime], api_key: str) -> str:
        """Utilise l'API gratuite 2.5"""
        
        if not target_date or target_date.date() == datetime.now().date():
            # Météo actuelle
            weather_url = f"{self.base_url}/weather"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': api_key,
                'units': 'metric',
                'lang': 'fr'
            }
            
            response = requests.get(weather_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return self._format_current_weather(data, city_name, country)
            
        elif target_date and target_date <= datetime.now() + timedelta(days=5):
            # Prévisions sur 5 jours
            forecast_url = f"{self.base_url}/forecast"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': api_key,
                'units': 'metric',
                'lang': 'fr'
            }
            
            response = requests.get(forecast_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return self._format_forecast_weather(data, city_name, country, target_date)
        else:
            return "Erreur: Les prévisions ne sont disponibles que pour les 5 prochains jours maximum."

    def _format_current_weather(self, data: dict, city_name: str, country: str) -> str:
        """Formate les données météo actuelles"""
        try:
            weather = data['weather'][0]
            main = data['main']
            wind = data.get('wind', {})
            
            result = f"🌤️ **Météo actuelle pour {city_name}, {country}**\n\n"
            result += f"**Conditions:** {weather['description'].title()}\n"
            result += f"**Température:** {main['temp']:.1f}°C (ressenti: {main['feels_like']:.1f}°C)\n"
            result += f"**Humidité:** {main['humidity']}%\n"
            result += f"**Pression:** {main['pressure']} hPa\n"
            
            if 'speed' in wind:
                result += f"**Vent:** {wind['speed']} m/s"
                if 'deg' in wind:
                    result += f" ({self._wind_direction(wind['deg'])})"
                result += "\n"
            
            if 'visibility' in data:
                result += f"**Visibilité:** {data['visibility']/1000:.1f} km\n"
                
            return result
            
        except KeyError as e:
            return f"Erreur lors du formatage des données météo: {str(e)}"

    def _format_forecast_weather(self, data: dict, city_name: str, country: str, target_date: datetime) -> str:
        """Formate les prévisions météo pour une date spécifique"""
        try:
            target_date_str = target_date.strftime("%Y-%m-%d")
            
            # Trouver les prévisions pour la date cible
            forecasts_for_date = []
            for forecast in data['list']:
                forecast_date = datetime.fromtimestamp(forecast['dt']).strftime("%Y-%m-%d")
                if forecast_date == target_date_str:
                    forecasts_for_date.append(forecast)
            
            if not forecasts_for_date:
                return f"Aucune prévision disponible pour le {target_date_str}"
            
            result = f"🌤️ **Prévisions météo pour {city_name}, {country} - {target_date.strftime('%d/%m/%Y')}**\n\n"
            
            for i, forecast in enumerate(forecasts_for_date):
                time = datetime.fromtimestamp(forecast['dt']).strftime("%H:%M")
                weather = forecast['weather'][0]
                main = forecast['main']
                wind = forecast.get('wind', {})
                
                result += f"**{time}:**\n"
                result += f"  • Conditions: {weather['description'].title()}\n"
                result += f"  • Température: {main['temp']:.1f}°C (ressenti: {main['feels_like']:.1f}°C)\n"
                result += f"  • Humidité: {main['humidity']}%\n"
                
                if 'speed' in wind:
                    result += f"  • Vent: {wind['speed']} m/s"
                    if 'deg' in wind:
                        result += f" ({self._wind_direction(wind['deg'])})"
                    result += "\n"
                
                if i < len(forecasts_for_date) - 1:
                    result += "\n"
            
            return result
            
        except KeyError as e:
            return f"Erreur lors du formatage des prévisions: {str(e)}"

    def _wind_direction(self, degrees: float) -> str:
        """Convertit les degrés en direction du vent"""
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                     "S", "SSO", "SO", "OSO", "O", "ONO", "NO", "NNO"]
        index = round(degrees / 22.5) % 16
        return directions[index]

    def _get_intelligent_recommendation(self, weather_data: str, activity_type: str, location: str, target_date: Optional[datetime]) -> Optional[str]:
        """Utilise Claude pour générer des recommandations intelligentes basées sur la météo et l'activité"""
        try:
            if not self.claude_client:
                return None
            
            date_str = target_date.strftime('%d/%m/%Y') if target_date else "aujourd'hui"
            
            prompt = f"""Analysez ces données météorologiques pour {location} le {date_str} et donnez une recommandation pour une activité de type "{activity_type}" :

DONNÉES MÉTÉO :
{weather_data}

TYPE D'ACTIVITÉ : {activity_type}

Votre tâche :
1. Analysez si les conditions météo sont adaptées à cette activité
2. Donnez une recommandation claire : IDÉAL / ACCEPTABLE / DÉCONSEILLÉ / CHANGEZ DE DESTINATION
3. Proposez des alternatives si nécessaire
4. Répondez en français, maximum 150 mots
5. Utilisez un ton pratique et bienveillant

Exemples de logique :
- Plage + pluie = CHANGEZ DE DESTINATION ou reportez
- Ski + température > 5°C = DÉCONSEILLÉ
- Randonnée + orage = CHANGEZ DE DESTINATION
- Ville + pluie légère = ACCEPTABLE avec parapluie
- Festival en extérieur + pluie forte = DÉCONSEILLÉ

Format de réponse :
🎯 **RECOMMANDATION VOYAGE**
[Votre analyse et conseil]"""

            response = self.claude_client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=200,
                temperature=0.2,
                system="Vous êtes un conseiller météo expert. Donnez des recommandations pratiques et claires pour les activités de voyage.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text.strip()
            
        except Exception:
            return None

    def _detect_activity_from_location(self, location: str) -> Optional[str]:
        """Détecte automatiquement le type d'activité probable basé sur la localisation"""
        location_lower = location.lower()
        
        # Stations balnéaires et plages
        beach_keywords = ['nice', 'cannes', 'saint-tropez', 'biarritz', 'deauville', 'miami', 'maldives', 'ibiza', 'mykonos', 'cancun', 'phuket', 'bali']
        if any(keyword in location_lower for keyword in beach_keywords):
            return "plage"
        
        # Stations de ski
        ski_keywords = ['chamonix', 'val d\'isère', 'courchevel', 'méribel', 'aspen', 'zermatt', 'st moritz', 'verbier']
        if any(keyword in location_lower for keyword in ski_keywords):
            return "ski"
        
        # Destinations de randonnée
        hiking_keywords = ['mont blanc', 'everest', 'kilimanjaro', 'patagonie', 'himalaya', 'alpes', 'pyrénées']
        if any(keyword in location_lower for keyword in hiking_keywords):
            return "randonnee"
        
        return None 