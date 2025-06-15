#!/usr/bin/env python3

from tools.mood_to_need import MoodToNeedTool, claude_mood_to_need_model
from tools.need_to_destination import NeedToDestinationTool, claude_need_to_destination_model
from tools.weather_tool import WeatherTool
from tools.country_info_tool import CountryInfoTool
from tools.find_flight import FlightsFinderTool

def test_tools():
    print("🧪 Testing individual tools...\n")
    
    # Test 1: MoodToNeed
    print("1️⃣ Testing MoodToNeed...")
    mood_tool = MoodToNeedTool(model=claude_mood_to_need_model)
    need = mood_tool.forward(mood="happy")
    print(f"   Input: 'happy' → Output: '{need}'\n")
    
    # Test 2: NeedToDestination
    print("2️⃣ Testing NeedToDestination...")
    destination_tool = NeedToDestinationTool(model=claude_need_to_destination_model)
    destinations = destination_tool.forward(need=need)
    print(f"   Input: '{need}' → Output: {destinations}\n")
    
    # Test 3: WeatherTool
    print("3️⃣ Testing WeatherTool...")
    weather_tool = WeatherTool()
    if destinations and len(destinations) > 0:
        first_dest = destinations[0]["destination"]
        weather = weather_tool.forward(location=first_dest)
        print(f"   Input: '{first_dest}' → Output: {weather[:200]}...\n")
    
    # Test 4: CountryInfoTool
    print("4️⃣ Testing CountryInfoTool...")
    country_tool = CountryInfoTool()
    if destinations and len(destinations) > 0:
        # Extract country from destination
        dest_parts = destinations[0]["destination"].split(", ")
        if len(dest_parts) > 1:
            country = dest_parts[1]
            safety = country_tool.forward(country=country, info_type="security")
            print(f"   Input: '{country}' → Output: {safety[:200]}...\n")
    
    # Test 5: FlightsFinderTool
    print("5️⃣ Testing FlightsFinderTool...")
    flights_tool = FlightsFinderTool()
    if destinations and len(destinations) > 0:
        dest_airport = destinations[0]["departure"]["to_airport"]
        flights = flights_tool.forward(
            departure_airport="CDG",
            arrival_airport=dest_airport,
            outbound_date="2025-06-15",
            return_date="2025-06-22"
        )
        print(f"   Input: CDG → {dest_airport} → Output: {flights[:200]}...\n")
    
    print("✅ All tools tested!")

if __name__ == "__main__":
    test_tools() 