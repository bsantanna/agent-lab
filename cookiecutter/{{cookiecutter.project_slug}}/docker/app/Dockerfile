FROM python:3.12-slim

ENV SERVICE_NAME="{{ cookiecutter.project_name }}"
ENV SERVICE_VERSION=0.1.0
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8000
ENV WORKERS=1

WORKDIR /app

# If you add a WebAgentBase-derived agent (web crawling / voice transcription),
# add the ffmpeg static-binary COPY layer back — see agent-lab's own Dockerfile.
COPY pyproject.toml uv.lock /app/
RUN --mount=from=ghcr.io/astral-sh/uv:latest,source=/uv,target=/bin/uv \
    uv sync --no-build --frozen --no-dev --no-install-project \
    && rm -rf /tmp/* /var/tmp/* \
    && groupadd -r app && useradd -r -g app -d /app app \
    && chown -R app:app /app

USER app
COPY {{ cookiecutter.package_name }} /app/{{ cookiecutter.package_name }}/
COPY config-docker.yml /app/

CMD ["/bin/bash", "-c", "/app/.venv/bin/python -m uvicorn {{ cookiecutter.package_name }}.main:app --host ${HOST} --port ${PORT} --workers ${WORKERS}"]
