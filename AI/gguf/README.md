# CTF GGUF (веб-вариант)

Мини-сервис, который принимает файл `.gguf`, пытается загрузить его через `llama-cpp-python`, а затем даёт сделать маленький инференс.

## Быстрый старт (локально)

```bash
docker compose -f infra/docker-compose.yml build
docker compose -f infra/docker-compose.yml up
# Открыть http://localhost:8000

