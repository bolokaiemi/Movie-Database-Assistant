import os
import sys
# Reconfigure stdout to support unicode emoji printing in Windows terminal
sys.stdout.reconfigure(encoding='utf-8')
# Set up import path to point to root directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app import fetch_movie_metadata_online

print("--- Testing fetch_movie_metadata_online for 'The Shine' ---")
res = fetch_movie_metadata_online("The Shine", "Horror")
print("Title:", res.get("title"))
print("Genre:", res.get("genre"))
print("Description:", res.get("description"))
print("Poster URL:", res.get("poster_url"))
print("Trailer URL:", res.get("trailer_url"))

print("\n--- Testing fetch_movie_metadata_online with long description (The Shining) ---")
res2 = fetch_movie_metadata_online("The Shining")
print("Title:", res2.get("title"))
print("Description length:", len(res2.get("description", "")))
print("Description:", res2.get("description"))

print("\n--- Testing fetch_movie_metadata_online for fake movie 'Antigravity Agents' (OpenAI Fallback) ---")
res3 = fetch_movie_metadata_online("Antigravity Agents", "Sci-Fi")
print("Title:", res3.get("title"))
print("Genre:", res3.get("genre"))
print("Description:", res3.get("description"))

