from smolagents import CodeAgent, LiteLLMModel
from tools.mood_to_need import MoodToNeedTool, claude_mood_to_need_model
from tools.need_to_destination import NeedToDestinationTool, claude_need_to_destination_model
from tools.weather_tool import WeatherTool
from tools.find_flight import FlightsFinderTool
from tools.final_answer import FinalAnswerTool
from tools.country_info_tool import CountryInfoTool
from smolagents import CodeAgent,DuckDuckGoSearchTool, HfApiModel,load_tool,tool
from smolagents import MultiStepAgent, ActionStep, AgentText, AgentImage, AgentAudio, handle_agent_output_types
from Gradio_UI import GradioUI
import yaml
# from tools.mock_tools import MoodToNeedTool, NeedToDestinationTool, WeatherTool, FlightsFinderTool, FinalAnswerTool

# Initialize Claude model via Hugging Face
model = LiteLLMModel(
    model_id="claude-3-opus-20240229",
    temperature=0.7,
    max_tokens=2048
)

# Load prompt templates
with open("prompts.yaml", "r") as f:
    prompt_templates = yaml.safe_load(f)

# Define the agent with all tools
# agent = CodeAgent(
#     model=model,
#     tools=[
#         MoodToNeedTool(),          # Step 1: Mood → Need
#         NeedToDestinationTool(),   # Step 2: Need → Destination
#         WeatherTool(),             # Step 3: Weather for destination
#         FlightsFinderTool(),       # Step 4: Destination → Flights           # Step 5: Claude wrap
#         FinalAnswerTool()       # Required final output
#     ],
#     max_steps=6,
#     verbosity_level=1,
#     prompt_templates=prompt_templates
# )

agent = CodeAgent(
    model=model,
    tools=[
        MoodToNeedTool(model=claude_mood_to_need_model),          # Step 1: Mood → Need
        NeedToDestinationTool(model=claude_need_to_destination_model),   # Step 2: Need → Destination
        WeatherTool(),             # Step 3: Weather for destination
        FlightsFinderTool(),       # Step 4: Destination → Flights           # Step 5: Claude wrap
        FinalAnswerTool(),      # Required final output
        CountryInfoTool()           # Step 6: Country info
    ],
    max_steps=10,
    verbosity_level=1,
    prompt_templates=prompt_templates
)

# Launch the Gradio interface
GradioUI(agent).launch()
