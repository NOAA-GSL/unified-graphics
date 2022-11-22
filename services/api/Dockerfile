FROM python:3.11

WORKDIR /usr/src/app

RUN pip3 install --no-cache-dir gunicorn poetry \
    && poetry config virtualenvs.create false

COPY . .

RUN poetry install --no-interaction --no-ansi --no-dev
RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

EXPOSE 80
CMD ["gunicorn", "unified_graphics.wsgi:app", "--bind=0.0.0.0:80", "--timeout=600"]
