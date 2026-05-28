from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI

import os
import requests
import tmdbsimple

import movie_storage_sql as storage

from movie_storage_sql import (
    add_movie,
    list_movies,
    delete_movie,
    get_showtimes,
    get_ticket_tiers,
    fetch_banner_movies,
    get_banner_movies
)

# =========================================
# LOAD ENV
# =========================================
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

tmdbsimple.API_KEY = TMDB_API_KEY

# =========================================
# APP INIT
# =========================================
app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=OPENAI_API_KEY)

# =========================================
# DATABASE INITIALIZATION & SEEDING
# =========================================
def initialize_and_seed_db():
    import sqlite3
    import datetime
    
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "movies.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # 1. Create default user if not exists
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO users (id, name) VALUES (1, 'Bolokaiemi')")
        print("Seeded default user 'Bolokaiemi' with ID 1.")
    
    # 2. Update existing movies with user_id = 1 if currently null
    cur.execute("UPDATE movies SET user_id = 1 WHERE user_id IS NULL")
    conn.commit()
    print("Assigned all unassigned movies in database to user_id = 1.")
    
    # 3. Seed movie_catalog if empty
    cur.execute("SELECT COUNT(*) FROM movie_catalog")
    if cur.fetchone()[0] == 0:
        catalog_movies = [
            (
                "Inception",
                "Sci-Fi / Action",
                "A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea into the mind of a C.O.",
                "https://image.tmdb.org/t/p/w500/o01v6t3N1w1Q9ofIY8zR7i4izwh.jpg",
                "https://www.youtube.com/embed/YoHD9XEInc0"
            ),
            (
                "Titanic",
                "Romance / Drama",
                "A seventeen-year-old aristocrat falls in love with a kind but poor artist aboard the luxurious, ill-fated R.M.S. Titanic.",
                "https://image.tmdb.org/t/p/w500/9g5tBjU1n4C9FY56V48gH7u7MOd.jpg",
                "https://www.youtube.com/embed/CHekzSiZcYQ"
            ),
            (
                "The Dark Knight",
                "Action / Thriller",
                "When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman must accept one of the greatest psychological and physical tests of his ability to fight injustice.",
                "https://image.tmdb.org/t/p/w500/qJ2tWGB25Ui1t6Ns3JAAU3Yl7nY.jpg",
                "https://www.youtube.com/embed/EXeTwQWrcwY"
            ),
            (
                "Interstellar",
                "Sci-Fi / Adventure",
                "A team of explorers travel through a wormhole in space in an attempt to ensure humanity's survival.",
                "https://image.tmdb.org/t/p/w500/gEU2Qv4zcyeOSKF3P8vCoJbpzbC.jpg",
                "https://www.youtube.com/embed/zSWdZAeeCgs"
            ),
            (
                "Avatar: The Way of Water",
                "Sci-Fi / Adventure",
                "Jake Sully lives with his newfound family formed on the extraterrestrial moon of Pandora. Once a familiar threat returns to finish what was previously started, Jake must work with Neytiri and the army of the Na'vi race to protect their home.",
                "https://image.tmdb.org/t/p/w500/t6zVee75h14k4hCuokq0szc265j.jpg",
                "https://www.youtube.com/embed/d9MyW72ELq0"
            )
        ]
        cur.executemany("""
            INSERT INTO movie_catalog (title, genre, description, poster, preview_link)
            VALUES (?, ?, ?, ?, ?)
        """, catalog_movies)
        conn.commit()
        print("Seeded movie_catalog table.")
        
        # Seed showtimes and ticket tiers for the seeded movies
        cur.execute("SELECT id FROM movie_catalog")
        movie_ids = [r[0] for r in cur.fetchall()]
        
        showtimes = []
        ticket_tiers = []
        
        today = datetime.date.today()
        dates = [
            today.strftime("%Y-%m-%d"),
            (today + datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
            (today + datetime.timedelta(days=2)).strftime("%Y-%m-%d")
        ]
        
        for m_id in movie_ids:
            # 3 showtimes per movie
            showtimes.append((m_id, dates[0], "14:30", "Screen 1 Standard"))
            showtimes.append((m_id, dates[1], "18:00", "Screen 2 IMAX"))
            showtimes.append((m_id, dates[2], "21:15", "Screen 3 VIP"))
            
            # 3 ticket tiers per movie
            ticket_tiers.append((m_id, "Standard", 12.0))
            ticket_tiers.append((m_id, "IMAX 3D", 18.0))
            ticket_tiers.append((m_id, "VIP Lounge", 25.0))
            
        cur.executemany("""
            INSERT INTO showtimes (movie_id, show_date, show_time, theater)
            VALUES (?, ?, ?, ?)
        """, showtimes)
        
        cur.executemany("""
            INSERT INTO ticket_tiers (movie_id, tier_name, price)
            VALUES (?, ?, ?)
        """, ticket_tiers)
        conn.commit()
        print("Seeded showtimes and ticket tiers tables.")
        
    conn.close()

# =========================================
# INIT DB
# =========================================
storage.create_table()
initialize_and_seed_db()

history = []

# =========================================
# COUNTRY FLAGS
# =========================================
def country_to_flag(country_name):

    countries = {
        "USA": "us",
        "United States": "us",
        "UK": "gb",
        "United Kingdom": "gb",
        "France": "fr",
        "Germany": "de",
        "Japan": "jp",
        "India": "in",
        "Canada": "ca",
        "South Korea": "kr",
        "China": "cn",
        "Italy": "it",
        "Spain": "es"
    }

    return countries.get(country_name, "")


# =========================================
# LOCAL POSTER DOWNLOAD PROXY (BYPASSES SCHOOL FIREWALLS)
# =========================================
def download_local_poster(title, original_url):
    import string
    
    # Create safe filename from movie title
    safe_chars = "-_" + string.ascii_letters + string.digits
    safe_title = "".join(c for c in title if c in safe_chars or c == " ").replace(" ", "_")
    filename = f"{safe_title}.jpg"
    
    poster_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "poster")
    filepath = os.path.join(poster_dir, filename)
    local_url = f"/static/poster/{filename}"
    
    # If the local file already exists, serve it instantly
    if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
        return local_url
        
    # Download the image from the internet in the background python process
    if original_url and original_url.startswith("http"):
        try:
            # Set a standard User-Agent to bypass download scrapers
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            res = requests.get(original_url, headers=headers, timeout=5)
            if res.status_code == 200:
                os.makedirs(poster_dir, exist_ok=True)
                with open(filepath, "wb") as f:
                    f.write(res.content)
                print(f"Downloaded local poster for: {title}")
                return local_url
        except Exception as e:
            print(f"Error downloading poster for {title}:", e)
            
    return original_url # fallback if download fails


# =========================================
# TMDB + OMDB ENRICHMENT
# =========================================
def enrich_movie(title):

    movie_data = {
        "title": title,
        "poster": "",
        "rating": "N/A",
        "year": "",
        "country": "",
        "director": "",
        "note": "",
        "trailer": ""
    }

    # -------------------------
    # TMDB SEARCH
    # -------------------------
    try:
        tmdb_url = (
            f"https://api.themoviedb.org/3/search/movie"
            f"?api_key={TMDB_API_KEY}&query={title}"
        )

        res = requests.get(tmdb_url).json()
        results = res.get("results", [])

        if results:

            movie = results[0]

            if movie.get("poster_path"):
                original_url = (
                    "https://image.tmdb.org/t/p/w500"
                    f"{movie['poster_path']}"
                )
                movie_data["poster"] = download_local_poster(title, original_url)

            movie_data["rating"] = movie.get("vote_average", "N/A")
            movie_data["note"] = movie.get("overview", "")

            if movie.get("release_date"):
                movie_data["year"] = movie["release_date"][:4]

            # trailer
            tmdb_id = movie.get("id")

            video_url = (
                f"https://api.themoviedb.org/3/movie/"
                f"{tmdb_id}/videos?api_key={TMDB_API_KEY}"
            )

            video_res = requests.get(video_url).json()

            for v in video_res.get("results", []):
                if v.get("site") == "YouTube" and v.get("type") == "Trailer":
                    movie_data["trailer"] = (
                        "https://www.youtube.com/embed/"
                        f"{v['key']}"
                    )
                    break

    except Exception as e:
        print("TMDB error:", e)

    # -------------------------
    # OMDB
    # -------------------------
    try:
        omdb_url = (
            f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&t={title}"
        )

        omdb = requests.get(omdb_url).json()

        movie_data["country"] = omdb.get("Country", "")
        movie_data["director"] = omdb.get("Director", "")

    except Exception as e:
        print("OMDB error:", e)

    return movie_data


# =========================================
# HOME PAGE
# =========================================
@app.route("/")
def home():
    import sqlite3
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "movies.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT title, year, rating, poster, trailer, note, country FROM movies")
    rows = cur.fetchall()
    conn.close()

    movies = []
    seen_titles = set()
    for row in rows:
        title = row[0]
        if title and title not in seen_titles:
            seen_titles.add(title)
            enriched = enrich_movie(title)
            
            poster = enriched.get("poster")
            if not poster and row[3] and row[3].startswith("http"):
                poster = download_local_poster(title, row[3])
            poster = poster or ""
            
            movies.append({
                "title": title,
                "year": enriched.get("year") or row[1] or "",
                "rating": enriched.get("rating") or row[2] or "N/A",
                "poster": poster,
                "trailer": enriched.get("trailer") or row[4] or "",
                "note": enriched.get("note") or row[5] or "",
                "country": enriched.get("country") or row[6] or ""
            })

    banners = get_banner_movies()

    return render_template(
        "index.html",
        movies=movies,
        banners=banners,
        country_to_flag=country_to_flag
    )


# =========================================
# CATALOG PAGE
# =========================================
@app.route("/catalog")
def catalog_route():
    stored_catalog = storage.list_catalog_movies()
    movies = []
    for row in stored_catalog:
        title = row[1]
        poster_url = row[4]
        local_poster = download_local_poster(title, poster_url)
        movies.append({
            "id": row[0],
            "title": title,
            "genre": row[2],
            "description": row[3],
            "poster": local_poster,
            "trailer_url": row[5],
            "year": "2023",
            "rating": "8.4"
        })
    banners = get_banner_movies()
    return render_template(
        "catalog.html",
        movies=movies,
        banners=banners,
        country_to_flag=country_to_flag
    )


# =========================================
# USER MOVIES COLLECTION PAGE
# =========================================
@app.route("/movies/<int:user_id>")
def user_movies_route(user_id):
    import sqlite3
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "movies.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT title, year, rating, poster, trailer, note, country FROM movies")
    rows = cur.fetchall()
    conn.close()

    movies = []
    seen_titles = set()
    for row in rows:
        title = row[0]
        if title and title not in seen_titles:
            seen_titles.add(title)
            enriched = enrich_movie(title)
            
            poster = enriched.get("poster")
            if not poster and row[3] and row[3].startswith("http"):
                poster = download_local_poster(title, row[3])
            poster = poster or ""
            
            movies.append({
                "title": title,
                "year": enriched.get("year") or row[1] or "N/A",
                "rating": enriched.get("rating") or row[2] or "N/A",
                "poster": poster,
                "trailer": enriched.get("trailer") or row[4] or "",
                "description": enriched.get("note") or row[5] or "No description available.",
                "director": enriched.get("director") or "Unknown"
            })
    banners = get_banner_movies()
    return render_template(
        "movies.html",
        movies=movies,
        banners=banners,
        country_to_flag=country_to_flag
    )


# =========================================
# TICKET PURCHASE CHECKOUT PAGE
# =========================================
@app.route("/purchase/<int:movie_id>")
def purchase(movie_id):
    import sqlite3
    conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)), "movies.db"))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM movie_catalog WHERE id = ?", (movie_id,))
    row = cur.fetchone()
    conn.close()
    
    if not row:
        return redirect("/catalog")
        
    movie_catalog_data = dict(row)
    showtimes = get_showtimes(movie_id)
    
    movie_data = {
        "id": movie_catalog_data["id"],
        "name": movie_catalog_data["title"],
        "poster": movie_catalog_data["poster"],
        "date": "Today",
        "time": "8:00 PM",
        "screen": "Screen 1"
    }
    
    if showtimes:
        movie_data["date"] = showtimes[0][0]
        movie_data["time"] = showtimes[0][1]
        movie_data["screen"] = showtimes[0][2]
        
    banners = get_banner_movies()
    return render_template(
        "purchase.html",
        movie=movie_data,
        banners=banners,
        country_to_flag=country_to_flag
    )


# =========================================
# API TICKET & SNACK PURCHASE CHECKOUT
# =========================================
@app.route("/api/purchase", methods=["POST"])
def api_purchase():
    try:
        data = request.get_json()
        user_id = data.get("user_id", 1)
        movie_id = data.get("movie_id", 1)
        qr_code_link = data.get("qr_code_link", "")
        popcorn_size = data.get("popcorn_size", "None")
        drink_size = data.get("drink_size", "None")
        concessions_total = data.get("concessions_total", 0.0)
        has_ticket = data.get("has_ticket", False)

        from movie_storage_sql import add_qr_purchase, add_concession_purchase
        
        # Save ticket QR code record if bought
        if has_ticket:
            add_qr_purchase(user_id, movie_id, qr_code_link)
            
        # Save snack concession record if popcorn/drinks/snacks bought
        if popcorn_size != "None" or drink_size != "None" or concessions_total > 0:
            add_concession_purchase(user_id, movie_id, popcorn_size, drink_size, concessions_total)

        return jsonify({"success": True, "message": "Purchase saved successfully!"})
    except Exception as e:
        print("API PURCHASE ERROR:", e)
        return jsonify({"success": False, "message": str(e)})


# =========================================
# REFRESH BANNERS ROUTE
# =========================================
@app.route("/refresh_banners")
def refresh_banners_route():
    try:
        fetch_banner_movies()
    except Exception as e:
        print("Refresh banners error:", e)
    return redirect("/")


# =========================================
# CHAT
# =========================================
@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json() or {}
    user_message = data.get("message", "")
    client_history = data.get("history", [])

    messages = [
        {"role": "system", "content": "You are CinemaBot 🎬. Always respond in the same language as the user's message (e.g., respond in German if they ask in German, French if they ask in French, Spanish if they ask in Spanish, and English if they ask in English)."}
    ] + client_history + [
        {"role": "user", "content": user_message}
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            temperature=0.8
        )

        reply = response.choices[0].message.content

        return jsonify({
            "reply": reply.replace("\n", "<br>")
        })

    except Exception as e:
        print("CHAT ERROR:", e)
        return jsonify({"reply": "⚠️ OpenAI error"})


# =========================================
# ADD MOVIE
# =========================================
@app.route("/add_movie", methods=["POST"])
def add_movie_route():

    try:
        add_movie(
            request.form.get("user_id"),
            request.form.get("title"),
            request.form.get("year"),
            request.form.get("rating"),
            request.form.get("poster"),
            request.form.get("trailer"),
            request.form.get("note"),
            request.form.get("country")
        )

        return jsonify({"success": True})

    except Exception as e:
        print("ADD ERROR:", e)
        return jsonify({"success": False})


# =========================================
# DELETE MOVIE
# =========================================
@app.route("/delete_movie", methods=["POST"])
def delete_movie_route():

    try:
        delete_movie(
            request.form.get("user_id"),
            request.form.get("title")
        )

        return jsonify({"success": True})

    except Exception as e:
        print("DELETE ERROR:", e)
        return jsonify({"success": False})


# =========================================
# SHOWTIMES
# =========================================
@app.route("/showtimes/<int:movie_id>")
def showtimes_route(movie_id):

    showtimes = get_showtimes(movie_id)

    return jsonify({
        "success": True,
        "showtimes": [
            {
                "show_date": s[0],
                "show_time": s[1],
                "theater": s[2]
            }
            for s in showtimes
        ]
    })


# =========================================
# TICKET TIERS
# =========================================
@app.route("/ticket_tiers/<int:movie_id>")
def ticket_tiers_route(movie_id):

    tiers = get_ticket_tiers(movie_id)

    return jsonify({
        "success": True,
        "ticket_tiers": [
            {
                "tier_name": t[0],
                "price": t[1]
            }
            for t in tiers
        ]
    })





# =========================
# ICON TOOLBAR ROUTES
# =========================

from flask import Flask, jsonify, render_template



# Like
@app.route("/like")
def like():
    return jsonify({
        "status": "success",
        "message": "Movie liked 👍"
    })


# Disike
@app.route("/dislike")
def dislike():
    return jsonify({
        "status": "success",
        "message": "Movie disliked 👎"
    })


# SHARE
@app.route("/share")
def share():
    return jsonify({
        "status": "success",
        "message": "Share link copied 🔗"
    })


# BOOKMARK (COMING SOON)
@app.route("/bookmark")
def bookmark():
    return jsonify({
        "status": "disabled",
        "message": "Bookmark feature coming soon 🔖"
    })


# SAVE (COMING SOON)
@app.route("/save")
def save():
    return jsonify({
        "status": "disabled",
        "message": "Save feature coming soon 💾"
    })




# About Page Route
@app.route('/about')
def about():
    return render_template('about.html')



# Contact Page Route
@app.route('/contact')
def contact():
    return render_template('contact.html')


# Contact Form Submission Route
@app.route('/submit_contact', methods=['POST'])
def submit_contact():
    name = request.form.get('name')
    email = request.form.get('email')
    message = request.form.get('message')

    # You can process or save the form data here
    print(f"Name: {name}")
    print(f"Email: {email}")
    print(f"Message: {message}")

    return "Message sent successfully!"




# School Project Page Route
@app.route('/school-project')
def school_project():
    return render_template('school-project.html')






# =========================================
# RUN APP
# =========================================
if __name__ == "__main__":

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )