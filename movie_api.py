import requests
import sqlite3
from datetime import datetime
import os
from dotenv import load_dotenv
# LOAD ENV VARIABLES
# =========================
load_dotenv()
# =========================

# ==========================================
# OMDb API (Your Existing Movie Search API)
# ==========================================
OMDB_API_KEY = os.environ.get("OMDB_API_KEY")


def fetch_movie(title):
    """Fetch single movie details from OMDb API."""

    url = f"http://www.omdbapi.com/?t={title}&apikey={OMDB_API_KEY}"

    try:
        response = requests.get(url)
        data = response.json()

        print(data, "getting data")

        # Movie not found
        if data.get("Response") == "False":
            return None

        # Clean return format
        return {
            "title": data.get("Title"),
            "year": int(data.get("Year")) if data.get("Year") else 0,
            "rating": float(data.get("imdbRating"))
            if data.get("imdbRating") not in (None, "N/A")
            else 0.0,
            "plot": data.get("Plot", "N/A"),
            "poster": data.get("Poster", "")
        }

    except Exception as e:
        print("OMDb API error:", e)
        return None


# ==========================================
# TMDb API Configuration
# ==========================================
# Get FREE API Key:
# https://www.themoviedb.org/settings/api

TMDB_API_KEY = "YOUR_TMDB_API_KEY"

BASE_URL = "https://api.themoviedb.org/3"

IMAGE_BASE_URL = "https://image.tmdb.org/t/p/original"

