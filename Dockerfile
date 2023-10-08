FROM python:3.11-slim

WORKDIR /tg-bot-movieclub

ARG PROD
ARG TOKEN
ARG DATABASE
ARG LEVEL
ARG ENV_FILE

ENV PROD=${PROD} \
    TOKEN=${TOKEN} \
    DATABASE=${DATABASE} \
    LEVEL=${LEVEL} \
    ENV_FILE=${ENV_FILE}

RUN ["python", "-m", "pip", "install", "pip", "--upgrade"]

RUN ["python", "-m", "pip", "install", "poetry", "--ignore-installed"]

COPY pyproject.toml poetry.lock /tg-bot-movieclub/

RUN ["poetry", "config", "virtualenvs.create", "false"]

RUN if [ "$PROD" = "1" ]; then \
      poetry install --no-ansi --no-interaction --no-root --no-dev; \
    else \
      poetry install --no-ansi --no-interaction --no-root; \
    fi

COPY ./test /tg-bot-movieclub/test/

RUN if [ "$PROD" = "1" ]; then rm -rf /tg-bot-movieclub/test ; fi

COPY ./src /tg-bot-movieclub/src/

RUN ["poetry", "run", "migration"]

RUN ["poetry", "run", "seeder"]

ENTRYPOINT ["poetry", "run", "python", "-m", "src.main"]