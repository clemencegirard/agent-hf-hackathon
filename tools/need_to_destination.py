from smolagents.tools import Tool
from anthropic import Anthropic
import os
import json
from dotenv import load_dotenv
load_dotenv()  # Loads variables from .env into environment

class NeedToDestinationTool(Tool):
    name = "NeedToDestination"
    inputs = {
        "need": {"type": "string", "description": "User's travel need as text"},
    }
    output_type = "array"
    description = "Suggests destinations and flight info based on user need."

    def __init__(self, model: callable, departure_airport: str = "CDG") -> None:
        super().__init__()
        self.model = model
        self.departure_airport = departure_airport

    def forward(self, need: str) -> list[dict]:
        prompt = f"""
            You are a travel agent AI.

            Based on the user's need: "{need}",
            suggest 2-3 travel destinations with round-trip flight information.

            Return the output as valid JSON in the following format:

            [
            {{
                "destination": "DestinationName",
                "departure": {{
                "date": "YYYY-MM-DD",
                "from_airport": "{self.departure_airport}",
                "to_airport": "XXX"
                }},
                "return": {{
                "date": "YYYY-MM-DD",
                "from_airport": "XXX",
                "to_airport": "{self.departure_airport}"
                }}
            }},
            ...
            ]

            DO NOT add explanations, only return raw JSON.
            """
        result = self.model(prompt)
        try:
            destinations = json.loads(result.strip())
        except json.JSONDecodeError:
            raise ValueError("Could not parse LLM output to JSON.")

        return destinations
    

client = Anthropic(api_key=os.getenv("ANTROPIC_KEY"))

def claude_need_to_destination_model(prompt: str) -> str:
    message = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1024,
        temperature=0.7,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return message.content[0].text