import json
import os
import re
from typing import Any

from langchain.agents import create_agent
from langchain_core.runnables import RunnableLambda
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from services.cinema import MovieGuide
from services.weather import IndianWeather


weather_service = IndianWeather()
movie_guide = MovieGuide()


@tool
def look_up_city_weather(city: str) -> str:
    """Look up current temperature, conditions, humidity, and wind for an Indian city."""
    return weather_service.report(city)


@tool
def pick_indian_movies(genre: str) -> str:
    """Recommend Indian movies that match a genre such as action, comedy, or romance."""
    return movie_guide.recommend(genre)


@tool
def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert a Celsius temperature to Fahrenheit."""
    return round((celsius * 9 / 5) + 32, 1)


class ChatRequest(BaseModel):
    input: str = Field(description="A weather or Indian movie question")


def _to_conversation(request: Any) -> dict[str, Any]:
    message = request["input"] if isinstance(request, dict) else request.input
    return {"messages": [("user", message)]}


def _final_text(state: Any) -> str:
    if not isinstance(state, dict):
        return str(state)

    messages = state.get("messages", [])
    for message in reversed(messages):
        if getattr(message, "type", None) == "ai":
            content = getattr(message, "content", "")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                return "\n".join(
                    part.get("text", "") if isinstance(part, dict) else str(part)
                    for part in content
                ).strip()
    return "I couldn't prepare an answer. Please try again."


def _quick_answer(message: str) -> str | None:
    """Answer the assistant's two focused tasks directly and reliably."""
    movie_words = re.search(r"\b(movie|movies|film|films|cinema|recommend)\b", message, re.I)
    if movie_words:
        genre_patterns = (
            ("sci-fi", r"\b(?:sci[- ]fi|science fiction)\b"),
            ("thriller", r"\bthriller\b"),
            ("comedy", r"\bcomedy\b"),
            ("action", r"\baction\b"),
            ("drama", r"\bdrama\b"),
            ("family", r"\bfamily\b"),
            ("horror", r"\bhorror\b"),
            ("romance", r"\b(?:romance|romantic)\b"),
        )
        genre = next((name for name, pattern in genre_patterns if re.search(pattern, message, re.I)), None)
        if genre:
            return movie_guide.recommend(genre)
        return "Which genre are you in the mood for? Try action, comedy, drama, family, horror, romance, sci-fi, or thriller."

    if re.search(r"\b(weather|temperature|forecast)\b", message, re.I):
        match = re.search(
            r"\b(?:in|for|at)\s+([A-Za-z][A-Za-z .'-]*?)(?:\s+(?:right now|currently|today|please)\b|[?.!,]|$)",
            message,
            re.I,
        )
        if not match:
            return "Which Indian city should I check?"

        raw_report = weather_service.report(match.group(1).strip())
        try:
            report = json.loads(raw_report)
        except (TypeError, ValueError):
            return raw_report
        if "temperature_celsius" not in report:
            return raw_report

        temperature = report["temperature_celsius"]
        details = (
            f"Weather for {report['location']}: {temperature}°C, {report['condition']}; "
            f"humidity {report['humidity_percent']}%; wind {report['wind_speed_kmh']} km/h."
        )
        if re.search(r"\b(fahrenheit|\bF\b)\b", message, re.I):
            details += f" That's {celsius_to_fahrenheit.invoke({'celsius': float(temperature)})}°F."
        return details
    return None


def _respond(conversation: dict[str, Any]) -> str:
    message = conversation["messages"][-1][1]
    direct = _quick_answer(message)
    if direct is not None:
        return direct
    return _final_text(agent.invoke(conversation))


def make_chat_chain():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("Set GEMINI_API_KEY in .env or the hosting environment.")

    model = ChatGoogleGenerativeAI(
        model=os.environ.get("GEMINI_MODEL", "gemma-4-31b-it"),
        api_key=key,
        temperature=0,
        retries=1,
        request_timeout=30,
    )
    agent = create_agent(
        model=model,
        tools=[look_up_city_weather, pick_indian_movies, celsius_to_fahrenheit],
        system_prompt=(
            "You are India Weather & Movies Assistant. Help with current weather for Indian cities and Indian movies by genre. "
            "Use the relevant tool for every weather or recommendation request. For weather, state the city and state, temperature in Celsius, conditions, humidity, and wind speed in km/h. "
            "Include Fahrenheit if requested. Never invent live weather. Keep replies concise and friendly. "
            "For unrelated topics, say: 'I can help with Indian city weather and Indian movie recommendations.'"
        ),
    )

    # Run the synchronous provider client in LangChain's worker pool so a
    # Windows event loop/network policy cannot block the Gemini socket call.
    return (
        RunnableLambda(_to_conversation)
        | RunnableLambda(_respond)
    ).with_types(input_type=ChatRequest, output_type=str)
