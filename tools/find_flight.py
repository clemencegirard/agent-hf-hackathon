import os
from typing import Optional
from smolagents.tools import Tool
import serpapi
from dotenv import load_dotenv
load_dotenv()  # Loads variables from .env into environment



class FlightsFinderTool(Tool):
    name = "flights_finder"
    description = "Find flights using the Google Flights engine."
    inputs = {
        'departure_airport': {'type': 'string', 'description': 'Departure airport code (IATA)'},
        'arrival_airport': {'type': 'string', 'description': 'Arrival airport code (IATA)'},
        'outbound_date': {'type': 'string', 'description': 'Outbound date in YYYY-MM-DD format'},
        'return_date': {'type': 'string', 'description': 'Return date in YYYY-MM-DD format'},
        'adults': {'type': 'integer', 'default': 1, 'nullable': True, 'description': 'Number of adults'},
        'children': {'type': 'integer', 'default': 0, 'nullable': True, 'description': 'Number of children'},
    }
    output_type = "string"

    @staticmethod
    def find_flight(
        departure_airport: Optional[str] = None,
        arrival_airport: Optional[str] = None,
        date: Optional[str] = None,
        adults: Optional[int] = 1,
        children: Optional[int] = 0,
    ) -> str:
        """
        Finds the cheapest one-way flight for a given route and date.

        Args:
            departure_airport (str): Departure airport code (IATA)
            arrival_airport (str): Arrival airport code (IATA)
            date (str): Flight date in YYYY-MM-DD format
            adults (int): Number of adults
            children (int): Number of children
            infants_in_seat (int): Number of infants in seat
            infants_on_lap (int): Number of lap infants

        Returns:
            str: Formatted string with cheapest flight details
        """
        params = {
            'api_key': os.getenv("SERPAPI_API_KEY"),
            'engine': 'google_flights',
            'hl': 'en',
            'gl': 'us',
            'departure_id': departure_airport,
            'arrival_id': arrival_airport,
            'outbound_date': date,
            'currency': 'USD',
            'adults': adults,
            'children': children,
            'type': 2,
        }

        try:
            search = serpapi.search(params)
            flights = search.data.get("best_flights", [])
            if not flights:
                return "No flights found."

            # Find the flight with the lowest price
            cheapest = min(flights, key=lambda f: f.get("price", float("inf")))

            if not cheapest.get("flights"):
                return "No flight segments found."

            flight = cheapest["flights"][0]
            dep = flight["departure_airport"]
            arr = flight["arrival_airport"]
            dep_time = dep["time"]
            arr_time = arr["time"]
            duration = flight["duration"]
            airline = flight.get("airline", "Unknown")
            price = cheapest["price"]

            hours = duration // 60
            minutes = duration % 60
            duration_str = f"{hours}h {minutes}m"

            return (
                f"From {dep['id']} at {dep_time} → {arr['id']} at {arr_time} | "
                f"Duration: {duration_str}\nAirline: {airline} | Price: ${price}"
            )

        except Exception as e:
            return f"Error occurred: {e}"
        
    def forward(
        self,
        departure_airport: str,
        arrival_airport: str,
        outbound_date: str,
        return_date: str,
        adults: int = 1,
        children: int = 0,
    ) -> str:
        outbound = self.find_flight(
            departure_airport=departure_airport,
            arrival_airport=arrival_airport,
            date=outbound_date,
            adults=adults,
            children=children,
        )

        inbound = self.find_flight(
            departure_airport=arrival_airport,
            arrival_airport=departure_airport,
            date=return_date,
            adults=adults,
            children=children,
        )

        return f"✈️ Outbound Flight:\n{outbound}\n\n🛬 Inbound Flight:\n{inbound}"

        
    def __init__(self, *args, **kwargs):
        self.is_initialized = False

