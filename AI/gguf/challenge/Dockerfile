# База
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Системные зависимости: билд C++ и BLAS
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      cmake \
      git \
      libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

# Непривилегированный пользователь и каталоги
RUN useradd -ms /bin/bash ctf
WORKDIR /app
RUN mkdir -p /app/uploads && chown -R ctf:ctf /app

RUN echo 'flag{gguf_1s_n0t_d3ad}' > /flag.txt
RUN chown ctf:ctf /flag.txt && chmod 0400 /flag.txt

# Зависимости приложения
COPY challenge/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r /app/requirements.txt

# Код приложения
COPY challenge/app.py /app/app.py
COPY challenge/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Переменные окружения
ENV MAX_UPLOAD_MB=50 \
    UPLOAD_DIR=/app/uploads \
    LLM_N_CTX=2048 \
    LLM_THREADS=2 \
    LLM_N_PREDICT=32

# Непривилегированный пользователь
USER ctf

# Порт
EXPOSE 8000

# Старт
ENTRYPOINT ["/app/entrypoint.sh"]
