import random
import statistics
import movie_storage_sql as storage
import movie_api as api
import website_generator as webgen


# =========================
# UI HEADER
# =========================

title = "My Movies Database"
width = 120

print("*" * width)
print(title.center(width))
print("*" * width)


# =========================
# HELPERS
# =========================

def safe_int_input(prompt: str) -> int:
    """Safely get integer input."""
    while True:
        value = input(prompt)
        if value.isdigit():
            return int(value)
        print("❌ Please enter a valid number.")


def get_user_by_id(user_id: int):
    users = storage.list_users()
    for user in users:
        if user[0] == user_id:
            return user
    return None


# =========================
# USER SYSTEM
# =========================

def select_user() -> int:
    users = storage.list_users()

    print("\nSelect a user:")
    for u in users:
        print(f"{u[0]}. {u[1]}")
    print("0. Create new user")

    choice = safe_int_input("Enter choice: ")

    if choice == 0:
        name = input("Enter new username: ").strip()
        if not name:
            print("❌ Invalid name.")
            return select_user()

        storage.add_user(name)
        return select_user()

    user = get_user_by_id(choice)
    if not user:
        print("❌ User not found.")
        return select_user()

    return choice


# =========================
# COMMANDS
# =========================

def command_list_movies(user_id: int) -> None:
    movies = storage.list_movies(user_id)

    if not movies:
        print("No movies yet.")
        return

    print(f"\n{len(movies)} movies in total")
    for title, data in movies.items():
        print(f"{title} ({data['year']}): {data['rating']}")


def command_add_movie(user_id: int) -> None:
    movie_title = input("Enter movie name: ").strip()

    if not movie_title:
        print("Invalid title.")
        return

    movies = storage.list_movies(user_id)
    if movie_title in movies:
        print("Movie already exists!")
        return

    print("Fetching data from API...")
    data = api.fetch_movie(movie_title)

    if not data:
        print("❌ Movie not found.")
        return

    try:
        movie_title = data["title"]
        year = int(data["year"])
        rating = float(data["rating"])
    except (KeyError, ValueError):
        print("⚠️ Invalid API data.")
        return

    poster_url = input("Poster URL (Enter = default): ").strip() or data.get("poster", "")
    trailer_url = input("Trailer URL (Enter = default): ").strip() or data.get("trailer", "")

    if "watch?v=" in trailer_url:
        trailer_url = trailer_url.replace("watch?v=", "embed/")

    country = data.get("country", "Unknown")

    storage.add_movie(
        user_id,
        movie_title,
        year,
        rating,
        poster_url,
        trailer_url,
        "",
        country
    )

    print("✅ Movie added!")


def command_delete_movie(user_id: int) -> None:
    movie_title = input("Enter movie to delete: ").strip()
    storage.delete_movie(user_id, movie_title)
    print("✅ Movie Deleted Successfully!")


def command_update_movie(user_id: int) -> None:
    """Update movie rating + reaction."""

    movie_title = input("Movie name: ").strip()
    rating = input("Rating: ").strip()

    #liked = input("Did you like this movie? (y/n): ").strip().lower()
    #thumbs = "👍" if liked == "y" else "👎"

    storage.update_movie_note(
        user_id,
        movie_title,
        rating,
        #thumbs
    )

    print(f"✅ Updated {movie_title} ")


def command_statistics(user_id: int) -> None:
    movies = storage.list_movies(user_id)

    if not movies:
        print("No movies.")
        return

    ratings = [m["rating"] for m in movies.values()]

    print("Average:", round(statistics.mean(ratings), 2))
    print("Median:", round(statistics.median(ratings), 2))


def command_random_movie(user_id: int) -> None:
    movies = storage.list_movies(user_id)

    if not movies:
        print("No movies.")
        return

    movie_title = random.choice(list(movies.keys()))
    movie = movies[movie_title]

    print(f"{movie_title} ({movie['year']}) - ⭐ {movie['rating']}")


def command_search_movie(user_id: int) -> None:
    movies = storage.list_movies(user_id)
    text = input("Search: ").lower()

    found = False

    for movie_title, data in movies.items():
        if text in movie_title.lower():
            print(f"{movie_title} ({data['year']}): {data['rating']}")
            found = True

    if not found:
        print("No matches.")


def command_sort_by_rating(user_id: int) -> None:
    movies = storage.list_movies(user_id)

    sorted_movies = sorted(
        movies.items(),
        key=lambda x: x[1]["rating"],
        reverse=True
    )

    for title, data in sorted_movies:
        print(f"{title} ({data['year']}): {data['rating']}")


def command_sort_by_year(user_id: int) -> None:
    movies = storage.list_movies(user_id)

    sorted_movies = sorted(
        movies.items(),
        key=lambda x: x[1]["year"],
        reverse=True
    )

    for title, data in sorted_movies:
        print(f"{title} ({data['year']}): {data['rating']}")


def command_generate_website(user_id: int) -> None:
    movies = storage.list_movies(user_id)
    user = get_user_by_id(user_id)

    if not user:
        print("User not found.")
        return

    username = user[1]
    webgen.generate(movies, username)

    print("🌐 Website generated!")


# =========================
# MENU
# =========================

def print_menu() -> None:
    print("\nMenu:")
    print("1. List movies")
    print("2. Add movie")
    print("3. Delete movie")
    print("4. Update movie")
    print("5. Generate website")
    print("6. Stats")
    print("7. Random movie")
    print("8. Search movie")
    print("9. Sort by rating")
    print("10. Sort by year")
    print("11. Switch user")
    print("0. Exit")


# =========================
# MAIN
# =========================

def main() -> None:
    storage.create_table()
    user_id = select_user()

    while True:
        print_menu()
        choice = safe_int_input("Choice: ")

        if choice == 1:
            command_list_movies(user_id)
        elif choice == 2:
            command_add_movie(user_id)
        elif choice == 3:
            command_delete_movie(user_id)
        elif choice == 4:
            command_update_movie(user_id)
        elif choice == 5:
            command_generate_website(user_id)
        elif choice == 6:
            command_statistics(user_id)
        elif choice == 7:
            command_random_movie(user_id)
        elif choice == 8:
            command_search_movie(user_id)
        elif choice == 9:
            command_sort_by_rating(user_id)
        elif choice == 10:
            command_sort_by_year(user_id)
        elif choice == 11:
            user_id = select_user()
        elif choice == 0:
            print("Goodbye!")
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()