from smolagents.tools import tool

@tool
def mood_to_need(mood: str) -> str:
    """
    Map a mood to a need.

    Args:
        mood (str): The current emotional state of the user.

    Returns:
        str: A description of what the user needs based on the mood.
    """
    return "You need relaxation and nature."

@tool
def need_to_destination(need: str) -> str:
    """
    Map a need to a destination.

    Args:
        need (str): The user's identified need (e.g., relaxation, adventure).

    Returns:
        str: A suggested destination that fulfills the need.
    """
    return "Bali, Indonesia"

@tool
def get_weather(dest: str) -> str:
    """
    Get weather forecast for a destination.

    Args:
        dest (str): The destination location.

    Returns:
        str: A weather forecast for the given destination.
    """
    return "Sunny and 28°C"

@tool
def get_flights(dest: str) -> str:
    """
    Get flight options for a destination.

    Args:
        dest (str): The destination location.

    Returns:
        str: A list of flight options for the destination.
    """
    return "Flight from Paris to Bali: €600 roundtrip"

@tool
def final_wrap(info: str) -> str:
    """
    Create a final wrap-up message.

    Args:
        info (str): Summary information about the destination and travel.

    Returns:
        str: A personalized wrap-up message.
    """
    return f"Bali sounds like a perfect place for relaxation with great weather and affordable flights!"

@tool
def final_answer_tool(answer: str) -> str:
    """
    Provides a final answer to the user.

    Args:
        answer (str): The final recommendation or conclusion.

    Returns:
        str: The same final answer.
    """
    return answer
    
    