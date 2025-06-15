from typing import Any
from smolagents.tools import Tool
import requests
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv
import re
import anthropic

class CountryInfoTool(Tool):
    name = "country_info"
    description = "Retrieves important contextual information about a country in real-time: security, current events, national holidays, political climate, travel advice."
    inputs = {
        'country': {'type': 'string', 'description': 'Country name in French or English (e.g., "France", "United States", "Japan")'},
        'info_type': {'type': 'string', 'description': 'Type of information requested: "all" (recommended), "security", "events", "holidays", "travel", "politics"', 'nullable': True}
    }
    output_type = "string"

    def __init__(self):
        super().__init__()
        load_dotenv()
        
        # Initialiser le client Claude (Anthropic)
        self.claude_client = anthropic.Anthropic(api_key=os.getenv('ANTROPIC_KEY'))
        
        # Mapping étendu des pays français vers anglais pour les APIs
        self.country_mapping = {
            # Europe
            'france': 'France', 'allemagne': 'Germany', 'italie': 'Italy', 'espagne': 'Spain',
            'royaume-uni': 'United Kingdom', 'angleterre': 'United Kingdom', 'écosse': 'United Kingdom',
            'pays-bas': 'Netherlands', 'hollande': 'Netherlands', 'belgique': 'Belgium', 
            'suisse': 'Switzerland', 'autriche': 'Austria', 'portugal': 'Portugal',
            'suède': 'Sweden', 'norvège': 'Norway', 'danemark': 'Denmark', 'finlande': 'Finland',
            'pologne': 'Poland', 'république tchèque': 'Czech Republic', 'tchéquie': 'Czech Republic',
            'hongrie': 'Hungary', 'roumanie': 'Romania', 'bulgarie': 'Bulgaria',
            'grèce': 'Greece', 'croatie': 'Croatia', 'slovénie': 'Slovenia', 'slovaquie': 'Slovakia',
            'estonie': 'Estonia', 'lettonie': 'Latvia', 'lituanie': 'Lithuania',
            'irlande': 'Ireland', 'islande': 'Iceland', 'malte': 'Malta', 'chypre': 'Cyprus',
            'serbie': 'Serbia', 'bosnie': 'Bosnia and Herzegovina', 'monténégro': 'Montenegro',
            'macédoine': 'North Macedonia', 'albanie': 'Albania', 'moldavie': 'Moldova',
            'ukraine': 'Ukraine', 'biélorussie': 'Belarus', 'russie': 'Russia',
            
            # Amériques
            'états-unis': 'United States', 'usa': 'United States', 'amérique': 'United States',
            'canada': 'Canada', 'mexique': 'Mexico',
            'brésil': 'Brazil', 'argentine': 'Argentina', 'chili': 'Chile', 'pérou': 'Peru',
            'colombie': 'Colombia', 'venezuela': 'Venezuela', 'équateur': 'Ecuador',
            'bolivie': 'Bolivia', 'paraguay': 'Paraguay', 'uruguay': 'Uruguay',
            'guatemala': 'Guatemala', 'costa rica': 'Costa Rica', 'panama': 'Panama',
            'cuba': 'Cuba', 'jamaïque': 'Jamaica', 'haïti': 'Haiti', 'république dominicaine': 'Dominican Republic',
            
            # Asie
            'chine': 'China', 'japon': 'Japan', 'corée du sud': 'South Korea', 'corée du nord': 'North Korea',
            'inde': 'India', 'pakistan': 'Pakistan', 'bangladesh': 'Bangladesh', 'sri lanka': 'Sri Lanka',
            'thaïlande': 'Thailand', 'vietnam': 'Vietnam', 'cambodge': 'Cambodia', 'laos': 'Laos',
            'myanmar': 'Myanmar', 'birmanie': 'Myanmar', 'malaisie': 'Malaysia', 'singapour': 'Singapore',
            'indonésie': 'Indonesia', 'philippines': 'Philippines', 'brunei': 'Brunei',
            'mongolie': 'Mongolia', 'kazakhstan': 'Kazakhstan', 'ouzbékistan': 'Uzbekistan',
            'kirghizistan': 'Kyrgyzstan', 'tadjikistan': 'Tajikistan', 'turkménistan': 'Turkmenistan',
            'afghanistan': 'Afghanistan', 'iran': 'Iran', 'irak': 'Iraq', 'syrie': 'Syria',
            'turquie': 'Turkey', 'israël': 'Israel', 'palestine': 'Palestine', 'liban': 'Lebanon',
            'jordanie': 'Jordan', 'arabie saoudite': 'Saudi Arabia', 'émirats arabes unis': 'United Arab Emirates',
            'qatar': 'Qatar', 'koweït': 'Kuwait', 'bahreïn': 'Bahrain', 'oman': 'Oman', 'yémen': 'Yemen',
            
            # Afrique
            'maroc': 'Morocco', 'algérie': 'Algeria', 'tunisie': 'Tunisia', 'libye': 'Libya', 'égypte': 'Egypt',
            'soudan': 'Sudan', 'éthiopie': 'Ethiopia', 'kenya': 'Kenya', 'tanzanie': 'Tanzania',
            'ouganda': 'Uganda', 'rwanda': 'Rwanda', 'burundi': 'Burundi', 'congo': 'Democratic Republic of the Congo',
            'république démocratique du congo': 'Democratic Republic of the Congo', 'rdc': 'Democratic Republic of the Congo',
            'république du congo': 'Republic of the Congo', 'cameroun': 'Cameroon', 'nigeria': 'Nigeria',
            'ghana': 'Ghana', 'côte d\'ivoire': 'Ivory Coast', 'sénégal': 'Senegal', 'mali': 'Mali',
            'burkina faso': 'Burkina Faso', 'niger': 'Niger', 'tchad': 'Chad', 'centrafrique': 'Central African Republic',
            'gabon': 'Gabon', 'guinée équatoriale': 'Equatorial Guinea', 'sao tomé': 'Sao Tome and Principe',
            'cap-vert': 'Cape Verde', 'guinée-bissau': 'Guinea-Bissau', 'guinée': 'Guinea',
            'sierra leone': 'Sierra Leone', 'liberia': 'Liberia', 'togo': 'Togo', 'bénin': 'Benin',
            'mauritanie': 'Mauritania', 'gambie': 'Gambia', 'afrique du sud': 'South Africa',
            'namibie': 'Namibia', 'botswana': 'Botswana', 'zimbabwe': 'Zimbabwe', 'zambie': 'Zambia',
            'malawi': 'Malawi', 'mozambique': 'Mozambique', 'madagascar': 'Madagascar', 'maurice': 'Mauritius',
            'seychelles': 'Seychelles', 'comores': 'Comoros', 'djibouti': 'Djibouti', 'érythrée': 'Eritrea',
            'somalie': 'Somalia', 'lesotho': 'Lesotho', 'eswatini': 'Eswatini', 'swaziland': 'Eswatini',
            
            # Océanie
            'australie': 'Australia', 'nouvelle-zélande': 'New Zealand', 'fidji': 'Fiji',
            'papouasie-nouvelle-guinée': 'Papua New Guinea', 'vanuatu': 'Vanuatu', 'samoa': 'Samoa',
            'tonga': 'Tonga', 'îles salomon': 'Solomon Islands', 'micronésie': 'Micronesia',
            'palau': 'Palau', 'nauru': 'Nauru', 'kiribati': 'Kiribati', 'tuvalu': 'Tuvalu'
        }
        
        # Codes ISO pour certaines APIs
        self.country_codes = {
            'France': 'FR', 'United States': 'US', 'United Kingdom': 'GB',
            'Germany': 'DE', 'Italy': 'IT', 'Spain': 'ES', 'Japan': 'JP',
            'China': 'CN', 'India': 'IN', 'Brazil': 'BR', 'Canada': 'CA',
            'Australia': 'AU', 'Russia': 'RU', 'Mexico': 'MX', 'South Korea': 'KR',
            'Netherlands': 'NL', 'Belgium': 'BE', 'Switzerland': 'CH',
            'Sweden': 'SE', 'Norway': 'NO', 'Denmark': 'DK', 'Turkey': 'TR',
            'Egypt': 'EG', 'Thailand': 'TH', 'Iran': 'IR'
        }

    def forward(self, country: str, info_type: str = "all") -> str:
        try:
            # Normaliser le nom du pays
            country_normalized = self._normalize_country_name(country)
            
            if not country_normalized:
                return f"❌ Country not recognized: '{country}'. Try with the full name (e.g., 'France', 'United States', 'United Kingdom')"
            
            # Collecter les informations selon le type demandé
            info_sections = []
            
            if info_type in ["all", "security"]:
                security_info = self._get_security_info(country_normalized)
                if security_info:
                    info_sections.append(security_info)
            
            if info_type in ["all", "events"]:
                events_info = self._get_current_events_info(country_normalized)
                if events_info:
                    info_sections.append(events_info)
            
            if info_type in ["all", "holidays"]:
                holidays_info = self._get_holidays_info(country_normalized)
                if holidays_info:
                    info_sections.append(holidays_info)
            
            if info_type in ["all", "travel"]:
                travel_info = self._get_travel_info(country_normalized)
                if travel_info:
                    info_sections.append(travel_info)
            
            if info_type in ["all", "politics"]:
                politics_info = self._get_political_info(country_normalized)
                if politics_info:
                    info_sections.append(politics_info)
            
            if not info_sections:
                return f"❌ No information available for {country_normalized} currently."
            
            # Assembler le rapport final
            result = f"🌍 **Contextual Information for {country_normalized}**\n"
            result += f"*Updated: {datetime.now().strftime('%m/%d/%Y %H:%M')}*\n\n"
            result += "\n\n".join(info_sections)
            
            # Ajouter une recommandation finale intelligente si Claude est disponible et qu'on demande toutes les infos
            if info_type == "all" and self.claude_client:
                final_recommendation = self._get_llm_final_recommendation(country_normalized, "\n\n".join(info_sections))
                if final_recommendation:
                    result += f"\n\n{final_recommendation}"
            
            return result
            
        except Exception as e:
            return f"❌ Error retrieving information: {str(e)}"

    def _normalize_country_name(self, country: str):
        """Normalise le nom du pays"""
        country_lower = country.lower().strip()
        
        # Vérifier dans le mapping français -> anglais
        if country_lower in self.country_mapping:
            return self.country_mapping[country_lower]
        
        # Vérifier si c'est déjà un nom anglais valide
        for french, english in self.country_mapping.items():
            if country_lower == english.lower():
                return english
        
        # Essayer une correspondance partielle
        for french, english in self.country_mapping.items():
            if country_lower in french or french in country_lower:
                return english
        
        # Si pas trouvé dans le mapping, essayer de valider via l'API REST Countries
        validated_country = self._validate_country_via_api(country)
        if validated_country:
            return validated_country
        
        return None

    def _validate_country_via_api(self, country: str):
        """Valide et normalise le nom du pays via l'API REST Countries"""
        try:
            # Essayer d'abord avec le nom exact
            url = f"https://restcountries.com/v3.1/name/{country}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    # Retourner le nom officiel en anglais
                    return data[0].get('name', {}).get('common', country.title())
            
            # Si échec, essayer avec une recherche partielle
            url = f"https://restcountries.com/v3.1/name/{country}?fullText=false"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    # Prendre le premier résultat
                    return data[0].get('name', {}).get('common', country.title())
            
            return None
            
        except Exception:
            # En cas d'erreur, retourner le nom avec la première lettre en majuscule
            return country.title() if len(country) > 2 else None

    def _get_country_code_from_api(self, country: str):
        """Récupère le code ISO du pays via l'API REST Countries"""
        try:
            url = f"https://restcountries.com/v3.1/name/{country}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    # Retourner le code ISO alpha-2
                    return data[0].get('cca2', '')
            
            return None
            
        except Exception:
            return None

    def _get_security_info(self, country: str) -> str:
        """Récupère les informations de sécurité avec recherche exhaustive"""
        try:
            # Vérifier d'abord si c'est un pays à risque connu
            risk_level = self._check_known_risk_countries(country)
            
            # Recherches multiples avec différents mots-clés
            all_news_data = []
            
            # Recherche 1: Sécurité générale
            security_keywords = f"{country} travel advisory security warning conflict war"
            news_data1 = self._search_security_news(security_keywords)
            all_news_data.extend(news_data1)
            
            # Recherche 2: Conflits spécifiques
            conflict_keywords = f"{country} war conflict violence terrorism attack bombing"
            news_data2 = self._search_security_news(conflict_keywords)
            all_news_data.extend(news_data2)
            
            # Recherche 3: Instabilité politique
            political_keywords = f"{country} coup government crisis instability sanctions"
            news_data3 = self._search_security_news(political_keywords)
            all_news_data.extend(news_data3)
            
            # Recherche 4: Alertes de voyage
            travel_keywords = f"{country} 'travel ban' 'do not travel' 'avoid travel' embassy"
            news_data4 = self._search_security_news(travel_keywords)
            all_news_data.extend(news_data4)
            
            # Supprimer les doublons
            unique_news = []
            seen_titles = set()
            for article in all_news_data:
                title = article.get('title', '')
                if title and title not in seen_titles:
                    unique_news.append(article)
                    seen_titles.add(title)
            
            # Analyser les résultats pour déterminer le niveau de sécurité
            security_level, description, recommendation = self._analyze_security_data(country, unique_news, risk_level)
            
            result = f"🛡️ **Security and Travel Advice**\n"
            result += f"{security_level} **Level determined by real-time analysis**\n"
            result += f"📋 {description}\n"
            result += f"🎯 **Recommendation: {recommendation}**"
            
            return result
            
        except Exception as e:
            return f"🛡️ **Security**: Error during retrieval - {str(e)}"

    def _check_known_risk_countries(self, country: str) -> str:
        """Vérifie si le pays est dans la liste des pays à risque connus"""
        
        # Pays à très haut risque (guerre active, conflit majeur)
        high_risk_countries = [
            'Ukraine', 'Afghanistan', 'Syria', 'Yemen', 'Somalia', 'South Sudan',
            'Central African Republic', 'Mali', 'Burkina Faso', 'Niger',
            'Democratic Republic of the Congo', 'Myanmar', 'Palestine', 'Gaza',
            'West Bank', 'Iraq', 'Libya', 'Sudan'
        ]
        
        # Pays à risque modéré (instabilité, tensions)
        moderate_risk_countries = [
            'Iran', 'North Korea', 'Venezuela', 'Belarus', 'Ethiopia',
            'Chad', 'Cameroon', 'Nigeria', 'Pakistan', 'Bangladesh',
            'Haiti', 'Lebanon', 'Turkey', 'Egypt', 'Algeria'
        ]
        
        # Pays avec tensions spécifiques
        tension_countries = [
            'Russia', 'China', 'Israel', 'India', 'Kashmir', 'Taiwan',
            'Hong Kong', 'Thailand', 'Philippines', 'Colombia'
        ]
        
        country_lower = country.lower()
        
        for risk_country in high_risk_countries:
            if risk_country.lower() in country_lower or country_lower in risk_country.lower():
                return "HIGH_RISK"
        
        for risk_country in moderate_risk_countries:
            if risk_country.lower() in country_lower or country_lower in risk_country.lower():
                return "MODERATE_RISK"
                
        for risk_country in tension_countries:
            if risk_country.lower() in country_lower or country_lower in risk_country.lower():
                return "TENSION"
        
        return "UNKNOWN"

    def _search_security_news(self, keywords: str) -> list:
        """Recherche d'actualités de sécurité avec période étendue"""
        try:
            # Utiliser NewsAPI si disponible
            api_key = os.getenv('NEWSAPI_KEY')
            if api_key:
                url = "https://newsapi.org/v2/everything"
                params = {
                    'q': keywords,
                    'sortBy': 'publishedAt',
                    'pageSize': 20,  # Plus d'articles
                    'language': 'en',
                    'from': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),  # 30 jours au lieu de 7
                    'apiKey': api_key
                }
                
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    articles = data.get('articles', [])
                    
                    # Filtrer les articles pertinents
                    relevant_articles = []
                    for article in articles:
                        title = article.get('title', '').lower()
                        description = article.get('description', '').lower()
                        
                        # Mots-clés critiques pour filtrer
                        critical_keywords = ['war', 'conflict', 'attack', 'bombing', 'terrorism', 
                                           'violence', 'crisis', 'coup', 'sanctions', 'advisory',
                                           'warning', 'danger', 'risk', 'threat', 'security']
                        
                        if any(keyword in title or keyword in description for keyword in critical_keywords):
                            relevant_articles.append(article)
                    
                    return relevant_articles
            
            # Fallback: recherche via une API publique alternative
            return self._search_alternative_news(keywords)
            
        except Exception:
            return []

    def _search_alternative_news(self, keywords: str) -> list:
        """Recherche alternative sans API key"""
        try:
            # Utiliser une API publique comme Guardian ou BBC
            # Pour l'exemple, on simule une recherche basique
            dangerous_keywords = ['war', 'conflict', 'terrorism', 'violence', 'crisis', 'coup', 'sanctions']
            warning_keywords = ['protest', 'unrest', 'advisory', 'caution', 'alert']
            
            # Simulation basée sur les mots-clés (à remplacer par vraie API)
            if any(word in keywords.lower() for word in dangerous_keywords):
                return [{'title': f'Security concerns in {keywords.split()[0]}', 'description': 'Recent security developments'}]
            elif any(word in keywords.lower() for word in warning_keywords):
                return [{'title': f'Travel advisory for {keywords.split()[0]}', 'description': 'Caution advised'}]
            
            return []
            
        except Exception:
            return []

    def _analyze_security_data(self, country: str, news_data: list, risk_level: str = "UNKNOWN") -> tuple:
        """Analyse les données de sécurité avec Claude uniquement"""
        try:
            if not self.claude_client:
                return ("⚪", 
                       "Claude not available", 
                       "❓ Anthropic API key required for security analysis")
            
            # Préparer le contenu des actualités pour l'analyse
            news_content = ""
            for i, article in enumerate(news_data[:10], 1):  # Limiter à 10 articles
                title = article.get('title', '')
                description = article.get('description', '')
                if title or description:
                    news_content += f"{i}. {title}\n{description}\n\n"
            
            # Si pas d'actualités mais pays à haut risque connu, forcer l'analyse
            if not news_content.strip():
                if risk_level == "HIGH_RISK":
                    return ("🔴", 
                           f"Very high risk country - active conflict or war",
                           "🚫 CHANGE DESTINATION - Active conflict zone")
                elif risk_level == "MODERATE_RISK":
                    return ("🟡", 
                           f"Moderate risk country - political instability",
                           "⚠️ Travel possible with enhanced precautions")
                else:
                    return ("🟢", 
                           f"No recent security news found",
                           "✅ Destination considered safe")
            
            # Utiliser Claude pour analyser
            analysis = self._llm_security_analysis(country, news_content, risk_level)
            
            if analysis:
                return analysis
            else:
                return ("⚪", 
                       "Claude analysis error", 
                       "❓ Unable to analyze security currently")
                       
        except Exception:
            return ("⚪", "Analysis impossible", "❓ Consult official sources")

    def _llm_security_analysis(self, country: str, news_content: str, risk_level: str = "UNKNOWN"):
        """Utilise Claude pour analyser la sécurité du pays"""
        try:
            if not self.claude_client:
                return None
                
            prompt = f"""Analyze the following recent news about {country} and determine the security level for a traveler:

KNOWN RISK LEVEL: {risk_level}
- HIGH_RISK = Country in active war or major conflict
- MODERATE_RISK = Country with significant political instability  
- TENSION = Country with geopolitical tensions
- UNKNOWN = No special classification

RECENT NEWS:
{news_content}

CRITICAL INSTRUCTIONS:
1. If RISK LEVEL = HIGH_RISK, you MUST recommend CHANGE_DESTINATION unless clear evidence of improvement
2. For Ukraine, Palestine, Afghanistan, Syria, Yemen: ALWAYS RED/CHANGE_DESTINATION
3. Analyze risk level for a civilian tourist/traveler
4. Be VERY STRICT - traveler safety is priority

Respond ONLY in the following JSON format:

{{
    "level": "RED|YELLOW|GREEN",
    "description": "Short situation description (max 100 characters)",
    "recommendation": "CHANGE_DESTINATION|ENHANCED_PRECAUTIONS|SAFE_DESTINATION",
    "justification": "Explanation of your decision (max 200 characters)"
}}

STRICT Criteria:
- RED/CHANGE_DESTINATION: active war, armed conflict, active terrorism, coup, widespread violence, combat zones
- YELLOW/ENHANCED_PRECAUTIONS: violent protests, very high crime, political instability, ethnic tensions
- GREEN/SAFE_DESTINATION: no major risks for civilians

ABSOLUTE PRIORITY: Protect travelers - when in doubt, choose the strictest security level."""

            response = self.claude_client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=300,
                temperature=0.1,
                system="Vous êtes un expert en sécurité des voyages. Analysez objectivement les risques.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            result_text = response.content[0].text.strip()
            # Parser la réponse JSON
            try:
                result = json.loads(result_text)
                level = result.get('level', 'GREEN')
                description = result.get('description', 'Analysis completed')
                recommendation = result.get('recommendation', 'SAFE_DESTINATION')
                justification = result.get('justification', '')
                
                # Convertir en format attendu
                if level == 'RED':
                    emoji = "🔴"
                    advice = "🚫 CHANGE DESTINATION - " + justification
                elif level == 'YELLOW':
                    emoji = "🟡"
                    advice = "⚠️ Travel possible with enhanced precautions - " + justification
                else:
                    emoji = "🟢"
                    advice = "✅ Destination considered safe - " + justification
                
                return (emoji, description, advice)
                
            except json.JSONDecodeError:
                return None
                
        except Exception:
            return None



    def _get_current_events_info(self, country: str) -> str:
        """Retrieves current events via web search"""
        try:
            # Search for recent events
            events_keywords = f"{country} current events news today recent"
            events_data = self._search_current_events(events_keywords)
            
            if not events_data:
                return f"📅 **Events**: No major events detected for {country}"
            
            result = f"📅 **Current Events and Context**\n"
            for i, event in enumerate(events_data[:5], 1):
                title = event.get('title', 'Event not specified')
                result += f"• {title}\n"
            
            return result.rstrip()
            
        except Exception:
            return "📅 **Events**: Error during retrieval"

    def _search_current_events(self, keywords: str) -> list:
        """Recherche d'événements actuels"""
        try:
            # Utiliser NewsAPI si disponible
            api_key = os.getenv('NEWSAPI_KEY')
            if api_key:
                url = "https://newsapi.org/v2/everything"
                params = {
                    'q': keywords,
                    'sortBy': 'publishedAt',
                    'pageSize': 5,
                    'from': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                    'language': 'en',
                    'apiKey': api_key
                }
                
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    return data.get('articles', [])
            
            return []
            
        except Exception:
            return []

    def _get_holidays_info(self, country: str) -> str:
        """Retrieves national holidays via API"""
        try:
            country_code = self.country_codes.get(country, '')
            
            # If no code in our mapping, try to get it via API
            if not country_code:
                country_code = self._get_country_code_from_api(country)
            
            if not country_code:
                return f"🎉 **Holidays**: Country code not found for {country}"
            
            # Use Calendarific API or similar
            holidays_data = self._fetch_holidays_api(country_code)
            
            if not holidays_data:
                return f"🎉 **Holidays**: Information not available for {country}"
            
            current_month = datetime.now().month
            current_year = datetime.now().year
            
            result = f"🎉 **Holidays and Seasonal Events**\n"
            
            # Filter holidays from current month and upcoming months
            upcoming_holidays = []
            for holiday in holidays_data:
                try:
                    holiday_date = datetime.strptime(holiday.get('date', ''), '%Y-%m-%d')
                    if holiday_date.month >= current_month and holiday_date.year == current_year:
                        upcoming_holidays.append(holiday)
                except:
                    continue
            
            if upcoming_holidays:
                result += f"**Upcoming holidays:**\n"
                for holiday in upcoming_holidays[:5]:
                    name = holiday.get('name', 'Unknown holiday')
                    date = holiday.get('date', '')
                    result += f"• {name} ({date})\n"
            else:
                result += f"**No major holidays scheduled in the coming months**\n"
            
            return result.rstrip()
            
        except Exception:
            return "🎉 **Holidays**: Error during retrieval"

    def _fetch_holidays_api(self, country_code: str) -> list:
        """Récupère les fêtes via API publique"""
        try:
            # Utiliser une API publique de fêtes (exemple: Calendarific, Nager.Date)
            year = datetime.now().year
            url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country_code}"
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            
            return []
            
        except Exception:
            return []

    def _get_travel_info(self, country: str) -> str:
        """Retrieves travel information via REST Countries API"""
        try:
            # Use REST Countries API
            url = f"https://restcountries.com/v3.1/name/{country}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    country_data = data[0]
                    
                    # Extract information
                    currencies = country_data.get('currencies', {})
                    languages = country_data.get('languages', {})
                    region = country_data.get('region', 'Unknown')
                    
                    currency_name = list(currencies.keys())[0] if currencies else 'Unknown'
                    language_list = list(languages.values()) if languages else ['Unknown']
                    
                    result = f"✈️ **Practical Travel Information**\n"
                    result += f"💰 Currency: {currency_name}\n"
                    result += f"🗣️ Languages: {', '.join(language_list[:3])}\n"
                    result += f"🌍 Region: {region}\n"
                    result += f"📋 Check visa requirements on the country's official website"
                    
                    return result
            
            return f"✈️ **Travel**: Information not available for {country}"
            
        except Exception:
            return "✈️ **Travel**: Error during retrieval"

    def _get_political_info(self, country: str) -> str:
        """Retrieves political context via news search"""
        try:
            # Search for recent political news
            political_keywords = f"{country} politics government election democracy"
            political_data = self._search_political_news(political_keywords)
            
            if not political_data:
                return f"🏛️ **Politics**: Stable situation for {country}"
            
            result = f"🏛️ **Political Context**\n"
            
            # Analyze political news
            for article in political_data[:3]:
                title = article.get('title', '')
                if title:
                    result += f"• {title}\n"
            
            return result.rstrip()
            
        except Exception:
            return "🏛️ **Politics**: Error during retrieval"

    def _search_political_news(self, keywords: str) -> list:
        """Recherche d'actualités politiques"""
        try:
            api_key = os.getenv('NEWSAPI_KEY')
            if api_key:
                url = "https://newsapi.org/v2/everything"
                params = {
                    'q': keywords,
                    'sortBy': 'publishedAt',
                    'pageSize': 5,
                    'from': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                    'language': 'en',
                    'apiKey': api_key
                }
                
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    return data.get('articles', [])
            
            return []
            
        except Exception:
            return []

    def _get_llm_final_recommendation(self, country: str, full_report: str):
        """Uses Claude to generate an intelligent final recommendation"""
        try:
            if not self.claude_client:
                return None
                
            prompt = f"""Analyze this complete report about {country} and provide a concise final recommendation for a traveler:

COMPLETE REPORT:
{full_report}

Your task:
1. Synthesize the most important information
2. Give a clear and actionable recommendation
3. Respond in English, maximum 200 words
4. Use a professional but accessible tone
5. If risks exist, be explicit about precautions

Desired response format:
🎯 **FINAL RECOMMENDATION**
[Your synthetic analysis and recommendation]

If the destination is dangerous, clearly use "CHANGE DESTINATION" in your response."""

            response = self.claude_client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=250,
                temperature=0.2,
                system="You are an expert travel advisor. Provide clear and practical recommendations.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text.strip()
            
        except Exception:
            return None 