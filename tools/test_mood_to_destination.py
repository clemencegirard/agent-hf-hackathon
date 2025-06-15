from tools.mood_to_need import MoodToNeedTool, claude_mood_to_need_model
from tools.need_to_destination import NeedToDestinationTool, claude_need_to_destination_model
import json

mood_tool = MoodToNeedTool(model=claude_mood_to_need_model)
mood = "I'm feeling stuck in a routine and need change"
# mood = "I feel overwhelmed and burned out."
# mood = "I just got out of a break up"

need = mood_tool(mood=mood)
print(f"Mood: {mood}")
print("Need:", need)

destination_tool = NeedToDestinationTool(model=claude_need_to_destination_model, departure_airport="CDG")
try:
    destinations = destination_tool(need=need)
    print("\n→ Suggested Destinations:")
    for dest in destinations:
        print(json.dumps(dest, indent=2))
except ValueError as e:
    print(f"Error parsing Claude output: {e}")