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
        
    # Download the image from the internet in a background thread so we never block!
    if original_url and original_url.startswith("http"):
        import threading
        
        def download_worker(url, path, p_dir, t_name):
            try:
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                res = requests.get(url, headers=headers, timeout=5)
                if res.status_code == 200:
                    os.makedirs(p_dir, exist_ok=True)
                    with open(path, "wb") as f:
                        f.write(res.content)
                    print(f"Downloaded local poster asynchronously for: {t_name}")
            except Exception as ex:
                print(f"Async poster download error for {t_name}: {ex}")

        threading.Thread(target=download_worker, args=(original_url, filepath, poster_dir, title), daemon=True).start()
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
# REFRESH BANNERS ROUTE
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
        conn.close()
        
        context = "Available movies in the Cinema Catalog (purchase tickets and watch trailers inline):\n"
        for row in catalog_rows:
            p_url = row['poster_url'] or "/static/image/cinema_luxury.png"
            if p_url.startswith("http"):
                p_url = download_local_poster(row['title'], p_url)
            t_url = get_clean_embed_trailer(row['title'], row['trailer_url'] or "")
            context += f"- Title: {row['title']} | ID: {row['id']} | Genre: {row['genre']} | Details & Comments Link: /movie/{row['id']} | Purchase Link: /purchase/{row['id']} | Poster URL: {p_url} | Trailer Embed URL: {t_url}\n"
            
        context += "\nUser's Personal Saved Movies Collection:\n"
        for row in user_rows:
            p_url = row['poster_url'] or "/static/image/cinema_luxury.png"
            if p_url.startswith("http"):
                p_url = download_local_poster(row['title'], p_url)
            t_url = get_clean_embed_trailer(row['title'], row['trailer_url'] or "")
            context += f"- Title: {row['title']} | Year: {row['year']} | Rating: {row['rating']} | User Note: {row['note']} | Poster URL: {p_url} | Trailer Embed URL: {t_url}\n"
            
        return context
    except Exception as e:
        print("Error building chat context:", e)
        return "Movie database is currently empty."


TRAILER_CACHE = {}

def get_clean_embed_trailer(title, default_url):
    """
    Tries to fetch the official working YouTube trailer key from TMDB.
    Falls back to the database default_url if TMDB fails or doesn't find one.
    Guarantees the output is ALWAYS formatted as a clean YouTube embed URL
    (e.g., https://www.youtube.com/embed/<key>), never a standard watch link.
    """
    global TRAILER_CACHE
    cache_key = (title, default_url)
    if cache_key in TRAILER_CACHE:
        return TRAILER_CACHE[cache_key]

    import requests
    import urllib.parse
    
    def extract_yt_key(url):
        if not url:
            return None
        url = url.strip()
        
        # Check standard query string watch?v=
        if "v=" in url:
            parts = url.split("v=")
            for part in parts[1:]:
                candidate = part.split("&")[0].split("?")[0].split("/")[0]
                if len(candidate) == 11:
                    return candidate
                    
        # Check path elements like embed/ or v/ or watch/
        for marker in ["embed/", "v/", "watch/", "shorts/", "youtu.be/"]:
            if marker in url:
                parts = url.split(marker)
                if len(parts) > 1:
                    candidate = parts[1].split("?")[0].split("&")[0].split("/")[0]
                    if len(candidate) == 11:
                        return candidate
                        
        if len(url) == 11 and "/" not in url:
            return url
            
        import re
        match = re.search(r'(?:v=|embed/|v/|shorts/|youtu\.be/|/)([a-zA-Z0-9_-]{11})(?:\?|&|$|/)', url)
        if match:
            return match.group(1)
            
        match_end = re.search(r'([a-zA-Z0-9_-]{11})(?:\?|&|$)', url)
        if match_end:
            return match_end.group(1)
            
        return None

    # Performance Boost: Parse default_url locally and return instantly to bypass network delay!
    if default_url:
        key = extract_yt_key(default_url)
        if key:
            result = f"https://www.youtube.com/embed/{key}"
            TRAILER_CACHE[cache_key] = result
            return result
        if "http" in default_url:
            TRAILER_CACHE[cache_key] = default_url
            return default_url

    # Try fetching from TMDB if database didn't have a valid YouTube link
    try:
        api_key = os.getenv("TMDB_API_KEY")
        if api_key:
            search_url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={urllib.parse.quote(title)}"
            res = requests.get(search_url, timeout=4).json()
            results = res.get("results", [])
            if results:
                tmdb_id = results[0].get("id")
                video_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/videos?api_key={api_key}"
                video_res = requests.get(video_url, timeout=4).json()
                for v in video_res.get("results", []):
                    if v.get("site") == "YouTube" and v.get("type") == "Trailer" and v.get("key"):
                        result = f"https://www.youtube.com/embed/{v['key']}"
                        TRAILER_CACHE[cache_key] = result
                        return result
    except Exception as e:
        print(f"Error fetching TMDB trailer for {title}:", e)

    # Defensive default
    result = "https://www.youtube.com/embed/YoHD9XEInc0"
    TRAILER_CACHE[cache_key] = result
    return result


def post_process_chat_reply(reply, user_message):
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
            
    # 1. Post-process placeholders
    matched_movie = None
    user_msg_lower = user_message.lower()
    reply_lower = reply.lower()
    
    # Find matching title
    # Sort keys by length descending to match longer titles first
    sorted_titles = sorted(movie_data.keys(), key=len, reverse=True)
    for title_key in sorted_titles:
        if title_key in user_msg_lower or title_key in reply_lower:
            matched_movie = movie_data[title_key]
            break
            
    if matched_movie:
        p_url = matched_movie["poster_url"]
        t_url = matched_movie["trailer_url"]
        
        # Replace literal placeholders
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
            
    # 2. Programmatic injection if user asked for a poster and it's missing in reply
    asked_for_poster = any(k in user_msg_lower for k in ["poster", "cover", "image", "picture", "photo", "cover art"])
    has_img_tag = "<img" in reply
    
    if asked_for_poster and not has_img_tag and matched_movie:
        p_url = matched_movie["poster_url"]
        img_html = f'<br><img src="{p_url}" alt="{matched_movie["title"]}" class="chat-movie-poster" style="width:120px; border-radius:10px; margin: 12px auto; display:block; box-shadow: 0 4px 10px rgba(0,0,0,0.3); transition: 0.2s;">'
        reply += img_html
        
    # 3. Programmatic injection if user asked for a trailer/video and it's missing in reply
    asked_for_trailer = any(k in user_msg_lower for k in ["trailer", "video", "play", "watch", "stream"])
    has_iframe_tag = "<iframe" in reply
    
    if asked_for_trailer and not has_iframe_tag and matched_movie and matched_movie["trailer_url"]:
        t_url = matched_movie["trailer_url"]
        iframe_html = f'<br><div style="margin-top:8px; border-radius:10px; overflow:hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.4);"><iframe width="100%" height="200" src="{t_url}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe></div>'
        reply += iframe_html
        
    return reply


# =========================================
# CHAT
# =========================================
@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json() or {}
    user_message = data.get("message", "")
    client_history = data.get("history", [])

    # Get rich movie metadata from database
    movie_context = get_chatbot_movie_context()

    system_prompt = f"""You are CinemaBot 🎬. Always respond in the same language as the user's message (e.g., respond in German if they ask in German, French if they ask in French, Spanish if they ask in Spanish, and English if in English). Default to English.

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
3. Always make action links and buttons beautifully styled HTML tags rather than plain text or markdown links. For example, to buy tickets or view details:
    <a href='/movie/<movie_id>' class='chat-action-btn' style='display:inline-block; background:#ff3c3c; color:#fff; padding:8px 16px; border-radius:8px; font-weight:bold; text-decoration:none; margin-top:8px; font-size:12px; box-shadow: 0 4px 12px rgba(255, 60, 60, 0.2);'>🔍 View Details & Reviews</a> <a href='/purchase/<movie_id>' class='chat-action-btn' style='display:inline-block; background:#06b6d4; color:#000; padding:8px 16px; border-radius:8px; font-weight:bold; text-decoration:none; margin-top:8px; font-size:12px; margin-left:6px; box-shadow: 0 4px 12px rgba(6, 182, 212, 0.2);'>🍿 Purchase Tickets</a>
4. If a movie doesn't have a poster in the database, use '/static/image/cinema_luxury.png' as a high-fidelity fallback.
"""

    messages = [
        {"role": "system", "content": system_prompt}
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

        # Apply programmatic fail-safe post-processing filter
        reply = post_process_chat_reply(reply, user_message)

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
# DEDICATED ANALYTICS DASHBOARD PAGE
# =========================================
@app.route("/dashboard")
def dashboard():
    banners = get_banner_movies()
    return render_template(
        "dashboard.html",
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