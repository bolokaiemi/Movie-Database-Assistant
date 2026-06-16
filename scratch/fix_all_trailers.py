import os
import sqlite3
import requests
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "movies.db")
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Get all movies from catalog
cur.execute("SELECT id, title, trailer_url FROM movie_catalog")
catalog_movies = cur.fetchall()

# Get all user movies
cur.execute("SELECT id, title, trailer_url FROM movies")
user_movies = cur.fetchall()

tmdb_key = os.getenv("TMDB_API_KEY", "bdc72992529ba332516d99262db8ca95")

print(f"Starting trailer updates for {len(catalog_movies)} catalog movies and {len(user_movies)} user movies...")

# We can cache TMDB movie trailers to avoid making repeated requests for the same movie
trailer_cache = {}

def get_trailer_from_tmdb(title):
    if title.lower() in trailer_cache:
        return trailer_cache[title.lower()]
    
    try:
        search_url = f"https://api.themoviedb.org/3/search/movie?api_key={tmdb_key}&query={urllib.parse.quote(title)}"
        r = requests.get(search_url, timeout=5)
        if r.status_code == 200:
            search_data = r.json()
            results = search_data.get("results", [])
            if results:
                matched_result = results[0]
                for result in results:
                    if result.get("title", "").lower() == title.lower():
                        matched_result = result
                        break
                
                movie_id = matched_result["id"]
                videos_url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={tmdb_key}"
                v_r = requests.get(videos_url, timeout=5)
                if v_r.status_code == 200:
                    videos = v_r.json().get("results", [])
                    # Look for official trailer
                    for video in videos:
                        if video.get("site") == "YouTube" and video.get("type") in ["Trailer"]:
                            key = video.get("key")
                            if key:
                                trailer_cache[title.lower()] = f"https://www.youtube.com/embed/{key}"
                                return trailer_cache[title.lower()]
                    # Look for Teaser/Clip
                    for video in videos:
                        if video.get("site") == "YouTube" and video.get("type") in ["Teaser", "Clip"]:
                            key = video.get("key")
                            if key:
                                trailer_cache[title.lower()] = f"https://www.youtube.com/embed/{key}"
                                return trailer_cache[title.lower()]
    except Exception as e:
        print(f"Error fetching TMDB trailer for {title}:", e)
    
    trailer_cache[title.lower()] = None
    return None

updated_catalog_count = 0
for mid, title, old_url in catalog_movies:
    new_url = get_trailer_from_tmdb(title)
    if new_url:
        if new_url != old_url:
            cur.execute("UPDATE movie_catalog SET trailer_url = ? WHERE id = ?", (new_url, mid))
            print(f"Catalog Updated: '{title}'\n  Old: {old_url}\n  New: {new_url}")
            updated_catalog_count += 1

updated_user_count = 0
for mid, title, old_url in user_movies:
    new_url = get_trailer_from_tmdb(title)
    if new_url:
        # Clean up any suffix query params or extra text in old_url
        clean_old_url = old_url.split('?')[0].split('"')[0].strip() if old_url else ""
        if new_url != clean_old_url:
            cur.execute("UPDATE movies SET trailer_url = ? WHERE id = ?", (new_url, mid))
            print(f"User Movie Updated: '{title}' (ID {mid})\n  Old: {old_url}\n  New: {new_url}")
            updated_user_count += 1

conn.commit()
conn.close()
print(f"Trailer update completed! Updated {updated_catalog_count} catalog entries and {updated_user_count} user movies.")
