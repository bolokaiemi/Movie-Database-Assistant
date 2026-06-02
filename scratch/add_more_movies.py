import sqlite3
import os
import datetime

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "movies.db")

new_movies = [
    (
        "Oppenheimer",
        "Drama / Biography",
        "The story of American scientist J. Robert Oppenheimer and his role in the development of the atomic bomb.",
        "https://image.tmdb.org/t/p/w500/8Gxv2wSbs86QTuZ58T2sgTc1CcA.jpg",
        "https://www.youtube.com/embed/uYPbbEG8y0c"
    ),
    (
        "Spider-Man: Into the Spider-Verse",
        "Animation / Sci-Fi / Action",
        "Teen Miles Morales becomes the Spider-Man of his universe, and must join with five spider-powered individuals from other dimensions to stop a threat for all realities.",
        "https://image.tmdb.org/t/p/w500/iiZZN63i7P2tdww9pcVsuu3ABjC.jpg",
        "https://www.youtube.com/embed/g4HbzQF471Y"
    ),
    (
        "Dune: Part Two",
        "Sci-Fi / Adventure",
        "Follow the mythic journey of Paul Atreides as he unites with Chani and the Fremen while on a path of revenge against the conspirators who destroyed his family.",
        "https://image.tmdb.org/t/p/w500/czemb6f2BhTyYiJ7W5w4YWbJ1ST.jpg",
        "https://www.youtube.com/embed/Way9Dexny3w"
    ),
    (
        "Barbie",
        "Comedy / Fantasy",
        "Barbie and Ken are having the time of their lives in the colorful and seemingly perfect world of Barbie Land. However, when they get a chance to go to the real world, they soon discover the joys and perils of living among humans.",
        "https://image.tmdb.org/t/p/w500/iuFNmZ51jW6J6qR46B6vR6EvwA9.jpg",
        "https://www.youtube.com/embed/pBk4NYhWNMM"
    ),
    (
        "The Lord of the Rings: The Fellowship of the Ring",
        "Fantasy / Adventure",
        "An ancient Ring thought lost for centuries has been found, and through a strange twist in fate has been given to a small Hobbit named Frodo.",
        "https://image.tmdb.org/t/p/w500/6oom5QDN2187KMW3BEiIQ0m2X5c.jpg",
        "https://www.youtube.com/embed/V75dMMIW2B4"
    ),
    (
        "The Lord of the Rings: The Return of the King",
        "Fantasy / Adventure",
        "Aragorn is revealed as the heir to the ancient kings as he, Gandalf and the other members of the broken fellowship struggle to save Gondor from Sauron's forces.",
        "https://image.tmdb.org/t/p/w500/rC0a0t14vJ1J4iT7gl3O68A0J7W.jpg",
        "https://www.youtube.com/embed/r5X-hFf6Bwo"
    ),
    (
        "Parasite",
        "Thriller / Drama",
        "Greed and class discrimination threaten the newly formed symbiotic relationship between the wealthy Park family and the destitute Kim clan.",
        "https://image.tmdb.org/t/p/w500/7IiTT05EX2V2v9G9uXn6n6IQz7y.jpg",
        "https://www.youtube.com/embed/5xH0HfJHsaY"
    ),
    (
        "Fight Club",
        "Drama / Thriller",
        "An insomniac office worker and a devil-may-care soap maker form an underground fight club that evolves into much more.",
        "https://image.tmdb.org/t/p/w500/bptfRGE27n36RWSyWvV7sCwCIE3.jpg",
        "https://www.youtube.com/embed/qtRqhHHDtRY"
    ),
    (
        "The Shawshank Redemption",
        "Drama",
        "Over the course of several years, two convicts form a friendship, seeking consolation and, eventually, redemption through basic compassion.",
        "https://image.tmdb.org/t/p/w500/9cqN6GOUuOYfr46Y4LSs5FTQwZq.jpg",
        "https://www.youtube.com/embed/PLl99DlL6b4"
    ),
    (
        "Pulp Fiction",
        "Crime / Thriller",
        "The lives of two mob hitmen, a boxer, a gangster and his wife, and a pair of diner bandits intertwine in four tales of violence and redemption.",
        "https://image.tmdb.org/t/p/w500/f1Exj5240212f71J0eJgKjYtS3p.jpg",
        "https://www.youtube.com/embed/s7EdQ4FqbhY"
    ),
    (
        "Spirited Away",
        "Animation / Fantasy",
        "During her family's move to the suburbs, a sullen 10-year-old girl wanders into a world ruled by gods, witches, and spirits, and where humans are changed into beasts.",
        "https://image.tmdb.org/t/p/w500/393mh1e064Fiy8fv75o57Z7rqo1.jpg",
        "https://www.youtube.com/embed/ByXuk9QqQkk"
    ),
    (
        "The Lion King",
        "Animation / Drama / Adventure",
        "A young lion prince is cast out of his pride by his cruel uncle, who claims he killed his father. While the uncle rules with an iron paw, the prince grows up beyond the Savannah.",
        "https://image.tmdb.org/t/p/w500/s8Zssm7sOmsP1w61Auh0gHhQ2uB.jpg",
        "https://www.youtube.com/embed/4sj1MT05lAA"
    ),
    (
        "Jurassic Park",
        "Sci-Fi / Adventure",
        "A pragmatic paleontologist visiting an almost complete theme park is tasked with protecting a couple of kids after a power failure causes the park's cloned dinosaurs to run loose.",
        "https://image.tmdb.org/t/p/w500/b1xCNny2zwZ5w4uX078v27i2Flv.jpg",
        "https://www.youtube.com/embed/QWBKEmWWL38"
    ),
    (
        "Whiplash",
        "Drama / Music",
        "A promising young drummer enrolls at a cut-throat music conservatory where his dreams of greatness are mentored by an instructor who will stop at nothing to realize a student's potential.",
        "https://image.tmdb.org/t/p/w500/7th8R3k3nptqg5m5tS8eK7Rpx.jpg",
        "https://www.youtube.com/embed/7d_jQyGldo4"
    ),
    (
        "The Truman Show",
        "Drama / Comedy",
        "An insurance salesman discovers his whole life is actually a reality TV show.",
        "https://image.tmdb.org/t/p/w500/uX2uGh4ZFOg6XB20Li5wZjmdgdY.jpg",
        "https://www.youtube.com/embed/dlnmQbPGuls"
    ),
    (
        "Ratatouille",
        "Animation / Comedy",
        "A rat who can cook makes an unusual alliance with a young kitchen worker at a famous Paris restaurant.",
        "https://image.tmdb.org/t/p/w500/t3zgdPavUg53wtsmGFhrA8CDXYz.jpg",
        "https://www.youtube.com/embed/NgsQ8mWPkxw"
    ),
    (
        "Coco",
        "Animation / Adventure",
        "Aspiring musician Miguel, confronted with his family's ancestral ban on music, enters the Land of the Dead to find his great-great-grandfather, a legendary singer.",
        "https://image.tmdb.org/t/p/w500/gGE2S5254tTZbup1w2nziPRr76m.jpg",
        "https://www.youtube.com/embed/Rvr68u6k5sI"
    ),
    (
        "Star Wars: The Empire Strikes Back",
        "Sci-Fi / Adventure / Fantasy",
        "After the Rebels are brutally overpowered by the Empire on the ice planet Hoth, Luke Skywalker begins Jedi training with Yoda, while his friends are pursued by Darth Vader.",
        "https://image.tmdb.org/t/p/w500/n8V0W07hTzwtr5i6V0ef47vOI4v.jpg",
        "https://www.youtube.com/embed/JNwNXF9Y6C8"
    )
]

def run_seed():
    print(f"Connecting to database at {db_path}...")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # 1. Fetch current movie titles to prevent duplicates
    cur.execute("SELECT title FROM movie_catalog")
    existing_titles = {r[0] for r in cur.fetchall()}
    
    added_count = 0
    today = datetime.date.today()
    dates = [
        today.strftime("%Y-%m-%d"),
        (today + datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
        (today + datetime.timedelta(days=2)).strftime("%Y-%m-%d")
    ]
    
    for title, genre, desc, poster, trailer in new_movies:
        if title in existing_titles:
            print(f"Skipping '{title}' (already in catalog)")
            continue
            
        # Insert movie
        cur.execute("""
            INSERT INTO movie_catalog (title, genre, description, poster_url, trailer_url)
            VALUES (?, ?, ?, ?, ?)
        """, (title, genre, desc, poster, trailer))
        
        movie_id = cur.lastrowid
        print(f"Added film '{title}' with ID {movie_id}")
        
        # Insert 3 showtimes
        cur.executemany("""
            INSERT INTO showtimes (movie_id, show_date, show_time, theater)
            VALUES (?, ?, ?, ?)
        """, [
            (movie_id, dates[0], "14:30", "Screen 1 Standard"),
            (movie_id, dates[1], "18:00", "Screen 2 IMAX"),
            (movie_id, dates[2], "21:15", "Screen 3 VIP")
        ])
        
        # Insert 3 ticket tiers
        cur.executemany("""
            INSERT INTO ticket_tiers (movie_id, tier_name, price)
            VALUES (?, ?, ?)
        """, [
            (movie_id, "Standard", 12.0),
            (movie_id, "IMAX 3D", 18.0),
            (movie_id, "VIP Lounge", 25.0)
        ])
        
        # Insert positive starter reviews
        cur.executemany("""
            INSERT INTO movie_comments (movie_id, username, comment, rating)
            VALUES (?, ?, ?, ?)
        """, [
            (movie_id, "CinemaCritic", f"An absolute masterpiece! Must watch.", 5),
            (movie_id, "FilmLover99", f"Very enjoyable experience. Loved the soundtrack and visuals.", 5)
        ])
        
        added_count += 1
        
    conn.commit()
    conn.close()
    print(f"Database successfully updated. Added {added_count} new premium blockbusters with showtimes, ticket tiers, and starter reviews.")

if __name__ == "__main__":
    run_seed()
