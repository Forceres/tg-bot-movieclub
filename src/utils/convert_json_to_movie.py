from telegram import Update

from src.utils.movie_dto import Movie


async def process_movies_json(responses: list, update: Update):
    movies = []
    for movie in responses:
        link = "https://www.kinopoisk.ru/film/%s/" % movie.get("id")
        directors = [
            person.get("name")
            for person in movie["persons"]
            if person.get("enProfession") == "director"
        ]
        directors = ",".join(directors) if len(directors) > 1 else directors[0]
        description = movie.get("description")
        if description is not None:
            description = (
                description.encode("utf-8")
                .decode("utf-8")
                .replace("\xa0", " ")
            )
        else:
            description = ""
        title = movie.get("name").encode("utf-8").decode("utf-8")
        countries = ",".join(
            [country.get("name") for country in movie.get("countries")]
        )
        genres = ",".join([genre.get("name") for genre in movie.get("genres")])
        movies.append(
            Movie(
                title=title,
                description=description,
                director=directors,
                year=movie.get("year"),
                countries=countries,
                genres=genres,
                link=link,
                duration=movie.get("movieLength"),
                imdb=movie.get("rating").get("imdb"),
                suggested_by=update.effective_user.full_name,
            ).to_list()
        )
    return movies
