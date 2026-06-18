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
    from werkzeug.security import generate_password_hash
    
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "movies.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Create admin credentials table if not exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admin_credentials (
            username TEXT PRIMARY KEY,
            password_hash TEXT,
            reset_code TEXT,
            reset_expiry TIMESTAMP
        )
    """)
    conn.commit()
    
    # Seed default admin credentials if empty
    cur.execute("SELECT COUNT(*) FROM admin_credentials")
    if cur.fetchone()[0] == 0:
        admin_user = os.getenv("ADMIN_USERNAME") or os.getenv("admin_user") or "Admin"
        admin_pass = os.getenv("ADMIN_PASSWORD") or os.getenv("admin_password") or "Admin.123"
        hashed = generate_password_hash(admin_pass)
        cur.execute("INSERT INTO admin_credentials (username, password_hash) VALUES (?, ?)", (admin_user, hashed))
        conn.commit()
        print(f"Seeded default admin credentials in database: {admin_user}")
        
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
            INSERT INTO movie_catalog (title, genre, description, poster_url, trailer_url)
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
        
    # 4. Seed default comments if empty
    cur.execute("SELECT COUNT(*) FROM movie_comments")
    if cur.fetchone()[0] == 0:
        default_comments = [
            (1, "Sarah Johnson", "I really enjoyed the movie recommendations on this page. Inception is an absolute masterpiece!", 5),
            (1, "Michael Brown", "The visual effects and Christopher Nolan's directing in Inception are top-notch.", 5),
            (2, "Emily Davis", "Titanic is a timeless classic. The chemistry between Leo and Kate is amazing!", 5),
            (3, "John Doe", "Heath Ledger's Joker is legendary. The Dark Knight is hands down the best superhero movie.", 5),
            (4, "Alice Smith", "Interstellar made me cry. Hans Zimmer's soundtrack is out of this world!", 5),
            (5, "David Wilson", "Avatar: The Way of Water is a visual spectacle. Pandora looks stunning!", 4)
        ]
        cur.executemany("""
            INSERT INTO movie_comments (movie_id, username, comment, rating)
            VALUES (?, ?, ?, ?)
        """, default_comments)
        conn.commit()
        print("Seeded default movie comments.")

    conn.close()

# =========================================
# INIT DB
# =========================================
storage.create_table()
initialize_and_seed_db()

history = []

@app.context_processor
def inject_banners():
    try:
        banners = get_banner_movies()
    except Exception:
        banners = []
    return dict(banners=banners)

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
    import hashlib
    
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
        
    # Download the image synchronously to ensure the poster is available when the page renders
    if original_url and original_url.startswith("http"):
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            res = requests.get(original_url, headers=headers, timeout=5)
            if res.status_code == 200:
                os.makedirs(poster_dir, exist_ok=True)
                with open(filepath, "wb") as f:
                    f.write(res.content)
                print(f"Downloaded local poster synchronously for: {title}")
            else:
                print(f"Failed to download poster (status {res.status_code}) for: {title}")
        except Exception as ex:
            print(f"Poster download error for {title}: {ex}")
        return local_url
            
    # If download fails or is blocked by school firewall, use a beautiful local placeholder consistently!
    placeholders = [
        "/static/image/cinema_luxury.png",
        "/static/image/cinema_cozy.png",
        "/static/image/cinema_retro.png",
        "/static/image/cinema_audience.png"
    ]
    h = int(hashlib.md5(title.encode('utf-8')).hexdigest(), 16)
    placeholder = placeholders[h % len(placeholders)]
    return placeholder


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
    
    # Ensure classmate_feedback table exists defensively
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS classmate_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    except Exception as e:
        print("Error creating classmate_feedback table on home load:", e)

    # Fetch classmate feedbacks
    feedbacks = []
    try:
        cur.execute("SELECT username, feedback, created_at FROM classmate_feedback ORDER BY created_at DESC LIMIT 10")
        fb_rows = cur.fetchall()
        for r in fb_rows:
            feedbacks.append({
                "username": r[0],
                "feedback": r[1],
                "created_at": r[2]
            })
    except Exception as fb_err:
        print("Error fetching classmate feedback for home:", fb_err)

    # Fetch recent movie comments
    movie_reviews = []
    try:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='movie_comments'")
        if cur.fetchone():
            cur.execute("""
                SELECT mc.username, mc.comment, mc.rating, mc.created_at, c.title AS movie_title
                FROM movie_comments mc
                LEFT JOIN movie_catalog c ON mc.movie_id = c.id
                ORDER BY mc.created_at DESC
                LIMIT 10
            """)
            rows = cur.fetchall()
            for r in rows:
                movie_reviews.append({
                    "username": r[0],
                    "comment": r[1],
                    "rating": r[2],
                    "created_at": r[3],
                    "movie_title": r[4]
                })
    except Exception as e:
        print("Error fetching movie comments on home load:", e)

    cur.execute("SELECT DISTINCT title, year, rating, poster_url, trailer_url, note, country FROM movies")
    rows = cur.fetchall()
    conn.close()

    movies = []
    seen_titles = set()
    for row in rows:
        title = row[0]
        if title and title not in seen_titles:
            seen_titles.add(title)
            enriched = enrich_movie(title)
            
            poster_url = enriched.get("poster")
            if not poster_url and row[3] and row[3].startswith("http"):
                poster_url = download_local_poster(title, row[3])
            poster_url = poster_url or ""
            
            movies.append({
                "title": title,
                "year": enriched.get("year") or row[1] or "",
                "rating": enriched.get("rating") or row[2] or "N/A",
                "poster_url": poster_url,
                "trailer_url": get_clean_embed_trailer(title, enriched.get("trailer") or row[4] or ""),
                "note": enriched.get("note") or row[5] or "",
                "country": enriched.get("country") or row[6] or ""
            })

    banners = get_banner_movies()

    return render_template(
        "index.html",
        movies=movies,
        banners=banners,
        feedbacks=feedbacks,
        movie_reviews=movie_reviews,
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
            "poster_url": local_poster,
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
    cur.execute("SELECT DISTINCT title, year, rating, poster_url, trailer_url, note, country FROM movies")
    rows = cur.fetchall()
    conn.close()

    movies = []
    seen_titles = set()
    for row in rows:
        title = row[0]
        if title and title not in seen_titles:
            seen_titles.add(title)
            enriched = enrich_movie(title)
            
            poster_url = enriched.get("poster")
            if not poster_url and row[3] and row[3].startswith("http"):
                poster_url = download_local_poster(title, row[3])
            poster_url = poster_url or ""
            
            movies.append({
                "title": title,
                "year": enriched.get("year") or row[1] or "N/A",
                "rating": enriched.get("rating") or row[2] or "N/A",
                "poster_url": poster_url,
                "trailer_url": get_clean_embed_trailer(title, enriched.get("trailer") or row[4] or ""),
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
    
    # 1. Download and resolve high-fidelity poster locally
    local_poster = download_local_poster(movie_catalog_data["title"], movie_catalog_data["poster_url"])
    
    # 2. Get list of all available catalog movies for the dynamic dropdown selection
    stored_catalog = storage.list_catalog_movies()
    catalog_list = []
    for item in stored_catalog:
        catalog_list.append({
            "id": item[0],
            "title": item[1]
        })
        
    # 3. Retrieve showtimes from database
    showtimes = get_showtimes(movie_id)
    showtimes_list = []
    for s in showtimes:
        showtimes_list.append({
            "date": s[0],
            "time": s[1],
            "screen": s[2]
        })
        
    # 4. Fallback defensive showtimes if catalog database showtimes are unseeded
    if not showtimes_list:
        showtimes_list = [
            {"date": "Today", "time": "2:30 PM", "screen": "Screen 1 Standard"},
            {"date": "Today", "time": "6:00 PM", "screen": "Screen 2 IMAX"},
            {"date": "Tomorrow", "time": "9:15 PM", "screen": "Screen 3 VIP"}
        ]
        
    movie_data = {
        "id": movie_catalog_data["id"],
        "name": movie_catalog_data["title"],
        "poster_url": local_poster,
        "date": showtimes_list[0]["date"],
        "time": showtimes_list[0]["time"],
        "screen": showtimes_list[0]["screen"]
    }
        
    banners = get_banner_movies()
    return render_template(
        "purchase.html",
        movie=movie_data,
        showtimes=showtimes_list,
        catalog_movies=catalog_list,
        banners=banners,
        country_to_flag=country_to_flag
    )


# =========================================
# LANDING PAGE FOR PRESENTATION PROMOTION
# =========================================
@app.route("/landing")
def landing_page():
    """Render a landing page to promote the presentation.
    The page encourages visitors to review the presentation and share it on
    LinkedIn and Facebook. No database writes are performed – this is a simple
    static page with social‑share links.
    """
    # Presentation details – customize as needed
    presentation_title = "My Presentation"
    presentation_description = (
        "Help me reach 1,000 reviews! Watch the presentation and share your feedback."
    )
    # Assuming a PDF or video is stored in the static folder
    presentation_url = url_for('static', filename='presentation.pdf')
    return render_template(
        "landing.html",
        title=presentation_title,
        description=presentation_description,
        presentation_url=presentation_url,
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
# API SEND DIGITAL TICKET EMAIL RECEIPT
# =========================================
@app.route("/api/send_ticket_email", methods=["POST"])
def send_ticket_email():
    try:
        data = request.get_json() or {}
        target_email = data.get("email")
        ticket_code = data.get("ticket_code")
        movie_title = data.get("movie_title")
        show_date = data.get("date")
        show_time = data.get("time")
        screen = data.get("screen")
        items = data.get("items", [])
        total = data.get("total")

        if not target_email:
            return jsonify({"success": False, "message": "Destination email is missing."})

        # Load SMTP settings from .env file
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port_raw = os.getenv("SMTP_PORT", "587")
        try:
            smtp_port = int(smtp_port_raw)
        except ValueError:
            smtp_port = 587
            
        smtp_email = os.getenv("SMTP_EMAIL")
        smtp_password = os.getenv("SMTP_PASSWORD")

        # Verify SMTP configurations are set
        if not smtp_email or not smtp_password:
            return jsonify({
                "success": False,
                "message": "SMTP credentials are not configured in your .env file."
            })

        # Build items table rows
        receipt_rows = ""
        for item in items:
            name = item.get("name", "Cinema Item")
            quantity = item.get("quantity", 1)
            price = item.get("price", 0.0)
            receipt_rows += f"""
            <tr style="font-size: 13px; color: #d1d5db; border-bottom: 1px solid #1f1f2e;">
              <td style="padding: 8px 0; text-align: left;">{name} x{quantity}</td>
              <td style="padding: 8px 0; text-align: right; font-weight: bold;">${(price * quantity):.2f}</td>
            </tr>
            """

        # Construct beautiful cinematic HTML email layout
        html_content = f"""
        <html>
          <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #09090e; color: #f3f4f6; padding: 40px 20px; margin: 0;">
            <div style="max-width: 480px; margin: 0 auto; background: #14141d; border: 1px solid #232332; border-radius: 24px; overflow: hidden; box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);">
              
              <!-- Brand Header -->
              <div style="background: #1f1f2e; padding: 24px; text-align: center; border-bottom: 2px dashed #232332;">
                <span style="font-size: 12px; font-weight: 800; color: #9ca3af; letter-spacing: 2px; text-transform: uppercase;">🍿 MENTAL MOVIE CINEMAS</span>
              </div>
              
              <!-- Movie Details Card -->
              <div style="padding: 30px 24px 20px 24px;">
                <h2 style="font-size: 24px; font-weight: 900; color: #ffffff; margin: 0 0 24px 0; text-transform: uppercase; letter-spacing: -0.5px; line-height: 1.2;">{movie_title}</h2>
                
                <table style="width: 100%; border-collapse: collapse;">
                  <tr>
                    <td style="padding: 4px 0; font-size: 9px; color: #71717a; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">DATE</td>
                    <td style="padding: 4px 0; font-size: 9px; color: #71717a; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">SHOWTIME</td>
                  </tr>
                  <tr>
                    <td style="font-size: 14px; font-weight: 800; color: #ffffff; padding-bottom: 16px;">{show_date}</td>
                    <td style="font-size: 14px; font-weight: 800; color: #ffffff; padding-bottom: 16px;">{show_time}</td>
                  </tr>
                  <tr>
                    <td style="padding: 4px 0; font-size: 9px; color: #71717a; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">SCREEN</td>
                    <td style="padding: 4px 0; font-size: 9px; color: #71717a; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">SEATS</td>
                  </tr>
                  <tr>
                    <td style="font-size: 14px; font-weight: 800; color: #ffffff;">{screen}</td>
                    <td style="font-size: 14px; font-weight: 800; color: #ffffff;">General Adm</td>
                  </tr>
                </table>
              </div>
              
              <!-- Dashed Dividing Line -->
              <div style="height: 1px; border-top: 2px dashed #232332; margin: 0 24px;"></div>
              
              <!-- Concessions Receipt & QR Code -->
              <div style="padding: 24px; background: #1a1a26;">
                <h3 style="font-size: 11px; color: #71717a; margin: 0 0 16px 0; letter-spacing: 1px; font-weight: 700; text-transform: uppercase;">ORDER RECEIPT</h3>
                
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 16px;">
                  {receipt_rows}
                </table>
                
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 28px;">
                  <tr>
                    <td style="font-size: 14px; font-weight: 800; color: #ffffff; border-top: 1px solid #232332; padding-top: 14px;">TOTAL PAID</td>
                    <td style="font-size: 18px; font-weight: 900; color: #06b6d4; text-align: right; border-top: 1px solid #232332; padding-top: 14px;">{total}</td>
                  </tr>
                </table>
                
                <!-- Dynamic QR Code Center -->
                <div style="text-align: center; margin-top: 10px;">
                  <img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={ticket_code}" alt="Scan QR Code" style="background: #ffffff; padding: 12px; border-radius: 16px; border: 1px solid #232332; box-shadow: 0 10px 20px rgba(0, 0, 0, 0.4);" />
                  <p style="margin: 18px 0 2px 0; font-size: 9px; color: #71717a; font-weight: 700; letter-spacing: 1px;">TICKET CODE</p>
                  <p style="margin: 0; font-size: 18px; font-weight: 900; color: #ffffff; letter-spacing: 0.5px;">{ticket_code}</p>
                </div>
              </div>
              
            </div>
          </body>
        </html>
        """

        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        # Formulate Email Envelope
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🎟️ Your Digital Ticket Receipt: {movie_title} ({ticket_code})"
        msg["From"] = smtp_email
        msg["To"] = target_email

        # Attach text backup and beautiful HTML receipt
        text_backup = f"Cinema Ticket Receipt\nMovie: {movie_title}\nCode: {ticket_code}\nDate: {show_date}\nTime: {show_time}\nScreen: {screen}\nTotal: {total}"
        msg.attach(MIMEText(text_backup, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        # Setup Secure TLS SMTP connection
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_email, smtp_password)
        server.sendmail(smtp_email, target_email, msg.as_string())
        server.quit()

        return jsonify({"success": True, "message": "Email sent successfully!"})
    except Exception as e:
        print("API EMAIL DISPATCH ERROR:", e)
        return jsonify({"success": False, "message": f"SMTP Dispatch Error: {str(e)}"})


# =========================================
# API VERIFY BOOKING
# =========================================
@app.route("/api/verify_booking", methods=["POST"])
def verify_booking():
    try:
        data = request.get_json() or {}
        ticket_code = data.get("ticket_code")
        if not ticket_code:
            return jsonify({"success": False, "message": "Ticket code is required."})

        from movie_storage_sql import get_qr_purchase_details
        details = get_qr_purchase_details(ticket_code)
        if not details:
            return jsonify({"success": False, "message": "No booking found matching code."})

        return jsonify({"success": True, "details": details})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


# =========================================
# API CANCEL BOOKING & REFUND
# =========================================
@app.route("/api/cancel_booking", methods=["POST"])
def cancel_booking():
    try:
        data = request.get_json() or {}
        ticket_code = data.get("ticket_code")
        target_email = data.get("email")

        if not ticket_code:
            return jsonify({"success": False, "message": "Ticket code is required."})

        from movie_storage_sql import cancel_qr_purchase, get_qr_purchase_details
        
        details = get_qr_purchase_details(ticket_code)
        if not details:
            return jsonify({"success": False, "message": f"No booking found matching code {ticket_code}."})

        if details.get("status") == "cancelled":
            return jsonify({"success": False, "message": "This booking is already cancelled."})

        # Process cancellation in SQLite
        cancel_qr_purchase(ticket_code)

        # Trigger confirmation email if target email is provided
        if target_email:
            # Load SMTP settings
            smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
            smtp_port_raw = os.getenv("SMTP_PORT", "587")
            try:
                smtp_port = int(smtp_port_raw)
            except ValueError:
                smtp_port = 587
                
            smtp_email = os.getenv("SMTP_EMAIL")
            smtp_password = os.getenv("SMTP_PASSWORD")

            if smtp_email and smtp_password:
                # Construct email body
                html_content = f"""
                <html>
                  <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #09090e; color: #f3f4f6; padding: 40px 20px; margin: 0;">
                    <div style="max-width: 480px; margin: 0 auto; background: #14141d; border: 1px solid #232332; border-radius: 24px; overflow: hidden; box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);">
                      
                      <!-- Brand Header -->
                      <div style="background: #ef4444; padding: 24px; text-align: center; border-bottom: 2px dashed #232332;">
                        <span style="font-size: 12px; font-weight: 800; color: #ffffff; letter-spacing: 2px; text-transform: uppercase;">🍿 TICKET CANCELLED</span>
                      </div>
                      
                      <!-- Movie Details Card -->
                      <div style="padding: 30px 24px 20px 24px;">
                        <h2 style="font-size: 20px; font-weight: 900; color: #ffffff; margin: 0 0 16px 0; text-transform: uppercase; letter-spacing: -0.5px; line-height: 1.2;">CANCELLATION CONFIRMED</h2>
                        <p style="font-size: 13.5px; color: #9ca3af; line-height: 1.6; margin-bottom: 20px;">
                          Your booking for <strong>{details.get("movie_title", "Movie")}</strong> under ticket code <strong>{ticket_code}</strong> has been successfully cancelled.
                        </p>
                        <p style="font-size: 13.5px; color: #9ca3af; line-height: 1.6; margin-bottom: 20px;">
                          A full refund has been initiated to your original payment method. Please allow 3-5 business days for it to reflect in your account.
                        </p>
                      </div>
                      
                      <div style="background: #1a1a26; padding: 20px 24px; text-align: center;">
                        <span style="font-size: 11px; color: #71717a; text-transform: uppercase; letter-spacing: 1px;">Thank you for using Stoplight Cinema</span>
                      </div>
                      
                    </div>
                  </body>
                </html>
                """

                import smtplib
                from email.mime.multipart import MIMEMultipart
                from email.mime.text import MIMEText

                msg = MIMEMultipart("alternative")
                msg["Subject"] = f"❌ Booking Cancelled & Refund Processed: {details.get('movie_title')} ({ticket_code})"
                msg["From"] = smtp_email
                msg["To"] = target_email

                text_backup = f"Your booking for {details.get('movie_title')} under code {ticket_code} has been cancelled. A refund is being processed."
                msg.attach(MIMEText(text_backup, "plain"))
                msg.attach(MIMEText(html_content, "html"))

                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
                server.login(smtp_email, smtp_password)
                server.sendmail(smtp_email, target_email, msg.as_string())
                server.quit()
                print(f"Cancellation email sent successfully to {target_email} for code {ticket_code}")

        return jsonify({"success": True, "message": "Booking successfully cancelled and refund initiated!"})
    except Exception as e:
        print("API CANCELLATION ERROR:", e)
        return jsonify({"success": False, "message": f"Cancellation error: {str(e)}"})


# =========================================
# REFRESH BANNERS ROUTE
# =========================================
# =========================================
@app.route("/refresh_banners")
def refresh_banners_route():
    try:
        fetch_banner_movies()
    except Exception as e:
        print("Refresh banners error:", e)
    return redirect("/")


# Helper function to gather database context for the chatbot
def get_chatbot_movie_context():
    import sqlite3
    try:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "movies.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # 1. Fetch catalog movies
        cur.execute("SELECT id, title, genre, description, poster_url, trailer_url FROM movie_catalog")
        catalog_rows = cur.fetchall()
        
        # 2. Fetch user saved movies
        cur.execute("SELECT DISTINCT title, year, rating, poster_url, trailer_url, note FROM movies")
        user_rows = cur.fetchall()
        
        # 3. Fetch homepage banner/slider movies
        cur.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='banner_movies'")
        if cur.fetchone()[0] == 1:
            cur.execute("SELECT DISTINCT title, category, release_date, rating, overview, poster_url, banner_url FROM banner_movies")
            banner_rows = cur.fetchall()
        else:
            banner_rows = []
        conn.close()
        
        catalog_title_map = {row['title'].lower().strip(): row['id'] for row in catalog_rows}
        
        context = "Available movies in the Cinema Catalog (purchase tickets and watch trailers inline):\n"
        for row in catalog_rows:
            p_url = row['poster_url'] or "/static/image/cinema_luxury.png"
            if p_url.startswith("http"):
                p_url = download_local_poster(row['title'], p_url)
            t_url = get_clean_embed_trailer(row['title'], row['trailer_url'] or "")
            
            # Extract video ID to build standard watch URL
            watch_url = t_url
            if "/embed/" in t_url:
                yt_id = t_url.split("/embed/")[-1].split("?")[0]
                watch_url = f"https://www.youtube.com/watch?v={yt_id}"
                
            context += f"- Title: {row['title']} | ID: {row['id']} | Genre: {row['genre']} | Details & Comments Link: /movie/{row['id']} | Purchase Link: /purchase/{row['id']} | Poster URL: {p_url} | Trailer Embed URL: {t_url} | Trailer Watch URL: {watch_url}\n"
            
        context += "\nUser's Personal Saved Movies Collection:\n"
        for row in user_rows:
            p_url = row['poster_url'] or "/static/image/cinema_luxury.png"
            if p_url.startswith("http"):
                p_url = download_local_poster(row['title'], p_url)
            t_url = get_clean_embed_trailer(row['title'], row['trailer_url'] or "")
            
            # Extract video ID to build standard watch URL
            watch_url = t_url
            if "/embed/" in t_url:
                yt_id = t_url.split("/embed/")[-1].split("?")[0]
                watch_url = f"https://www.youtube.com/watch?v={yt_id}"
                
            context += f"- Title: {row['title']} | Year: {row['year']} | Rating: {row['rating']} | User Note: {row['note']} | Poster URL: {p_url} | Trailer Embed URL: {t_url} | Trailer Watch URL: {watch_url}\n"
            
        context += "\nMovies Currently Featured in the Homepage Slider Banner (Carousel):\n"
        for row in banner_rows:
            p_url = row['poster_url'] or "/static/image/cinema_luxury.png"
            title_lower = row['title'].lower().strip()
            cat_id = catalog_title_map.get(title_lower, None)
            
            friendly_category = row['category'].replace('_', ' ').title()
            details_link = f"/movie/{cat_id}" if cat_id else "/catalog"
            purchase_link = f"/purchase/{cat_id}" if cat_id else "/catalog"
            
            context += f"- Title: {row['title']} | Slider Category: {friendly_category} | Release Date: {row['release_date']} | Rating: {row['rating']} | Overview: {row['overview']} | Poster URL: {p_url} | Details Link: {details_link} | Purchase Link: {purchase_link}\n"
            
        return context

    except Exception as e:
        print("Error building chat context:", e)
        return "Movie database is currently empty."


TRAILER_CACHE = {}

def get_clean_embed_trailer(title, default_url):
    """
    Returns the trailer URL as‑is (no YouTube embed conversion).
    If no URL is supplied, returns an empty string.
    """
    global TRAILER_CACHE
    cache_key = (title, default_url)
    if cache_key in TRAILER_CACHE:
        return TRAILER_CACHE[cache_key]

    if not default_url or not default_url.strip():
        return ""

    # Strip whitespace and return the URL unchanged
    url = default_url.strip()
    TRAILER_CACHE[cache_key] = url
    return url


def post_process_chat_reply(reply, user_message):
    """
    Applies programmatic filters and fail-safe replacements to the chatbot's response.
    Specifically:
      1. Cleans up raw YouTube hyperlinks, Markdown links, and HTML anchors to standardise video embeds.
      2. Replaces placeholders (like '<trailer_embed_url>', '<poster_url>', '<movie_id>') with actual database values.
      3. Automatically injects the inline iframe player if the user asked for a trailer but the LLM did not output it.
      4. Automatically redirects to the local movie detail page (/movie/id) if no trailer URL is defined in the database.
    """
    import sqlite3
    import re
    
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "movies.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Fetch all movies from catalog
    cur.execute("SELECT id, title, poster_url, trailer_url FROM movie_catalog")
    catalog_movies = cur.fetchall()
    
    # Fetch all movies from personal
    cur.execute("SELECT DISTINCT title, poster_url, trailer_url FROM movies")
    personal_movies = cur.fetchall()
    
    # Fetch all movies from banner_movies if the table exists
    cur.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='banner_movies'")
    if cur.fetchone()[0] == 1:
        cur.execute("SELECT DISTINCT title, poster_url FROM banner_movies")
        banner_db_movies = cur.fetchall()
    else:
        banner_db_movies = []
        
    conn.close()
    
    # Build dictionaries
    movie_data = {}
    for row in catalog_movies:
        title = row[1]
        p_url = row[2] or "/static/image/cinema_luxury.png"
        if p_url.startswith("http"):
            p_url = download_local_poster(title, p_url)
        t_url = row[3] or ""
        movie_data[title.lower()] = {
            "title": title,
            "id": row[0],
            "poster_url": p_url,
            "trailer_url": get_clean_embed_trailer(title, t_url)
        }
        
    for row in personal_movies:
        title = row[0]
        p_url = row[1] or "/static/image/cinema_luxury.png"
        if p_url.startswith("http"):
            p_url = download_local_poster(title, p_url)
        t_url = row[2] or ""
        # If not in catalog, add to dict
        if title.lower() not in movie_data:
            movie_data[title.lower()] = {
                "title": title,
                "id": None,
                "poster_url": p_url,
                "trailer_url": get_clean_embed_trailer(title, t_url)
            }

    for row in banner_db_movies:
        title = row[0]
        p_url = row[1] or "/static/image/cinema_luxury.png"
        if p_url.startswith("http"):
            p_url = download_local_poster(title, p_url)
        # If not in catalog or personal, add to dict
        if title.lower() not in movie_data:
            movie_data[title.lower()] = {
                "title": title,
                "id": None,
                "poster_url": p_url,
                "trailer_url": ""
            }

            
    # 1. Clean up any remaining raw/markdown/html YouTube links first
    # This keeps our injected UI safe from the filter.
    def clean_youtube_links(text):
        def extract_id(url):
            match = re.search(r'(?:v=|embed/|v/|shorts/|youtu\.be/|/)([a-zA-Z0-9_-]{11})', url)
            if match:
                return match.group(1)
            return None

        # Replace markdown links to youtube
        markdown_pattern = r'\[[^\]]*\]\((https?://[^\s)]*youtube[^\s)]*|https?://[^\s)]*youtu\.be[^\s)]*)\)'
        # Replace html anchor tags linking to youtube
        html_pattern = r'<a\s+[^>]*href=["\'](https?://[^"\']*youtube[^"\']*|https?://[^"\']*youtu\.be[^"\']*)["\'][^>]*>.*?</a>'

        def replacer(match):
            url = match.group(1)
            return f"<a href='{url}' target='_blank' style='display:inline-block; margin-top:8px; padding:6px 12px; background:#ff3d3d; color:#fff; border-radius:6px; text-decoration:none;'>Watch Trailer</a>"

        text = re.sub(markdown_pattern, replacer, text)
        text = re.sub(html_pattern, replacer, text)

        # Replace standalone youtube URLs not inside src/href attributes
        plain_pattern = r'(?<!src=["\'])(?<!href=["\'])\b(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)[a-zA-Z0-9_-]{11}[^\s<]*)\b'
        
        def plain_replacer(match):
            url = match.group(1)
            return f"<a href='{url}' target='_blank' style='display:inline-block; margin-top:8px; padding:6px 12px; background:#ff3d3d; color:#fff; border-radius:6px; text-decoration:none;'>Watch Trailer</a>"
            
        text = re.sub(plain_pattern, plain_replacer, text)
        return text

    reply = clean_youtube_links(reply)

    # 2. Post-process placeholders
    matched_movie = None
    user_msg_lower = user_message.lower()
    reply_lower = reply.lower()
    
    # Find matching title
    sorted_titles = sorted(movie_data.keys(), key=len, reverse=True)
    for title_key in sorted_titles:
        if title_key in user_msg_lower or title_key in reply_lower:
            matched_movie = movie_data[title_key]
            break
            
    if matched_movie:
        p_url = matched_movie["poster_url"]
        t_url = matched_movie["trailer_url"]
        
        # Replace literal poster placeholders
        placeholders = [
            "[Poster URL from the context]",
            "<poster_url>",
            "poster_url",
            "[poster_url]",
            "<poster_path>",
            "[poster_path]",
            "poster_path"
        ]
        for ph in placeholders:
            reply = reply.replace(ph, p_url)
            
        # Replace trailer embed placeholders
        trailer_placeholders = [
            "<trailer_embed_url>",
            "[Trailer Embed URL]",
            "trailer_embed_url",
            "<trailer_url>",
            "[trailer_url]",
            "trailer_url"
        ]
        for ph in trailer_placeholders:
            reply = reply.replace(ph, t_url)
            
        # Replace movie id placeholders
        id_placeholders = [
            "<movie_id>",
            "[Movie ID]",
            "movie_id"
        ]
        if matched_movie["id"] is not None:
            for ph in id_placeholders:
                reply = reply.replace(ph, str(matched_movie["id"]))
            
    # 3. Programmatic injection if user asked for a poster and it's missing in reply
    asked_for_poster = any(k in user_msg_lower for k in ["poster", "cover", "image", "picture", "photo", "cover art"])
    has_img_tag = "<img" in reply
    
    if asked_for_poster and not has_img_tag and matched_movie:
        p_url = matched_movie["poster_url"]
        img_html = f'<br><img src="{p_url}" alt="{matched_movie["title"]}" class="chat-movie-poster" style="width:120px; border-radius:10px; margin: 12px auto; display:block; box-shadow: 0 4px 10px rgba(0,0,0,0.3); transition: 0.2s;">'
        reply += img_html
        
    # 4. Programmatic injection if user asked for a trailer/video and it's missing in reply
    asked_for_trailer = any(k in user_msg_lower for k in ["trailer", "video", "play", "watch", "stream"])
    has_trailer_tag = "Watch Trailer" in reply
    
    if asked_for_trailer and not has_trailer_tag and matched_movie:
        t_url = matched_movie["trailer_url"]
        if t_url:
            trailer_html = f'<br><a href="{t_url}" target="_blank" style="display:inline-block; margin-top:8px; padding:6px 12px; background:#ff3d3d; color:#fff; border-radius:6px; text-decoration:none;">Watch Trailer</a>'
            reply += trailer_html
        elif matched_movie["id"]:
            m_id = matched_movie["id"]
            fallback_html = f'<br><a href="/movie/{m_id}" class="chat-action-btn" style="display:inline-block; background:#ff3c3c; color:#fff; padding:8px 16px; border-radius:8px; font-weight:bold; text-decoration:none; margin-top:8px; font-size:12px; box-shadow: 0 4px 12px rgba(255, 60, 60, 0.25);">🔍 View Details & Showtimes</a>'
            reply += fallback_html
        
    return reply


def detect_language(text):
    """
    Detects language of input text (supporting English, German, French, Spanish).
    Prioritizes explicit language switching cues, then uses langdetect, and falls back to stopwords.
    """
    default_lang = "en"
    if not text or not text.strip():
        return default_lang

    text_clean = text.strip()
    text_lower = text_clean.lower()

    # 1. Explicit language request cues override (e.g. "explain in German", "in Spanish", etc.)
    lang_cues = {
        "de": ["german", "deutsch", "allemand", "auf deutsch", "in deutsch", "sprich deutsch", "schreib auf deutsch", "antworten auf deutsch", "erkläre auf deutsch", "erkläre in deutsch"],
        "es": ["spanish", "español", "espanol", "castellano", "en español", "habla español", "escribe en español", "responder en español", "explica en español"],
        "fr": ["french", "français", "francais", "en français", "parle français", "écris en français", "répondre en français", "explique en français"],
        "it": ["italian", "italiano", "en italiano", "in italian", "parla italiano", "scrivi in italiano", "rispondi in italiano", "spiega in italiano"],
        "pt": ["portuguese", "português", "portugues", "em português", "fala português", "escreve em português", "responde em português", "explica em português"],
        "nl": ["dutch", "nederlands", "in het nederlands", "spreek nederlands", "schrijf in het nederlands", "reageer in het nederlands", "leg uit in het nederlands"],
        "ru": ["russian", "русский", "на русском", "говори по-русски", "пиши по-русски", "отвечай по-русски", "объясни на русском"],
        "zh": ["chinese", "中文", "用中文", "说中文", "写中文", "回答中文", "用中文解释"],
        "ja": ["japanese", "日本語", "で日本語", "日本語で話す", "日本語で書く", "日本語で答える", "日本語で説明する"],
        "en": ["english", "inglés", "anglais", "in english", "speak english", "write in english", "respond in english", "explain in english"]
    }

    for lang_code, keywords in lang_cues.items():
        if any(f"in {kw}" in text_lower or f"en {kw}" in text_lower or f"auf {kw}" in text_lower or f"em {kw}" in text_lower or f"explain in {kw}" in text_lower or f"explicar en {kw}" in text_lower or f"expliquer en {kw}" in text_lower or f"на {kw}" in text_lower or f"用 {kw}" in text_lower or f"de{kw}" in text_lower or f"using {kw}" in text_lower or f"use {kw}" in text_lower for kw in keywords):
            return lang_code
        if any(f"speak {kw}" in text_lower or f"write in {kw}" in text_lower or f"respond in {kw}" in text_lower or f"say in {kw}" in text_lower or f"talk in {kw}" in text_lower for kw in keywords):
            return lang_code
        # Local direct triggers like "parle français"
        if lang_code in ["de", "es", "fr", "it", "pt", "ru", "zh", "ja"]:
            matching_kws = [kw for kw in keywords if len(kw) > 5 and kw in text_lower]
            if matching_kws:
                # Only trigger if user explicitly says a long keyword like "italiano" or "português" in context
                if any(any(phrase in text_lower for phrase in [f"speak {k}", f"write {k}", f"respond {k}", f"explain {k}", f"in {k}", f"en {k}", f"auf {k}", f"em {k}"]) for k in matching_kws):
                    return lang_code

    # 2. Attempt langdetect detection (supporting any 2-character ISO language code)
    try:
        from langdetect import detect
        detected = detect(text_clean)
        if detected and len(detected) == 2:
            return detected
    except Exception as e:
        print("[Language Detection] langdetect error/missing:", e)

    # 3. Heuristics fallback (stopword count)
    import re
    words = set(re.findall(r'\b\w+\b', text_lower))

    lang_keywords = {
        "de": {"ich", "ist", "und", "der", "die", "das", "ein", "eine", "nicht", "mit", "auf", "für", "von", "zu", "wir", "ihr", "sie", "es", "sind", "war", "kann", "wie", "was", "wo", "hallo", "film", "filme", "kino", "karten", "trailer", "bitte", "danke"},
        "fr": {"le", "la", "les", "et", "un", "une", "est", "dans", "pour", "en", "qui", "que", "nous", "vous", "ils", "elles", "film", "films", "cinéma", "billet", "billets", "bande-annonce", "bonjour", "merci", "salut"},
        "es": {"el", "la", "los", "las", "y", "un", "una", "es", "en", "para", "con", "que", "nosotros", "vosotros", "ellos", "ellas", "película", "películas", "cine", "entrada", "entradas", "tráiler", "hola", "gracias"},
        "en": {"the", "and", "a", "an", "is", "in", "to", "for", "with", "on", "of", "it", "we", "you", "they", "he", "she", "movie", "movies", "cinema", "ticket", "tickets", "trailer", "hello", "thanks", "please"}
    }

    scores = {"en": 0, "de": 0, "fr": 0, "es": 0}
    for word in words:
        for lang, keywords in lang_keywords.items():
            if word in keywords:
                scores[lang] += 1

    max_lang = max(scores, key=scores.get)
    if scores[max_lang] > 0:
        return max_lang

    return default_lang


# =========================================
# CHAT
# =========================================
@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json() or {}
    user_message = data.get("message", "")
    client_history = data.get("history", [])
    selected_model = data.get("model", "gpt-4.1-mini")

    # Fallback/validation: if it's not a known or supported model, default to gpt-4o-mini
    if selected_model not in ["gpt-4o-mini", "gpt-4.1-mini", "gpt-5-mini"]:
        selected_model = "gpt-4o-mini"

    # Default detected language in case language detection fails before target_lang is defined
    detected_lang = "en"

    try:
        # Get rich movie metadata from database
        movie_context = get_chatbot_movie_context()

        # Automatically detect the user's message language on the backend
        detected_lang = detect_language(user_message)
        lang_names = {
            "en": "English",
            "de": "German",
            "fr": "French",
            "es": "Spanish",
            "it": "Italian",
            "pt": "Portuguese",
            "nl": "Dutch",
            "ru": "Russian",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
            "ar": "Arabic",
            "tr": "Turkish",
            "pl": "Polish"
        }
        target_lang = lang_names.get(detected_lang, detected_lang.upper())

        system_prompt = f"""You are CinemaBot 🎬. You MUST respond in {target_lang} because the user's message is written/spoken in {target_lang}.

LANGUAGE FLEXIBILITY RULE:
If the user explicitly requests you to switch languages or speak/write in a specific language (for example: "Explain this in German", "respond in Spanish", "write in French", "write in English"), you MUST prioritize that instruction and reply in the requested language, regardless of the default/detected language of the prompt. Always ensure correct grammar, spelling, and vocabulary for the language you are responding in.

CONVERSATIONAL ENGAGEMENT & DIALOGUE CONTINUATION RULE:
You MUST NEVER end a turn with a passive statement, just a raw HTML link/image, or empty dialogue. After you have answered the user's request, displayed a poster, embedded a trailer, or handled a booking, you must ALWAYS actively engage the user by asking a helpful follow-up question in the same language to keep the conversation flowing. For example:
- English: "Would you like me to show you the trailer for this movie?" or "Should we proceed to book tickets for this film?" or "Is there anything else I can assist you with?"
- German: "Möchten Sie, dass ich Ihnen den Trailer zu diesem Film zeige?" or "Sollen wir mit der Ticketbuchung für diesen Film fortfahren?" or "Kann ich Ihnen sonst noch bei etwas behilflich sein?"
- Spanish: "¿Le gustaría que le muestre el tráiler de esta película?" or "¿Procedemos a reservar las entradas?" or "¿Hay algo más en lo que pueda ayudarle hoy?"
- French: "Souhaitez-vous que je vous montre la bande-annonce de ce film ?" or "Voulez-vous procéder à la réservation des billets ?" or "Puis-je vous aider avec autre chose aujourd'hui ?"
Keep the conversation active, polite, friendly, and helpful. Do not leave the user hanging.

GERMAN LANGUAGE DIRECTIVE (FORMAL ADDRESS / HÖFLICHKEITSFORM):
When responding in German, you must ALWAYS use the formal address "Sie" (capitalized), along with its related formal pronouns ("Ihr", "Ihre", "Ihnen", etc.). NEVER use the informal "du", "dein", or "ihr". Keep your tone polite, respectful, professional, and formal.

LIST READING & SPEECH SYNTHESIS (TTS) RULE:
Please read the list items by saying the number followed directly by the text, without adding words like "point" (e.g., do not say "one point" when reading a list item like "1. [item]"). Format and phrase your list responses so that text-to-speech engines do not pronounce punctuation as the word "point".

You have access to the movie catalog and the user's personal collection. Use this context to answer questions accurately!
{movie_context}

CRITICAL FORMATTING INSTRUCTIONS FOR POSTERS & TRAILERS:
1. Always display the movie poster image directly inside the chatbot window using a raw HTML <img> tag when discussing a movie. Format it exactly like this, substituting the actual values from the movie context:
   <img src="[Poster URL from the context]" alt="[Movie Title]" class="chat-movie-poster" style="width:120px; border-radius:10px; margin: 12px auto; display:block; box-shadow: 0 4px 10px rgba(0,0,0,0.3); transition: 0.2s;">
   
   CRITICAL VALUE REPLACEMENT RULES:
   - Replace "[Poster URL from the context]" with the actual HTTP URL listed after "Poster URL:" in the movie context (for example: "https://image.tmdb.org/t/p/w500/9g5tBjU1n4C9FY56V48gH7u7MOd.jpg").
   - NEVER output the literal text "[Poster URL from the context]" or the string "<poster_url>" or the word "poster_url" inside the src attribute. Doing so is a fatal bug that displays a broken image.
   - Do NOT wrap this <img> tag in any <a> (anchor) tag that redirects to the purchase page or the image file. This prevents the user from being redirected away from their active chatbot conversation.
2. If the user asks to see a trailer, watch a video, or play a trailer, EMBED the YouTube video directly inside the chat so they can watch it inline! Use raw HTML iframe tags:
   <div style='margin-top:8px; border-radius:10px; overflow:hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.4);'><iframe width='100%' height='200' src='<trailer_embed_url>' frameborder='0' allow='accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture' allowfullscreen></iframe></div>
   If no trailer URL is available in the context (it is empty), you MUST instead show a button link pointing to the movie details page in our local database:
   <a href='/movie/<movie_id>' class='chat-action-btn' style='display:inline-block; background:#ff3c3c; color:#fff; padding:8px 16px; border-radius:8px; font-weight:bold; text-decoration:none; margin-top:8px; font-size:12px; box-shadow: 0 4px 12px rgba(255, 60, 60, 0.25);'>🔍 View Details & Showtimes</a>
3. Always make action links and buttons beautifully styled HTML tags rather than plain text or markdown links. For example, to buy tickets or view details:
     <a href='/movie/<movie_id>' class='chat-action-btn' style='display:inline-block; background:#ff3c3c; color:#fff; padding:8px 16px; border-radius:8px; font-weight:bold; text-decoration:none; margin-top:8px; font-size:12px; box-shadow: 0 4px 12px rgba(255, 60, 60, 0.25);'>🔍 View Details & Reviews</a> <a href='/purchase/<movie_id>' class='chat-action-btn' style='display:inline-block; background:#06b6d4; color:#000; padding:8px 16px; border-radius:8px; font-weight:bold; text-decoration:none; margin-top:8px; font-size:12px; margin-left:6px; box-shadow: 0 4px 12px rgba(6, 182, 212, 0.25);'>🍿 Purchase Tickets</a>
4. If a movie doesn't have a poster in the database, use '/static/image/cinema_luxury.png' as a high-fidelity fallback.

INTEGRATION & NAVIGATION INSTRUCTIONS:
You are fully connected to and integrated with the Stoplight Cinema Portal web application. When users ask about the dashboard, cinema portal, analytics, or cinema map, guide them using these exact instructions, links, or custom action buttons:
1. Cinema Portal: Provide a link to `/catalog` or styled button:
   <a href='/catalog' class='chat-action-btn' style='display:inline-block; background:#ff3c3c; color:#fff; padding:8px 16px; border-radius:8px; font-weight:bold; text-decoration:none; margin-top:8px; font-size:12px; box-shadow: 0 4px 12px rgba(255, 60, 60, 0.25);'>🍿 Go to Cinema Portal</a>
2. Dashboard (Admin Control Console): Provide a link to `/dashboard` or styled button:
   <a href='/dashboard' class='chat-action-btn' style='display:inline-block; background:#4f46e5; color:#fff; padding:8px 16px; border-radius:8px; font-weight:bold; text-decoration:none; margin-top:8px; font-size:12px; box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25);'>📊 Open Administrator Dashboard</a>
   Explain that if the dashboard is locked, they can log in using the "Login" button in the top navbar with their administrator credentials. Do NOT print or disclose default administrator usernames or passwords (such as "Admin" or "Admin.123") in the chat response under any circumstance.
3. Analytics Dashboard: Provide a link to `/analytics` or styled button:
   <a href='/analytics' class='chat-action-btn' style='display:inline-block; background:#06b6d4; color:#000; padding:8px 16px; border-radius:8px; font-weight:bold; text-decoration:none; margin-top:8px; font-size:12px; box-shadow: 0 4px 12px rgba(6, 182, 212, 0.25);'>📈 View Real-Time Analytics</a>
   Explain that they must be logged in as an administrator first.
4. Cinema Map: Offer a custom action button to open the map overlay modal directly:
   <button onclick="openCinemaMapModal()" class="chat-action-btn" style="display:inline-block; background:#10b981; color:#fff; padding:8px 16px; border-radius:8px; font-weight:bold; border:none; cursor:pointer; margin-top:8px; font-size:12px; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25);">📍 Open Cinema Map</button>
   Or instruct them to click "📍 Cinema Map" in the top navigation bar.
5. Cinema Websites & Showtimes: If the user asks about local cinema websites, booking pages, showtimes, or cinema halls, you must check if they have provided both the **City** and **Country** in their message/context.
    - If they did NOT provide both, politely ask them to specify both (e.g., "To help you find the correct cinema website and showtimes, could you please specify both the city and country?").
    - If they specify both the City and Country (matching Enugu, Berlin, Bochum, or Herne in Nigeria/Germany), output the matching embedded website panel AND also provide a direct, styled clickable anchor button pointing to the official external URL to view external showtimes and exterior views:
      <a href="[Official External Website URL]" target="_blank" class="chat-action-btn" style="display:inline-block; background:#06b6d4; color:#000; padding:8px 16px; border-radius:8px; font-weight:bold; text-decoration:none; margin-top:8px; font-size:12px; box-shadow: 0 4px 12px rgba(6, 182, 212, 0.25);">🌐 Visit Official Website & Exterior</a>

The cities, countries, and cinema mappings are:
- Enugu, Nigeria:
  - Genesis Cinema Enugu: Slug `genesis-enugu`, External URL `https://genesiscinemas.com`
  - WNN Cinema Enugu: Slug `wnn-enugu`, External URL `https://www.google.com/search?q=WNN+Cinema+Enugu+showtimes`
- Berlin, Germany:
  - Zoo Palast Berlin: Slug `zoo-palast-berlin`, External URL `https://www.zoopalast.de`
  - Cubix Alexanderplatz: Slug `cubix-berlin`, External URL `https://www.yorck.de`
- Bochum, Germany:
  - Union Filmtheater Bochum: Slug `union-bochum`, External URL `https://www.union-kino.de`
  - Metropolis Kino Bochum: Slug `metropolis-bochum`, External URL `https://www.metropolis-bochum.de`
- Herne, Germany:
  - Filmwelt Herne: Slug `filmwelt-herne`, External URL `https://www.filmwelt-herne.de`
  - UCI Kinowelt Ruhr Park: Slug `uci-herne`, External URL `https://www.uci-kinowelt.de`

Always output the HTML structure for each matching cinema website, substituting the matching values:
    <div class="chat-cinema-web-wrapper" style="margin-top:12px; border-radius:12px; overflow:hidden; border:1.5px solid var(--accent); box-shadow: 0 8px 20px rgba(0,0,0,0.5); width:100%;">
      <div style="background:rgba(15,23,42,0.9); padding:8px 12px; border-bottom:1px solid rgba(255,255,255,0.08); font-size:12px; display:flex; justify-content:space-between; align-items:center;">
        <span style="color:white; font-weight:700;">🌐 [Cinema Name] Website</span>
        <a href="/cinema_website/[city]/[cinema-slug]" target="_blank" style="color:var(--accent); font-weight:600; text-decoration:none;">Open Embedded External ↗</a>
      </div>
      <iframe src="/cinema_website/[city]/[cinema-slug]" style="width:100%; height:320px; border:none; display:block; background:#0c0f17;" title="[Cinema Name] Portal"></iframe>
    </div>

Always explain in a friendly manner in their query language that they can browse showtimes and view exterior designs directly inside the embedded panel or by clicking the Visit Official Website button.
"""

        messages = [
            {"role": "system", "content": system_prompt}
        ] + client_history + [
            {"role": "user", "content": user_message}
        ]

        response = client.chat.completions.create(
            model=selected_model,
            messages=messages,
            temperature=0.8
        )

        reply = response.choices[0].message.content

        # Apply programmatic fail-safe post-processing filter
        reply = post_process_chat_reply(reply, user_message)

        # Detect the language of the reply to synchronize the frontend dropdown
        final_lang = detect_language(reply)

        return jsonify({
            "reply": reply.replace("\n", "<br>"),
            "language": final_lang
        })

    except Exception as e:
        print("CHAT ERROR:", e)
        fallback_messages = {
            "en": "I didn't quite understand your request, could you please rephrase it?",
            "es": "No he entendido bien su solicitud, ¿podría reformular la pregunta, por favor?",
            "de": "Ich habe Ihre Anfrage nicht ganz verstanden, könnten Sie die Frage bitte anders formulieren?",
            "fr": "Je n'ai pas bien compris votre demande, pourriez-vous reformuler la question, s'il vous plaît ?"
        }
        reply = fallback_messages.get(detected_lang, fallback_messages["en"])
        return jsonify({
            "reply": reply,
            "language": detected_lang
        })


# =========================================
# ADMIN LOGIN API
# =========================================
@app.route("/api/login", methods=["POST"])
def api_login():
    try:
        from werkzeug.security import check_password_hash, generate_password_hash
        import sqlite3
        
        data = request.get_json() or {}
        user = data.get("username", "").strip()
        password = data.get("password", "")
        
        if not user or not password:
            return jsonify({"success": False, "message": "Username and password are required"})
            
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "movies.db")
        
        # Check database for admin credentials
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT password_hash FROM admin_credentials WHERE username = ?", (user,))
        row = cur.fetchone()
        conn.close()
        
        if row:
            if check_password_hash(row[0], password):
                return jsonify({"success": True})
            else:
                return jsonify({"success": False, "message": "Invalid username or password"})
            
        # Fallback to check default environment variables (only if user does not exist in DB yet)
        admin_user = os.getenv("ADMIN_USERNAME") or os.getenv("admin_user") or "Admin"
        admin_pass = os.getenv("ADMIN_PASSWORD") or os.getenv("admin_password") or "Admin.123"
        
        if user == admin_user and password == admin_pass:
            # Cache hashed credentials in database
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            hashed = generate_password_hash(admin_pass)
            cur.execute("""
                INSERT OR REPLACE INTO admin_credentials (username, password_hash)
                VALUES (?, ?)
            """, (admin_user, hashed))
            conn.commit()
            conn.close()
            return jsonify({"success": True})
            
        return jsonify({"success": False, "message": "Invalid username or password"})
    except Exception as e:
        print("LOGIN ERROR:", e)
        return jsonify({"success": False, "message": f"Login Error: {str(e)}"})


# =========================================
# FORGOT PASSWORD API
# =========================================
@app.route("/api/forgot_password", methods=["POST"])
def api_forgot_password():
    try:
        from werkzeug.security import generate_password_hash
        import sqlite3
        import random
        import datetime
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        
        data = request.get_json() or {}
        username = data.get("username", "").strip()
        if not username:
            return jsonify({"success": False, "message": "Username is required."})

        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "movies.db")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT username FROM admin_credentials WHERE username = ?", (username,))
        row = cur.fetchone()
        
        # Fallback check
        default_user = os.getenv("ADMIN_USERNAME") or os.getenv("admin_user") or "Admin"
        if not row and username.lower() == default_user.lower():
            admin_pass = os.getenv("ADMIN_PASSWORD") or os.getenv("admin_password") or "Admin.123"
            hashed = generate_password_hash(admin_pass)
            cur.execute("INSERT OR REPLACE INTO admin_credentials (username, password_hash) VALUES (?, ?)", (default_user, hashed))
            conn.commit()
            row = (default_user,)

        if not row:
            conn.close()
            return jsonify({"success": False, "message": "Admin username not found."})

        actual_username = row[0]
        
        # Generate 6-digit OTP
        reset_code = f"{random.randint(100000, 999999)}"
        expiry = (datetime.datetime.now() + datetime.timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
        
        cur.execute("""
            UPDATE admin_credentials
            SET reset_code = ?, reset_expiry = ?
            WHERE username = ?
        """, (reset_code, expiry, actual_username))
        conn.commit()
        conn.close()
        
        # SMTP configurations
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port_raw = os.getenv("SMTP_PORT", "587")
        try:
            smtp_port = int(smtp_port_raw)
        except ValueError:
            smtp_port = 587
            
        smtp_email = os.getenv("SMTP_EMAIL")
        smtp_password = os.getenv("SMTP_PASSWORD")
        admin_email = os.getenv("ADMIN_EMAIL") or smtp_email
        
        if not smtp_email or not smtp_password:
            # Local Dev Mock Mode fallback if email credentials not set
            print(f"\n🔒 [MOCK RESET] SMTP credentials not set. Password Reset OTP for '{actual_username}' is: {reset_code}\n")
            return jsonify({
                "success": True, 
                "message": f"SMTP not configured. (Local Dev Mode) OTP Code is: {reset_code} (printed in server console log)"
            })
            
        # Send actual verification email
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "🔒 Admin Password Reset Code"
            msg["From"] = smtp_email
            msg["To"] = admin_email
            
            html_content = f"""
            <html>
              <body style="font-family: Arial, sans-serif; background-color: #09090e; color: #f3f4f6; padding: 30px;">
                <div style="max-width: 450px; margin: 0 auto; background: #14141d; border: 1px solid #232332; border-radius: 16px; padding: 24px; text-align: center;">
                  <h2 style="color: #ff3c3c; margin-bottom: 20px;">Admin Password Reset</h2>
                  <p style="color: #cbd5e1; font-size: 15px;">A password reset request was initiated for the admin account <strong>{actual_username}</strong>.</p>
                  <div style="font-size: 32px; font-weight: 800; color: #22d3ee; background: rgba(34, 211, 238, 0.1); padding: 16px; border-radius: 12px; margin: 24px 0; letter-spacing: 4px;">
                    {reset_code}
                  </div>
                  <p style="color: #94a3b8; font-size: 12px;">This verification code is valid for 10 minutes. If you did not request this, please ignore this email.</p>
                </div>
              </body>
            </html>
            """
            msg.attach(MIMEText(f"Admin Password Reset Code: {reset_code}", "plain"))
            msg.attach(MIMEText(html_content, "html"))
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_email, smtp_password)
            server.sendmail(smtp_email, admin_email, msg.as_string())
            server.quit()
            
            # Mask email address for response
            masked_email = admin_email
            if "@" in admin_email:
                parts = admin_email.split("@")
                masked_email = parts[0][:3] + "***@" + parts[1]
            return jsonify({"success": True, "message": f"Verification code successfully sent to {masked_email}!"})
        except Exception as smtp_err:
            print("SMTP DISPATCH ERROR:", smtp_err)
            return jsonify({
                "success": True,
                "message": f"SMTP Dispatch failed: {str(smtp_err)}. (Local Dev Mode) OTP Code is: {reset_code} (printed in server console log)"
            })
            
    except Exception as e:
        print("FORGOT PASSWORD ERROR:", e)
        return jsonify({"success": False, "message": f"Forgot password error: {str(e)}"})


# =========================================
# RESET PASSWORD API
# =========================================
@app.route("/api/reset_password", methods=["POST"])
def api_reset_password():
    try:
        from werkzeug.security import generate_password_hash
        import sqlite3
        import datetime
        
        data = request.get_json() or {}
        username = data.get("username", "").strip()
        reset_code = data.get("reset_code", "").strip()
        new_password = data.get("new_password", "").strip()
        
        if not username or not reset_code or not new_password:
            return jsonify({"success": False, "message": "All fields are required."})
            
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "movies.db")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        cur.execute("SELECT reset_code, reset_expiry FROM admin_credentials WHERE username = ?", (username,))
        row = cur.fetchone()
        
        if not row:
            conn.close()
            return jsonify({"success": False, "message": "Admin username not found."})
            
        db_code, db_expiry = row[0], row[1]
        
        if not db_code or db_code != reset_code:
            conn.close()
            return jsonify({"success": False, "message": "Invalid verification code."})
            
        # Check code expiration
        if db_expiry:
            try:
                expiry_dt = datetime.datetime.strptime(db_expiry, "%Y-%m-%d %H:%M:%S")
                if datetime.datetime.now() > expiry_dt:
                    conn.close()
                    return jsonify({"success": False, "message": "Verification code has expired."})
            except Exception as dt_err:
                print("Date parse error:", dt_err)
                
        # Hash new password and save
        hashed = generate_password_hash(new_password)
        cur.execute("""
            UPDATE admin_credentials
            SET password_hash = ?, reset_code = NULL, reset_expiry = NULL
            WHERE username = ?
        """, (hashed, username))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "Password successfully reset! You can now log in."})
    except Exception as e:
        print("RESET PASSWORD ERROR:", e)
        return jsonify({"success": False, "message": f"Reset password error: {str(e)}"})


# =========================================
# ADD MOVIE TO CATALOG (ADMIN ROUTE)
# =========================================
@app.route("/api/add_catalog_movie", methods=["POST"])
def api_add_catalog_movie():
    """
    API endpoint to add a new movie to the main movie_catalog database table.
    Expects a POST request with JSON containing:
      - title (str): The name of the movie (required).
      - genre (str): The movie genres.
      - description (str): Brief synopsis of the plot.
      - poster_url (str): Link to the movie poster.
      - trailer_url (str): YouTube trailer link.
    On successful insertion, it automatically populates three default showtimes,
    three ticket pricing tiers (Standard, IMAX, VIP), and two positive starter
    classmate/critic reviews to make the movie catalog entry immediately functional.
    """
    try:
        data = request.get_json() or {}
        title = data.get("title", "").strip()
        genre = data.get("genre", "").strip()
        description = data.get("description", "").strip()
        poster_url = data.get("poster_url", "").strip()
        trailer_url = data.get("trailer_url", "").strip()

        if not title:
            return jsonify({"success": False, "message": "Movie title is required."})

        # Save to database catalog
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "movies.db")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # Check if movie already exists in catalog
        cur.execute("SELECT id FROM movie_catalog WHERE LOWER(title) = LOWER(?)", (title,))
        if cur.fetchone():
            conn.close()
            return jsonify({"success": False, "message": f"Movie '{title}' already exists in the catalog."})

        # Insert movie into catalog
        cur.execute("""
            INSERT INTO movie_catalog (title, genre, description, poster_url, trailer_url)
            VALUES (?, ?, ?, ?, ?)
        """, (title, genre, description, poster_url, trailer_url))
        
        movie_id = cur.lastrowid

        # Automatically insert default showtimes
        import datetime
        today = datetime.date.today()
        dates = [
            today.strftime("%Y-%m-%d"),
            (today + datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
            (today + datetime.timedelta(days=2)).strftime("%Y-%m-%d")
        ]
        cur.executemany("""
            INSERT INTO showtimes (movie_id, show_date, show_time, theater)
            VALUES (?, ?, ?, ?)
        """, [
            (movie_id, dates[0], "14:30", "Screen 1 Standard"),
            (movie_id, dates[1], "18:00", "Screen 2 IMAX"),
            (movie_id, dates[2], "21:15", "Screen 3 VIP")
        ])

        # Automatically insert ticket tiers
        cur.executemany("""
            INSERT INTO ticket_tiers (movie_id, tier_name, price)
            VALUES (?, ?, ?)
        """, [
            (movie_id, "Standard", 12.0),
            (movie_id, "IMAX 3D", 18.0),
            (movie_id, "VIP Lounge", 25.0)
        ])

        # Automatically insert initial positive starter reviews
        cur.executemany("""
            INSERT INTO movie_comments (movie_id, username, comment, rating)
            VALUES (?, ?, ?, ?)
        """, [
            (movie_id, "CinemaCritic", "An absolute masterpiece! Must watch.", 5),
            (movie_id, "FilmLover99", "Very enjoyable experience. Loved the soundtrack and visuals.", 5)
        ])

        conn.commit()
        conn.close()

        # Force download poster locally if possible
        try:
            download_local_poster(title, poster_url)
        except Exception as ex:
            print("Failed downloading local poster for new catalog entry:", ex)

        return jsonify({"success": True, "message": f"'{title}' successfully added to the catalog!"})
    except Exception as e:
        print("ADD CATALOG MOVIE ERROR:", e)
        return jsonify({"success": False, "message": f"Server Error: {str(e)}"})


# =========================================
# UPDATE MOVIE IN CATALOG (ADMIN ROUTE)
# =========================================
@app.route("/api/update_catalog_movie", methods=["POST"])
def api_update_catalog_movie():
    try:
        data = request.get_json() or {}
        movie_id = data.get("id")
        title = data.get("title", "").strip()
        genre = data.get("genre", "").strip()
        description = data.get("description", "").strip()
        poster_url = data.get("poster_url", "").strip()
        trailer_url = data.get("trailer_url", "").strip()

        if not movie_id:
            return jsonify({"success": False, "message": "Movie ID is required."})
        if not title:
            return jsonify({"success": False, "message": "Movie title is required."})

        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "movies.db")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # Update movie in catalog
        cur.execute("""
            UPDATE movie_catalog
            SET title = ?, genre = ?, description = ?, poster_url = ?, trailer_url = ?
            WHERE id = ?
        """, (title, genre, description, poster_url, trailer_url, movie_id))
        
        # Also clean up and update any corresponding entry in movies table if titles match
        # (This keeps trailers working in the user watchlists too)
        clean_trailer = get_clean_embed_trailer(title, trailer_url)
        cur.execute("""
            UPDATE movies
            SET trailer_url = ?
            WHERE LOWER(title) = LOWER(?)
        """, (clean_trailer, title))

        conn.commit()
        conn.close()

        # Force download poster locally if possible
        try:
            download_local_poster(title, poster_url)
        except Exception as ex:
            print("Failed downloading local poster for updated catalog entry:", ex)

        return jsonify({"success": True, "message": f"'{title}' successfully updated in the catalog!"})
    except Exception as e:
        print("UPDATE CATALOG MOVIE ERROR:", e)
        return jsonify({"success": False, "message": f"Server Error: {str(e)}"})


# =========================================
# AUTOFILL METADATA API
# =========================================
def fetch_movie_metadata_online(title, genre=None):
    import urllib.parse
    import requests
    import os
    
    metadata = {
        "title": title,
        "genre": genre or "",
        "description": "",
        "poster_url": "",
        "trailer_url": ""
    }
    
    omdb_key = os.getenv("OMDB_API_KEY", "f5055ab1")
    tmdb_key = os.getenv("TMDB_API_KEY", "bdc72992529ba332516d99262db8ca95")
    
    # 1. Query OMDb
    try:
        omdb_url = f"http://www.omdbapi.com/?t={urllib.parse.quote(title)}&apikey={omdb_key}"
        r = requests.get(omdb_url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data.get("Response") != "False":
                metadata["title"] = data.get("Title", title)
                if not metadata["genre"]:
                    metadata["genre"] = data.get("Genre", "")
                metadata["description"] = data.get("Plot", "")
                metadata["poster_url"] = data.get("Poster", "")
    except Exception as e:
        print("OMDb autofill error:", e)
        
    # 2. Query TMDB (for high-res poster and trailers)
    try:
        if tmdb_key:
            search_url = f"https://api.themoviedb.org/3/search/movie?api_key={tmdb_key}&query={urllib.parse.quote(title)}"
            r = requests.get(search_url, timeout=5)
            if r.status_code == 200:
                search_data = r.json()
                results = search_data.get("results", [])
                if results:
                    movie_id = results[0]["id"]
                    # Use TMDB overview if description is empty or too short
                    if not metadata["description"] or len(metadata["description"]) < 50:
                        metadata["description"] = results[0].get("overview", "")
                    
                    # Use TMDB poster if OMDb poster is empty or "N/A"
                    poster_path = results[0].get("poster_path")
                    if poster_path and (not metadata["poster_url"] or metadata["poster_url"] == "N/A"):
                        metadata["poster_url"] = f"https://image.tmdb.org/t/p/w500{poster_path}"
                        
                    # Get TMDB videos for trailers
                    videos_url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={tmdb_key}"
                    v_r = requests.get(videos_url, timeout=5)
                    if v_r.status_code == 200:
                        videos = v_r.json().get("results", [])
                        for video in videos:
                            if video.get("site") == "YouTube" and video.get("type") in ["Trailer", "Teaser"]:
                                key = video.get("key")
                                if key:
                                    metadata["trailer_url"] = f"https://www.youtube.com/watch?v={key}"
                                    break
    except Exception as e:
        print("TMDB autofill error:", e)
        
    # 3. Fallback: If description/overview is missing or too short, generate a 2-3 sentence engaging summary using OpenAI
    desc = metadata.get("description", "").strip()
    if not desc or desc in ["N/A", ""]:
        try:
            prompt = f"Write a brief, engaging, 2-3 sentence movie plot summary/overview for a film titled '{title}'"
            if genre:
                prompt += f" of genre '{genre}'"
            prompt += ". Keep it cinematic and do not include any introductory phrases like 'Here is the summary' or metadata, just output the plot summary directly."
            
            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are a movie database editor who writes brief, engaging plot summaries."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            ai_desc = response.choices[0].message.content.strip()
            if ai_desc:
                metadata["description"] = ai_desc
        except Exception as ai_err:
            print("OpenAI description generation error:", ai_err)
    elif len(desc) > 300:
        # If the plot overview is very long, summarize it into 2-3 sentences automatically
        try:
            prompt = f"Summarize the following movie plot overview into a brief, engaging, 2-3 sentence summary (max 250 characters):\n\n{desc}"
            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are a movie editor specializing in writing concise, punchy plot summaries."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=120,
                temperature=0.7
            )
            ai_summary = response.choices[0].message.content.strip()
            if ai_summary:
                metadata["description"] = ai_summary
        except Exception as ai_err:
            print("OpenAI summarization error:", ai_err)

    return metadata

@app.route("/api/autofill_movie", methods=["POST"])
def api_autofill_movie():
    try:
        data = request.get_json() or {}
        title = data.get("title", "").strip()
        genre = data.get("genre", "").strip()
        if not title:
            return jsonify({"success": False, "message": "Title is required for autofill."})
            
        metadata = fetch_movie_metadata_online(title, genre)
        return jsonify({"success": True, "metadata": metadata})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


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
            request.form.get("poster_url"),
            request.form.get("trailer_url"),
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







# =========================
#  List Page
# =========================
@app.route('/list')
def list_route():
    return redirect(url_for('user_movies_route', user_id=1))

@app.route('/movie_list')
def movie_list():
    return redirect(url_for('user_movies_route', user_id=1))


# =========================
# Series Page
# =========================
@app.route('/series')
def series():
    return render_template('series.html')


# =========================
# Trending Movies Page
# =========================
@app.route('/trendy')
def trendy():
    return render_template('trendy.html')


# =========================
# Films Page
# =========================
@app.route('/film')
def film():
    return redirect(url_for('user_movies_route', user_id=1))

# =========================
# Recommended Movies
# =========================
@app.route('/recommend')
def recommend():
    return render_template('recommend.html')


# =========================
# Action Movies
# =========================
@app.route('/action')
def action():
    return render_template('action.html')


# =========================
# Comedy Movies
# =========================
@app.route('/comedy')
def comedy():
    return render_template('comedy.html')


# =========================
# Horror Movies
# =========================
@app.route('/horror')
def horror():
    return render_template('horror.html')


# =========================
# Sci-Fi Movies
# =========================
@app.route('/sci-fi')
def sci_fi():
    return render_template('sci-fi.html')



@app.route('/add_comment', methods=['POST'])
def add_comment():
    username = request.form.get('username')
    comment = request.form.get('comment')
    movie_id = request.form.get('movie_id')
    rating_val = request.form.get('rating', 5)
    try:
        rating = int(rating_val)
    except (TypeError, ValueError):
        rating = 5

    if username and comment and movie_id:
        try:
            m_id = int(movie_id)
            storage.add_movie_comment(m_id, username, comment, rating)
            print(f"Added comment for movie {m_id} by {username}")
        except Exception as e:
            print("Error adding comment to DB:", e)

    return redirect(request.referrer)


# =========================================
# MOVIE DETAIL PAGE
# =========================================
@app.route("/movie/<int:movie_id>")
def movie_detail(movie_id):
    import sqlite3
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "movies.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM movie_catalog WHERE id = ?", (movie_id,))
    row = cur.fetchone()
    conn.close()
    
    if not row:
        return redirect("/catalog")
        
    movie_catalog_data = dict(row)
    
    # Resolve high-fidelity poster locally
    local_poster = download_local_poster(movie_catalog_data["title"], movie_catalog_data["poster_url"])
    
    # Retrieve showtimes from database
    showtimes = get_showtimes(movie_id)
    showtimes_list = []
    for s in showtimes:
        showtimes_list.append({
            "date": s[0],
            "time": s[1],
            "screen": s[2]
        })
        
    # Fallback defensive showtimes
    if not showtimes_list:
        showtimes_list = [
            {"date": "Today", "time": "2:30 PM", "screen": "Screen 1 Standard"},
            {"date": "Today", "time": "6:00 PM", "screen": "Screen 2 IMAX"},
            {"date": "Tomorrow", "time": "9:15 PM", "screen": "Screen 3 VIP"}
        ]
        
    # Get movie reviews
    comments = storage.get_movie_comments(movie_id)
    comments_list = []
    for c in comments:
        comments_list.append({
            "username": c[0],
            "comment": c[1],
            "rating": c[2],
            "created_at": c[3]
        })
        
    movie_data = {
        "id": movie_catalog_data["id"],
        "title": movie_catalog_data["title"],
        "genre": movie_catalog_data["genre"],
        "description": movie_catalog_data["description"],
        "poster_url": local_poster,
        "trailer_url": get_clean_embed_trailer(movie_catalog_data["title"], movie_catalog_data["trailer_url"]),
        "year": "2023",
        "rating": "8.4"
    }
    
    banners = get_banner_movies()
    return render_template(
        "movie_detail.html",
        movie=movie_data,
        showtimes=showtimes_list,
        comments=comments_list,
        banners=banners,
        country_to_flag=country_to_flag
    )


# =========================================
# DEDICATED CONTROL CONSOLE DASHBOARD PAGE
# =========================================
@app.route("/dashboard")
def dashboard():
    import sqlite3
    catalog_count = 0
    saved_count = 0
    comment_count = 0
    feedbacks = []
    movie_reviews = []
    catalog_movies = []
    
    try:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "movies.db")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # Get count of catalog films
        cur.execute("SELECT COUNT(*) FROM movie_catalog")
        catalog_count = cur.fetchone()[0]
        
        # Get count of saved watchlist records
        cur.execute("SELECT COUNT(*) FROM movies")
        saved_count = cur.fetchone()[0]
        
        # Get count of customer movie comments
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='movie_comments'")
        if cur.fetchone():
            cur.execute("SELECT COUNT(*) FROM movie_comments")
            comment_count = cur.fetchone()[0]
            
        # Fetch all catalog movies for editing dropdown
        cur.execute("SELECT id, title, genre, description, poster_url, trailer_url FROM movie_catalog ORDER BY title ASC")
        for r in cur.fetchall():
            catalog_movies.append({
                "id": r[0],
                "title": r[1],
                "genre": r[2],
                "description": r[3],
                "poster_url": r[4],
                "trailer_url": r[5]
            })
            
        conn.close()
    except Exception as e:
        print("Error fetching dashboard data:", e)
        # Fallbacks
        catalog_count = catalog_count or 5
        saved_count = saved_count or 12
        comment_count = comment_count or 8

    banners = get_banner_movies()
    return render_template(
        "dashboard.html",
        catalog_count=catalog_count,
        saved_count=saved_count,
        comment_count=comment_count,
        feedbacks=feedbacks,
        movie_reviews=movie_reviews,
        catalog_movies=catalog_movies,
        banners=banners,
        country_to_flag=country_to_flag
    )


# =========================================
# API ENDPOINT FOR SUBMITTING PEER FEEDBACK
# =========================================
@app.route("/api/classmate_feedback", methods=["POST"])
def submit_classmate_feedback():
    import sqlite3
    data = request.get_json()
    if not data or "feedback" not in data or not data["feedback"].strip():
        return jsonify({"success": False, "message": "Feedback content is required."})
        
    try:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "movies.db")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # Ensure classmate_feedback table exists (defensive check)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS classmate_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cur.execute(
            "INSERT INTO classmate_feedback (username, feedback) VALUES (?, ?)",
            ("Anonymous Classmate", data["feedback"].strip())
        )
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Feedback submitted successfully."})
    except Exception as e:
        print("Error saving classmate feedback:", e)
        return jsonify({"success": False, "message": str(e)})


# =========================================
# =========================================
# SIMULATED LOCAL CINEMA WEBSITES (CORS/X-Frame-Options Safe)
# =========================================
CINEMAS_DATA = {
    "enugu": {
        "genesis-enugu": {
            "name": "Genesis Cinema Enugu",
            "address": "Zik Ave, Enugu, Nigeria",
            "rating": "⭐ 4.4",
            "website_url": "https://genesiscinemas.com",
            "movies": [
                {
                    "id": 4,
                    "title": "Interstellar",
                    "showtimes": ["5:00 PM (Standard)", "8:30 PM (Standard)"]
                }
            ]
        },
        "wnn-enugu": {
            "name": "WNN Cinema Enugu",
            "address": "Independent Layout, Enugu, Nigeria",
            "rating": "⭐ 4.3",
            "website_url": "https://www.google.com/search?q=WNN+Cinema+Enugu+showtimes",
            "movies": [
                {
                    "id": 3,
                    "title": "The Dark Knight",
                    "showtimes": ["7:45 PM (VIP)"]
                }
            ]
        }
    },
    "bochum": {
        "union-bochum": {
            "name": "Union Filmtheater Bochum",
            "address": "Kortumstraße 16, 44787 Bochum, Germany",
            "rating": "⭐ 4.5",
            "website_url": "https://www.union-kino.de",
            "movies": [
                {
                    "id": 1,
                    "title": "Inception",
                    "showtimes": ["3:00 PM (Standard)", "7:00 PM (Standard)"]
                }
            ]
        },
        "metropolis-bochum": {
            "name": "Metropolis Kino Bochum",
            "address": "Kortumstraße 51, 44787 Bochum, Germany",
            "rating": "⭐ 4.7",
            "website_url": "https://www.metropolis-bochum.de",
            "movies": [
                {
                    "id": 5,
                    "title": "Avatar: The Way of Water",
                    "showtimes": ["4:00 PM (3D)", "8:00 PM (3D)"]
                }
            ]
        }
    },
    "herne": {
        "filmwelt-herne": {
            "name": "Filmwelt Herne",
            "address": "Berliner Platz 11, 44623 Herne, Germany",
            "rating": "⭐ 4.2",
            "website_url": "https://www.filmwelt-herne.de",
            "movies": [
                {
                    "id": 4,
                    "title": "Interstellar",
                    "showtimes": ["6:30 PM (IMAX)", "9:30 PM (IMAX)"]
                }
            ]
        },
        "uci-herne": {
            "name": "UCI Kinowelt Ruhr Park",
            "address": "Am Einkaufszentrum 22, 44791 Bochum/Herne Border",
            "rating": "⭐ 4.4",
            "website_url": "https://www.uci-kinowelt.de",
            "movies": [
                {
                    "id": 3,
                    "title": "The Dark Knight",
                    "showtimes": ["5:15 PM (Standard)", "8:45 PM (Standard)"]
                }
            ]
        }
    },
    "berlin": {
        "zoo-palast-berlin": {
            "name": "Zoo Palast Berlin",
            "address": "Hardenbergstraße 29a, 10623 Berlin, Germany",
            "rating": "⭐ 4.8",
            "website_url": "https://www.zoopalast.de",
            "movies": [
                {
                    "id": 1,
                    "title": "Inception",
                    "showtimes": ["4:30 PM (VIP)", "8:00 PM (VIP)"]
                }
            ]
        },
        "cubix-berlin": {
            "name": "Cubix Alexanderplatz",
            "address": "Rathausstraße 1, 10178 Berlin, Germany",
            "rating": "⭐ 4.6",
            "website_url": "https://www.yorck.de",
            "movies": [
                {
                    "id": 5,
                    "title": "Avatar: The Way of Water",
                    "showtimes": ["3:00 PM (3D)", "7:30 PM (3D)"]
                }
            ]
        }
    }
}

@app.route("/cinema_website/<city>/<cinema_slug>")
def cinema_website(city, cinema_slug):
    city_key = city.lower().strip()
    cinema_key = cinema_slug.lower().strip()
    
    if city_key not in CINEMAS_DATA or cinema_key not in CINEMAS_DATA[city_key]:
        return "Cinema Website Not Found", 404
        
    cinema_info = CINEMAS_DATA[city_key][cinema_key]
    
    import sqlite3
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "movies.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    hydrated_movies = []
    for m in cinema_info["movies"]:
        cur.execute("SELECT id, title, genre, description, poster_url, trailer_url FROM movie_catalog WHERE id = ?", (m["id"],))
        row = cur.fetchone()
        if row:
            hydrated_movies.append({
                "id": row[0],
                "title": row[1],
                "genre": row[2],
                "description": row[3],
                "poster_url": download_local_poster(row[1], row[4]),
                "showtimes": m["showtimes"],
                "trailer_url": row[5]
            })
    conn.close()
    
    cinema_data = {
        "name": cinema_info["name"],
        "address": cinema_info["address"],
        "rating": cinema_info["rating"],
        "website_url": cinema_info.get("website_url", "#"),
        "movies": hydrated_movies
    }
    
    return render_template("cinema_website.html", cinema=cinema_data)


# DEDICATED REAL-TIME ANALYTICS PAGE (STREAMLIT IFRAME)
# =========================================
@app.route("/analytics")
def analytics():
    banners = get_banner_movies()
    return render_template(
        "analytics.html",
        banners=banners,
        country_to_flag=country_to_flag
    )






# =========================================
# RUN APP
# =========================================
if __name__ == "__main__":

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )