from re import compile


async def parse_ids(raw_string: str) -> set:
    reg_exp = compile(r"https://www.kinopoisk.ru/film/(\d+)/")
    ids = reg_exp.findall(raw_string)
    return set(ids)


async def parse_refs(raw_string: str) -> set:
    reg_exp = compile(r"(https://www.kinopoisk.ru/film/\d+/)")
    refs = reg_exp.findall(raw_string)
    return set(refs)
