FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml alembic.ini ./
RUN pip install --no-cache-dir .
COPY app ./app
COPY migrations ./migrations
COPY docker ./docker
ENV PYTHONPATH=/app
RUN chmod +x /app/docker/entrypoint.sh
CMD ["/app/docker/entrypoint.sh"]

