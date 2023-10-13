# Unified Graphics Contributing Guide

## Building and Running

In development, you can run the Flask development server.

```
FLASK_APP=unified_graphics.wsgi:app FLASK_DIAG_ZARR=... poetry run flask run --debug
```

This will start up the Flask development server, which will watch the Python
code for changes and automatically reload the server. The development server is
available on http://localhost:5000.

### Configuration

The application is configured using environment variables. The environment
variables are all prefixed with `FLASK_` so that Flask can find them and add
them automatically to its config.

Flask supports `.env` files for storing environment variable configuration, so
you can define `FLASK_APP` and `FLASK_DIAG_ZARR` there to save yourself some typing
when running `flask run --debug`.

- `FLASK_APP` - The Python module containing the WSGI application: `unified_graphics.wsgi`
- `FLASK_DIAG_ZARR` - The path to the local directory or S3 bucket containing the
  Zarr diagnostics files. Should be prefixed with `file://` or `s3://` depending
  on the storage backend used. (Local files work with or without the file:// scheme)

## Testing

### Python

In our Python services we use `pytest` and `mypy` to test our code. You can run
these tests with `poetry`:

```
poetry run mypy src/
poetry run pytest
```

**Note**: You will need a postgres database and a `.env` file with the required
testing env variables set. You can do so with the following:

```
# Run a postgres container in the background ("-d")
$ docker run --name postgres15 -d -p 5432:5432 -e POSTGRES_PASSWORD=<password> -e POSTGRES_USER=postgres postgres:15

# Add the required variables to a .env file for testing
$ cat << EOF >> .env
TEST_DB_USER=postgres
TEST_DB_PASS=<password>
TEST_DB_HOST=localhost:5432
EOF
```

**Note**: There aren’t any type definitions for `pytest`, so running `mypy` on
the `tests/` directory results in errors. As such, it’s best to run `mypy` just
for our `src/` directory.

### JavaScript

JavaScript services use `npm` as a task runner, so running tests in a JavaScript
service is as simple as:

```
npm run vendor && npm run build
npm test
```

## Coding Style

### Python

For Python code, we lint using `flake8`, format using `black`, and sort imports with `isort`.

```
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


## Checking production infrastructure

The applications here are automatically deployed to an AWS account. If you need to check the logs in production you can do so by logging into the appropriate AWS console and then:

For the ETL application:

* Going to "Cloudwatch" -> "Log Groups". Logs are under the following log groups:
	* `/aws/lambda/rtma-vis-netcdf-processor`
	* `/aws/lambda/rtma-vis-nodd-processor`

For the web app:

* Connect via Session Manager to the `kubernetes-readonly-rtma-vis` EC2 instance
* Use kubectl to read the logs directly (`kubectl logs unified-graphics-api...`)
