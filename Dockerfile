FROM python:3.12-slim

ENV SERVICE_NAME=Agent-Lab
ENV SERVICE_VERSION=1.0.0
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8000
ENV WORKERS=3
ENV BROWSER_USE_VERSION=0.1.48
ENV PLAYWRIGHT_BROWSERS_PATH=/agent-lab/.cache

WORKDIR /agent-lab

COPY requirements.txt /agent-lab/

RUN apt update -q && apt install -yq xvfb ffmpeg \
    && apt clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir browser-use==${BROWSER_USE_VERSION} \
    && pip install --no-cache-dir -r requirements.txt

RUN playwright install chromium --with-deps --no-shell \
    && apt clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN groupadd -r agent-lab \
    && useradd -r -g agent-lab -d /agent-lab agent-lab \
    && chown -R agent-lab:agent-lab /agent-lab

USER agent-lab
COPY app/ /agent-lab/app/
COPY config-docker.yml /agent-lab/

CMD ["/bin/bash", "-x", "-c", "python -m uvicorn app.main:app --host ${HOST} --port ${PORT} --workers ${WORKERS}"]
