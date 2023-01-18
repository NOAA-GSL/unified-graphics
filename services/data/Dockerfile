FROM public.ecr.aws/lambda/python:3.9

RUN pip3 install --no-cache-dir poetry

COPY pyproject.toml .
COPY poetry.lock .

RUN poetry export --format requirements.txt --without dev --without-hashes --output requirements.txt \
    && pip install --target "${LAMBDA_TASK_ROOT}" --requirement requirements.txt

COPY src/ugdata/ "${LAMBDA_TASK_ROOT}/ugdata"

CMD ["ugdata.aws.lambda_handler"]
