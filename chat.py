def build_movie_context(user_id):

    import movie_storage_sql as storage

    movies = storage.list_movies(user_id)

    if not movies:
        return "User has no saved movies yet."

    context = "User movie database:\n\n"

    for title, data in movies.items():

        context += f"""
Movie: {title}
Year: {data['year']}
Rating: {data['rating']}
Country: {data['country']}
User Note: {data['note']}
"""

    return context