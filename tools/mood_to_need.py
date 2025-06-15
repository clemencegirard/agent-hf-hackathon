from smolagents.tools import Tool
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
import os
from dotenv import load_dotenv
load_dotenv()  # Loads variables from .env into environment
class MoodToNeedTool(Tool):
    """
    A tool that converts user mood descriptions into vacation needs using an LLM.

    Attributes:
        model: A callable language model used to generate the output.
    """
    name = "MoodToNeed"
    inputs = {
    "mood": {"type": "string", "description": "User's mood as text"},
}
    output_type = "string"

    description = "Converts user mood into a travel-related need."

    def __init__(self, model: callable) -> None:
        """
        Args:
            model: A callable language model with a __call__(str) -> str interface.
        """
        super().__init__()
        self.model = model

    def forward(self, mood: str) -> str:
        """
        Generates a vacation need from a user mood string.

        Args:
            mood: A string describing the user's emotional state.

        Returns:
            A short string describing the travel-related need.
        """
        prompt = (
            f"Given the user's mood, suggest a travel need.\n"
            f'Mood: "{mood}"\n'
            f'Return only the need, no explanation.\n'
            f'Example:\n'
            f'Mood: "I am exhausted" → Need: "A calm wellness retreat"\n'
            f'Mood: "{mood}"\n'
            f'Need:'
        )
        response = self.model(prompt)
        return response.strip()

client = Anthropic(api_key=os.getenv("ANTROPIC_KEY"))

def claude_mood_to_need_model(prompt: str) -> str:
    message = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1024,
        temperature=0.7,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return message.content[0].text