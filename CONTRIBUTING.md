# Unified Graphics Contributing Guide

## Project Structure

This is a monorepo composed of multiple services found in the `services/`
directory. The services are

- `services/api` — A Flask (Python) application that provides a RESTful API for
  the application
- `services/ui` — The frontend of the application, written with SvelteKit

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

### API Service

In development, you can run the Flask development server.

```
cd services/api
FLASK_ENV=development FLASK_APP=unified_graphics.wsgi:app FLASK_DIAG_DIR=... poetry run flask run
```

This will start up the Flask development server, which will watch the Python
code for changes and automatically reload the server. The development server is
available on http://localhost:5000.

To preview the production build, build and run the Docker image.

```
docker build -t unified-graphics/api:latest .
docker run --rm -p 5000:80 unified-graphics/api
```

#### Configuration

The application is configured using environment variables. The environment
variables are all prefixed with `FLASK_` so that Flask can find them and add
them automatically to its config.

- `FLASK_ENV` - Either “development” or “production” (default). When
  `FLASK_ENV=development`, the server adds a CORS header permitting connections
  from http://localhost:3000 so that the frontend can make requests without
  proxying
- `FLASK_DIAG_DIR` - The path to the local directory or S3 bucekt containing the
  NetCDF diagnostics files. Should be prefixed with `file://` or `s3://` depending
  on the storage backend used.

### UI Service

In development, you should run the development server with `npm`.

```
cd services/ui
UG_DIAG_API_HOST="http://localhost:5000" npm run dev
```

This will start up a Vite server that incrementally builds the application when
you make changes and loads them in the browser. The application will be
available at http://localhost:3000.

To preview the production build, you can either use SvelteKit’s preview
functionality:

```
npm run build
npm run preview
```

Or, better still, build the Docker container and run that:

```
docker build -t unified-graphics/ui:latest .
docker run --rm -p 3000:80 --env UG_DIAG_API_HOST=<API CONTAINER> unified-graphics/ui
```

#### Configuration

- `UG_DIAG_API_HOST` - The URL for the host where the API is located. In
  development, you can set this to `http://localhost:5000` to use the local
  version of the API

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
cd services/ui
npm test
```

## Coding Style

### Python

For Python code, we lint using `flake8` and format using `black`.

```
cd services/api
poetry run flake8 .
poetry run black .
```

### JavaScript

For JavaScript, SCSS, CSS, and HTML, we lint with either `eslint` or `stylelint`
and format using `prettier`. Stylelint enforces an order for CSS properties
based on the [9elements recommendations](https://9elements.com/css-rule-order/).

### Git Hooks

If you want to avoid getting scolded by CI for committing unlintend, unformatted
code, you can install our `pre-commit` hook from the `.githooks/` directory.

```
git config core.hookspath .githooks
```

The `pre-commit` script will check all of the files in your index with our
linters and formatters and warn you if any of the files fail linting and
formatting checks.
