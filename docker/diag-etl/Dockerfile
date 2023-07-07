FROM public.ecr.aws/lambda/python:3.10

RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel \
    && pip3 install --no-cache-dir poetry

RUN yum -y --setopt=tsflags=nodocs update && yum -y clean all && rm -rf rm -rf /var/cache

COPY pyproject.toml .
COPY poetry.lock .

RUN poetry export --format requirements.txt --without dev --without-hashes --output requirements.txt \
    && pip install --target "${LAMBDA_TASK_ROOT}" --requirement requirements.txt

COPY src/unified_graphics/ "${LAMBDA_TASK_ROOT}/unified_graphics"

CMD ["unified_graphics.etl.aws.lambda_handler"]
