FROM python:3.10-slim-bullseye

WORKDIR /usr/src/app

RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel \
    && pip3 install --no-cache-dir gunicorn poetry \
    && poetry config virtualenvs.create false

COPY . .

RUN apt-get update \
    && apt-get install -y build-essential \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*
RUN poetry install --no-interaction --no-ansi --without dev

RUN groupadd -g 1000 python && \
    useradd -r -u 1000 -g python python

USER 1000

EXPOSE 80
# Gunicorn recommends setting the number of workers to be 2-4 * num_cores
CMD ["gunicorn", "unified_graphics.wsgi:app", "--bind=0.0.0.0:80", "--timeout=600", "--workers=4"]
