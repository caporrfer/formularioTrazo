FROM python:3.12-alpine

WORKDIR /app
COPY backend/server.py /app/server.py
COPY content /app/content

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=6 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)" || exit 1

CMD ["python", "/app/server.py"]
