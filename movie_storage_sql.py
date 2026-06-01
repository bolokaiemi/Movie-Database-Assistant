import requests
import os
from movie_api import fetch_movie
import sqlite3
from datetime import datetime
import tmdbsimple
from dotenv import load_dotenv
# =========================
# LOAD ENV VARIABLES
# =========================
load_dotenv()

OMDB_API_KEY = os.environ.get("OMDB_API_KEY")
TMDB_API_KEY = os.environ.get("TMDB_API_KEY")

tmdbsimple.API_KEY = TMDB_API_KEY

# ==========================================
# TMDb API Configuration
# ==========================================
# Get FREE API Key:
# https://www.themoviedb.org/settings/api


BASE_URL = "https://api.themoviedb.org/3"

IMAGE_BASE_URL = "https://image.tmdb.org/t/p/original"


DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "movies.db")


# =========================
# CONNECTION
# =========================
def connect():
    return sqlite3.connect(DB_NAME)


# =========================
# CREATE TABLES
# =========================
def create_table():

    conn = connect()
    cursor = conn.cursor()

    # =========================
    # USERS TABLE
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    """)


    # =========================
    # MOVIES TABLE
    # =========================
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS movies
                   (
                       id          INTEGER PRIMARY KEY AUTOINCREMENT,
                       user_id     INTEGER,
                       title       TEXT NOT NULL,
                       poster_url  TEXT,
                       year        INTEGER,
                       rating      REAL,
                       description TEXT,
                       trailer_url TEXT,
                       note        TEXT,
                       country     TEXT,
                       date        TEXT,
                       time        TEXT,
                       screen      TEXT,
                       created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                   )
                   """)

    print("Database created with clean poster_url and trailer_url columns.")

    # =========================
    # MOVIE CATALOG TABLE
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movie_catalog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE,
            genre TEXT,
            description TEXT,
            poster_url TEXT,
            trailer_url TEXT
        )
    """)

    # =========================
    # SHOWTIMES TABLE
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS showtimes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER,
            show_date TEXT,
            show_time TEXT,
            theater TEXT,

            FOREIGN KEY(movie_id)
            REFERENCES movie_catalog(id)
        )
    """)

    # =========================
    # TICKET TIERS TABLE
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ticket_tiers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER,
            tier_name TEXT,
            price REAL,

            FOREIGN KEY(movie_id)
            REFERENCES movie_catalog(id)
        )
    """)

    # =========================
    # FOOD PURCHASES TABLE
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS concessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            movie_id INTEGER,
            popcorn_size TEXT,
            drink_size TEXT,
            total REAL,

            FOREIGN KEY(user_id)
            REFERENCES users(id),

            FOREIGN KEY(movie_id)
            REFERENCES movie_catalog(id)
        )
    """)

    # =========================
    # QR PURCHASES TABLE
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS qr_purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            movie_id INTEGER,
            qr_code_link TEXT,
            created_at TEXT,

            FOREIGN KEY(user_id)
            REFERENCES users(id),

            FOREIGN KEY(movie_id)
            REFERENCES movie_catalog(id)
        )
    """)

    # =========================
    # CHAT MEMORY TABLE
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            role TEXT,
            message TEXT,
            created_at TEXT,

            FOREIGN KEY(user_id)
            REFERENCES users(id)
        )
    """)

    # =========================
    # MOVIE COMMENTS TABLE
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movie_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER,
            username TEXT,
            comment TEXT,
            rating INTEGER DEFAULT 5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(movie_id) REFERENCES movie_catalog(id)
        )
    """)

    conn.commit()
    conn.close()


# =========================
# USERS FUNCTIONS
# =========================
def add_user(name):

    conn = connect()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO users (name) VALUES (?)",
            (name,)
        )

        conn.commit()

    except sqlite3.IntegrityError:
        print("User already exists.")

    conn.close()


def list_users():

    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users")

    users = cur.fetchall()

    conn.close()

    return users


def get_user(user_id):

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM users WHERE id=?",
        (user_id,)
    )

    user = cur.fetchone()

    conn.close()

    return user


# =========================
# MOVIE FUNCTIONS
# =========================
def add_movie(
    user_id,
    title,
    year,
    rating,
    poster_url="",
    trailer_url="",
    note="",
    country=""
):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO movies
        (
            user_id,
            title,
            year,
            rating,
            poster_url,
            trailer_url,
            note,
            country
           
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ? )

    """, (
        user_id,
        title,
        year,
        rating,
        poster_url,
        trailer_url,
        note,
        country
    ))

    conn.commit()
    conn.close()






def list_movies(user_id):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            title,
            year,
            rating,
            poster_url,
            trailer_url,
            note,
            country

        FROM movies

        WHERE user_id = ?
    """, (user_id,))

    rows = cur.fetchall()

    conn.close()

    movies = {}

    for row in rows:

        movies[row[0]] = {
            "year": row[1],
            "rating": row[2],
            "poster_url": row[3],
            "trailer_url": row[4],
            "note": row[5],
            "country": row[6]
        }

    return movies


def delete_movie(user_id, title):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM movies
        WHERE title = ?
        AND user_id = ?
    """, (title, user_id))

    conn.commit()
    conn.close()

    print(f"{title} deleted.")


def update_movie_note(user_id, title, note):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        UPDATE movies

        SET note = ?

        WHERE title = ?
        AND user_id = ?
    """, (note, title, user_id))

    conn.commit()
    conn.close()


def update_movie_rating(user_id, title, rating):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        UPDATE movies

        SET rating = ?

        WHERE title = ?
        AND user_id = ?
    """, (rating, title, user_id))

    conn.commit()
    conn.close()


def update_movie(user_id, title, rating, poster_url):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        UPDATE movies

        SET
            rating = ?,
            poster_url = ?

        WHERE title = ?
        AND user_id = ?
    """, (
        rating,
        poster_url,
        title,
        user_id
    ))

    conn.commit()
    conn.close()


# =========================
# MOVIE CATALOG FUNCTIONS
# =========================
def add_catalog_movie(
    title,
    genre,
    description,
    poster_url,
    trailer_url
):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO movie_catalog
        (
            title,
            genre,
            description,
            poster_url,
            trailer_url
        )

        VALUES (?, ?, ?, ?, ?)
    """, (
        title,
        genre,
        description,
        poster_url,
        trailer_url
    ))

    conn.commit()
    conn.close()


def list_catalog_movies():

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            title,
            genre,
            description,
            poster_url,
            trailer_url

        FROM movie_catalog
    """)

    movies = cur.fetchall()

    conn.close()

    return movies


# =========================
# MOVIE COMMENTS FUNCTIONS
# =========================
def add_movie_comment(movie_id, username, comment, rating=5):
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO movie_comments (movie_id, username, comment, rating)
        VALUES (?, ?, ?, ?)
    """, (movie_id, username, comment, rating))
    conn.commit()
    conn.close()


def get_movie_comments(movie_id):
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT username, comment, rating, created_at
        FROM movie_comments
        WHERE movie_id = ?
        ORDER BY id DESC
    """, (movie_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


# =========================
# SHOWTIMES FUNCTIONS
# =========================
def add_showtime(
    movie_id,
    show_date,
    show_time,
    theater
):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO showtimes
        (
            movie_id,
            show_date,
            show_time,
            theater
        )

        VALUES (?, ?, ?, ?)
    """, (
        movie_id,
        show_date,
        show_time,
        theater
    ))

    conn.commit()
    conn.close()


def get_showtimes(movie_id):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            show_date,
            show_time,
            theater

        FROM showtimes

        WHERE movie_id = ?
    """, (movie_id,))

    rows = cur.fetchall()

    conn.close()

    return rows


# =========================
# TICKET FUNCTIONS
# =========================
def add_ticket_tier(
    movie_id,
    tier_name,
    price
):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO ticket_tiers
        (
            movie_id,
            tier_name,
            price
        )

        VALUES (?, ?, ?)
    """, (
        movie_id,
        tier_name,
        price
    ))

    conn.commit()
    conn.close()


def get_ticket_tiers(movie_id):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            tier_name,
            price

        FROM ticket_tiers

        WHERE movie_id = ?
    """, (movie_id,))

    rows = cur.fetchall()

    conn.close()

    return rows


# =========================
# CONCESSIONS
# =========================
def add_concession_purchase(
    user_id,
    movie_id,
    popcorn_size,
    drink_size,
    total
):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO concessions
        (
            user_id,
            movie_id,
            popcorn_size,
            drink_size,
            total
        )

        VALUES (?, ?, ?, ?, ?)
    """, (
        user_id,
        movie_id,
        popcorn_size,
        drink_size,
        total
    ))

    conn.commit()
    conn.close()


# =========================
# QR CODE PURCHASES
# =========================
def add_qr_purchase(
    user_id,
    movie_id,
    qr_code_link
):

    conn = connect()
    cur = conn.cursor()

    created_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    cur.execute("""
        INSERT INTO qr_purchases
        (
            user_id,
            movie_id,
            qr_code_link,
            created_at
        )

        VALUES (?, ?, ?, ?)
    """, (
        user_id,
        movie_id,
        qr_code_link,
        created_at
    ))

    conn.commit()
    conn.close()


# =========================
# MULTI-TURN MEMORY
# =========================
def save_chat_message(
    user_id,
    role,
    message
):

    conn = connect()
    cur = conn.cursor()

    created_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    cur.execute("""
        INSERT INTO chat_memory
        (
            user_id,
            role,
            message,
            created_at
        )

        VALUES (?, ?, ?, ?)
    """, (
        user_id,
        role,
        message,
        created_at
    ))

    conn.commit()
    conn.close()


def get_chat_history(user_id, limit=20):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            role,
            message

        FROM chat_memory

        WHERE user_id = ?

        ORDER BY id DESC

        LIMIT ?
    """, (
        user_id,
        limit
    ))

    rows = cur.fetchall()

    conn.close()

    history = []

    for row in reversed(rows):

        history.append({
            "role": row[0],
            "content": row[1]
        })

    return history


# =========================
# TYPING INDICATOR
# =========================
typing_status = {}


def set_typing(user_id, status=True):
    typing_status[user_id] = status


def is_typing(user_id):
    return typing_status.get(user_id, False)




# ==========================================
# SQLite Database
# ==========================================
DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "movies.db")


def create_banner_table():
    """Create banner_movies table."""

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS banner_movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            title TEXT,
            category TEXT,

            release_date TEXT,
            rating REAL,

            overview TEXT,

            poster_path TEXT,
            backdrop_path TEXT,

            poster_url TEXT,
            banner_url TEXT,

            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


# ==========================================
# Save Movies To SQLite
# ==========================================
def save_banner_movies(movies, category):
    """Save banner movies into SQLite database."""

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    for movie in movies:

        poster_path = movie.get("poster_path", "")
        backdrop_path = movie.get("backdrop_path", "")

        poster_url = (
            f"{IMAGE_BASE_URL}{poster_path}"
            if poster_path else ""
        )

        banner_url = (
            f"{IMAGE_BASE_URL}{backdrop_path}"
            if backdrop_path else ""
        )

        cursor.execute("""
            INSERT INTO banner_movies (
                title,
                category,
                release_date,
                rating,
                overview,

                poster_path,
                backdrop_path,

                poster_url,
                banner_url,

                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            movie.get("title"),

            category,

            movie.get("release_date"),

            movie.get("vote_average"),

            movie.get("overview"),

            poster_path,
            backdrop_path,

            poster_url,
            banner_url,

            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

    conn.commit()
    conn.close()


# ==========================================
# Fetch Dynamic Banner Movies
# ==========================================
def fetch_banner_movies():
    """
    Fetch movies for homepage sliding banners.

    Categories:
    - Trending
    - Highest Rated
    - Sci-Fi
    - Classics
    - New Releases
    - Award Style Movies
    """

    categories = {

        # Trending Movies
        "trending":
            f"{BASE_URL}/trending/movie/week?api_key={TMDB_API_KEY}",

        # Highest Rated Movies
        "top_rated":
            f"{BASE_URL}/movie/top_rated?api_key={TMDB_API_KEY}",

        # Sci-Fi Movies
        # Genre ID = 878
        "sci_fi":
            f"{BASE_URL}/discover/movie?api_key={TMDB_API_KEY}&with_genres=878",

        # Classic Movies
        "classics":
            f"{BASE_URL}/discover/movie?api_key={TMDB_API_KEY}"
            f"&primary_release_date.lte=1990-01-01"
            f"&sort_by=vote_average.desc",

        # New Releases
        "new_releases":
            f"{BASE_URL}/movie/now_playing?api_key={TMDB_API_KEY}",

        # Award-Winning Style Movies
        "award_winners":
            f"{BASE_URL}/discover/movie?api_key={TMDB_API_KEY}"
            f"&sort_by=vote_average.desc"
            f"&vote_count.gte=5000"
    }

    create_banner_table()

    for category, url in categories.items():

        try:
            response = requests.get(url)

            data = response.json()

            movies = data.get("results", [])[:10]

            save_banner_movies(movies, category)

            print(f"Saved {len(movies)} movies for {category}")

        except Exception as e:
            print(f"Error fetching {category} movies:", e)


# ==========================================
# Get Banner Movies From Database
# ==========================================
def get_banner_movies(category=None):
    """Retrieve banner movies from SQLite."""

    conn = sqlite3.connect(DB_NAME)

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    if category:
        cursor.execute("""
            SELECT *
            FROM banner_movies
            WHERE category = ?
            ORDER BY rating DESC
        """, (category,))
        local_movies = [dict(row) for row in cursor.fetchall()]
    else:
        # Fetch the top 2 movies from each category to ensure a diverse showcase
        categories = ["trending", "top_rated", "sci_fi", "classics", "new_releases", "award_winners"]
        local_movies = []
        for cat in categories:
            cursor.execute("""
                SELECT *
                FROM banner_movies
                WHERE category = ?
                ORDER BY created_at DESC, rating DESC
                LIMIT 2
            """, (cat,))
            local_movies.extend([dict(row) for row in cursor.fetchall()])

    conn.close()

    return local_movies


# ==========================================
# Example Flask Route
# ==========================================
"""
from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():

    banners = get_banner_movies()

    return render_template(
        "index.html",
        banners=banners
    )
"""


# ==========================================
# Example HTML Banner Slider
# ==========================================
"""
<div class="banner-slider">

    {% for movie in banners %}

        <div class="banner-slide">

            <img
                src="{{ movie.banner_url }}"
                alt="{{ movie.title }}"
                class="banner-image"
            >

            <div class="banner-content">

                <h1>{{ movie.title }}</h1>

                <p>{{ movie.overview }}</p>

                <span>{{ movie.category }}</span>

                <span>⭐ {{ movie.rating }}</span>

            </div>

        </div>

    {% endfor %}

</div>
"""






# =========================
# INITIALIZE DATABASE
# =========================
if __name__ == "__main__":

    create_table()

    # Fetch fresh banner movies
    fetch_banner_movies()

    # Example output
    movies = get_banner_movies()

    print(movies[:3])

    print("🎬 Movies database upgraded successfully.")