
FROM python:3.11-slim

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    tsduck \
    ca-certificates \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app/app
COPY web/static /app/web/static
COPY configs /app/configs
RUN mkdir -p /app/out/hls /app/out/vtt /app/media

EXPOSE 8080
CMD ["python","-m","app.main"]
