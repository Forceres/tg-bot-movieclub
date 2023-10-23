from dataclasses import dataclass


@dataclass
class Movie:
    title: str
    description: str
    director: str
    year: int
    countries: str
    genres: str
    link: str
    duration: int
    imdb: float
    suggested_by: str

    def to_list(self):
        return list(self.__dict__.values())
