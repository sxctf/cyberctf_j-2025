# !TODO: is this image ok? has some cves on it
FROM python:3.11-slim

WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY . .

RUN useradd -ms /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

RUN uv sync --frozen --no-cache

EXPOSE 2000

ENV FLASK_ENV=production

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 CMD curl -f http://localhost:2000/ || exit 1

CMD ["uv", "run", "python", "app.py"]