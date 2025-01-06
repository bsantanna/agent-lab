FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8000

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir --upgrade pip \
    &&  pip install --no-cache-dir -r requirements.txt

CMD ["/bin/bash", "-c", "python -m uvicorn app.main:app --host ${HOST} --port ${PORT}"]
