def generate(movies, username):

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{username}'s Movies</title>
</head>

<body>

<h1>{username}'s Movie Collection</h1>

<div>
"""

    for title, movie in movies.items():
        html += f"""
        <div>
            <h3>{title}</h3>
            <p>{movie.get('year','')}</p>
            <p>{movie.get('rating','')}</p>
            <img src="{movie.get('poster_url','')}" width="150">
        </div>
        """

    html += """
</div>

</body>
</html>
"""

    with open("generated_site.html", "w", encoding="utf-8") as f:
        f.write(html)