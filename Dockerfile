FROM python:3.12-slim

ENV SERVICE_NAME=Agent-Lab
ENV SERVICE_VERSION=1.4.5
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8000
ENV WORKERS=1

WORKDIR /agent-lab

COPY requirements.txt /agent-lab/
RUN apt update -q && apt install -yq ffmpeg build-essential \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && apt clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && groupadd -r agent-lab \
    && useradd -r -g agent-lab -d /agent-lab agent-lab \
    && chown -R agent-lab:agent-lab /agent-lab

USER agent-lab
COPY app/ /agent-lab/app/
COPY config-docker.yml /agent-lab/

CMD ["/bin/bash", "-x", "-c", "python -m uvicorn app.main:app --host ${HOST} --port ${PORT} --workers ${WORKERS}"]
