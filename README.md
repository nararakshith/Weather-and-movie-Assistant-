# India Weather & Movies Assistant

A conversational assistant for current weather in Indian cities and Indian movie recommendations by genre. The web interface is served by FastAPI and sends chat messages to a LangChain agent through LangServe.

## Features

- Current Indian city weather: temperature, conditions, humidity, and wind speed.
- Movie suggestions by genre, including action, comedy, drama, family, horror, romance, sci-fi, and thriller.
- Follow-up questions, suggested prompts, and a clear-chat control.
- Open-Meteo for city search and forecasts, with wttr.in as a forecast fallback.

## Run locally

1. Install Python 3.10 or newer.
2. Install dependencies: `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and add your Google Gemini API key after `GEMINI_API_KEY=`.
4. Start the app: `python app.py`.
5. Open `http://localhost:8765`.

The website is served at `/`. The LangServe endpoint remains available at `/agent`.

## Deploy to Render

The repository includes `render.yaml` with the Python build command, Uvicorn start command, and `/health` check. Connect this repository to a Render Web Service (or use Render Blueprint) and add `GEMINI_API_KEY` in the service's Environment settings. Do not commit the secret.

For a manually configured Web Service, use:

- **Build command:** `pip install -r requirements.txt`
- **Start command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
- **Health check path:** `/health`

## Code layout

- `assistant.py` defines the LangChain tools and chat agent.
- `services/weather.py` handles Indian city lookup and live weather providers.
- `services/cinema.py` contains the independent genre-based Indian movie guide.
- `static/` contains the responsive chat website.

## Configuration

- `GEMINI_API_KEY` — required Google AI API key; read from `.env` locally or your hosting provider's environment settings.
- `GEMINI_MODEL` — optional Gemini model override; defaults to the model configured in `app.py`.
- `PORT` — optional server port; defaults to `8765` locally. Hosting platforms such as Render provide this automatically.

## Project details

- **Model:** Google Gemini through `langchain-google-genai`.
- **Frameworks:** Python, FastAPI, LangChain, LangServe, and Pydantic.
- **Weather APIs:** Open-Meteo Geocoding API, Open-Meteo Forecast API, and wttr.in fallback.
- **Retrieval:** No RAG pipeline or vector store; weather is fetched from APIs and movie suggestions come from this project's own curated guide.

## Example prompts

- “What is the weather in Vizianagaram?”
- “Give me some action movies.”

Weather data availability depends on the external providers. Movie recommendations are limited to the titles and genres configured in `search_movies`.
