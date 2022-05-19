FROM python:3.9

WORKDIR /usr/src/app

RUN pip3 install gunicorn poetry \
    && poetry config virtualenvs.create false

COPY . .

RUN poetry install --no-interaction --no-ansi --no-dev

EXPOSE 80
CMD ["gunicorn", "unified_graphics.wsgi:app", "--bind=0.0.0.0:80"]
