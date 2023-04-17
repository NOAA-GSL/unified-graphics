# Unified Graphics Contributing Guide

## Project Structure

This is a monorepo composed of multiple services found in the `services/`
directory. The services are

- `services/api` — A Flask (Python) application that provides a RESTful API for
  the application
- `services/data` — The Lambda function used to process incoming data

For the Python services, we use [poetry](https://python-poetry.org/) for
packaging. You will also need to install [pyenv](https://github.com/pyenv/pyenv)
so that `poetry` can create a virtual environment with the correct version of
Python.

For JavaScript services, we use `npm` for packaging and task running. You can
install [nvm](https://github.com/nvm-sh/nvm) to ensure you have the correct
version of Node; there is a `.nvmrc` file in the project root that defines the
version of Node we are targeting.

Each service is deployed inside a Docker container, so every service has a
`Dockerfile`.

## Building and Running

In development, you can run the Flask development server.

```
cd services/api
FLASK_DEBUG=true FLASK_APP=unified_graphics.wsgi:app FLASK_DIAG_ZARR=... poetry run flask run
```

This will start up the Flask development server, which will watch the Python
code for changes and automatically reload the server. The development server is
available on http://localhost:5000.

To preview the production build, build and run the Docker image.

```
docker build -t unified-graphics/api:latest .
docker run --rm -p 5000:80 unified-graphics/api
```

### Configuration

The application is configured using environment variables. The environment
variables are all prefixed with `FLASK_` so that Flask can find them and add
them automatically to its config.

- `FLASK_DEBUG` - Either “true” or “false” (default). When
  `FLASK_DEBUG=true`, the server adds a CORS header permitting connections
  from http://localhost:3000 so that the frontend can make requests without
  proxying
- `FLASK_DIAG_ZARR` - The path to the local directory or S3 bucekt containing the
  Zarr diagnostics files. Should be prefixed with `file://` or `s3://` depending
  on the storage backend used. (Local files work with or without the file:// scheme)

## Testing

### Python

In our Python services we use `pytest` and `mypy` to test our code. You can run
these tests with `poetry`:

```
cd services/api
poetry run mypy src/
poetry run pytest
```

**Note**: There aren’t any type definitions for `pytest`, so running `mypy` on
the `tests/` directory results in errors. As such, it’s best to run `mypy` just
for our `src/` directory.

### JavaScript

JavaScript services use `npm` as a task runner, so running tests in a JavaScript
service is as simple as:

```
cd services/api
npm run vendor && npm run build
npm test
```

## Coding Style

### Python

For Python code, we lint using `flake8`, format using `black`, and sort imports with `isort`.

```
cd services/api
poetry run flake8 .
poetry run black .
poetry run isort .
```

### JavaScript

For JavaScript, CSS, and HTML, we lint with either `eslint` or `stylelint`
and format using `prettier`. Stylelint enforces an alphabetical order for CSS
properties.

### Git Hooks

If you want to avoid getting scolded by CI for committing unlintend, unformatted
code, you can install the [pre-commit](https://pre-commit.com/) package for
running our hooks

```
pip3 install --user pre-commit
```

The `pre-commit` script will check all of the files in your index with our
linters and formatters and warn you if any of the files fail linting and
formatting checks.
