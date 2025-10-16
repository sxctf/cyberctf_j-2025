import os
import pathlib
import shutil
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

# llama-cpp-python
try:
    from llama_cpp import Llama
    from llama_cpp import llama_chat_format
except Exception:
    Llama = None
    llama_chat_format = None

app = FastAPI(title="Ohmama")

# CORS (не обязательно)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Конфиги через ENV
MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", "100"))
UPLOAD_DIR = pathlib.Path(os.environ.get("UPLOAD_DIR", "/app/uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

N_CTX = int(os.environ.get("LLM_N_CTX", "2048"))
N_THREADS = int(os.environ.get("LLM_THREADS", "2"))
N_PREDICT = int(os.environ.get("LLM_N_PREDICT", "32"))

# Глобальное состояние
CURRENT_MODEL_PATH: Optional[pathlib.Path] = None
CURRENT_MODEL: Optional["Llama"] = None


def _reset_model() -> None:
    global CURRENT_MODEL, CURRENT_MODEL_PATH
    CURRENT_MODEL = None
    CURRENT_MODEL_PATH = None


def _load_model(path: pathlib.Path) -> str:
    """
    Загружаем модель и, если в её метаданных есть tokenizer.chat_template,
    принудительно назначаем Jinja2 chat handler, чтобы рендер шел через Jinja.
    """
    if Llama is None:
        raise RuntimeError("llama-cpp-python не установлен/не инициализирован")

    if not path.exists():
        raise FileNotFoundError(f"Файл не найден: {path}")

    # 1) Инициализация модели (verbose=True, чтобы в логах увидеть выбор формата)
    model = Llama(
        model_path=str(path),
        n_ctx=N_CTX,
        n_threads=N_THREADS,
        verbose=True,
    )

    # 2) Пробуем вытащить шаблон из метаданных уже загруженной модели
    template: Optional[str] = None
    try:
        meta = getattr(model, "metadata", {}) or {}
        # основные варианты ключа
        for key in ("tokenizer.chat_template", "chat_template"):
            val = meta.get(key)
            if isinstance(val, str) and val.strip():
                template = val
                break
    except Exception:
        template = None  # безопасный фолбэк

    # 3) Если шаблон есть — форсируем Jinja2-обработчик
    if template and llama_chat_format is not None:
        try:
            j2 = llama_chat_format.Jinja2ChatFormatter(
                template=template, bos_token="", eos_token=""
            ).to_chat_handler()
            # Назначаем поверх любого "угаданного" формата
            model.chat_handler = j2  # type: ignore[attr-defined]
        except Exception as e:
            # Не падаем — просто продолжаем без форса
            print(
                f"[WARN] Не удалось установить Jinja chat handler: {type(e).__name__}: {e}"
            )

    # 4) Сохраняем глобально
    global CURRENT_MODEL, CURRENT_MODEL_PATH
    CURRENT_MODEL = model
    CURRENT_MODEL_PATH = path
    return "ok"


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <title>CTF GGUF Loader</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 760px; margin: 40px auto; padding: 0 12px; }}
    header {{ margin-bottom: 16px; }}
    .card {{ border: 1px solid #ddd; border-radius: 12px; padding: 16px; margin: 12px 0; }}
    button {{ padding: 8px 14px; border-radius: 10px; border: 1px solid #888; cursor: pointer; }}
    input[type=file] {{ padding: 8px; }}
    code {{ background: #f6f6f6; padding: 2px 6px; border-radius: 6px; }}
  </style>
</head>
<body>
  <header>
    <h1>CTF GGUF Loader</h1>
    <p>Загрузите файл <code>.gguf</code>, затем нажмите «Тест инференса».(используйте файлы <50 MB)</p>
  </header>

  <section class="card">
    <h3>1) Загрузить GGUF</h3>
    <form id="uploadForm">
      <input type="file" name="file" accept=".gguf" required>
      <button type="submit">Загрузить</button>
    </form>
    <pre id="uploadOut"></pre>
  </section>

  <section class="card">
    <h3>2) Тест инференса</h3>
    <form id="inferForm">
      <label>Промпт:
        <input type="text" name="prompt" value="Hey, how are you doing?" style="width:100%; padding:8px; margin-top:6px">
      </label>
      <div style="margin-top:10px">
        <button type="submit">Выполнить</button>
      </div>
    </form>
    <pre id="inferOut"></pre>
  </section>

<script>
const upForm = document.getElementById('uploadForm');
upForm.addEventListener('submit', async (e) => {{
  e.preventDefault();
  const fd = new FormData(upForm);
  const res = await fetch('/upload', {{ method: 'POST', body: fd }});
  const txt = await res.text();
  document.getElementById('uploadOut').textContent = txt;
}});

const infForm = document.getElementById('inferForm');
infForm.addEventListener('submit', async (e) => {{
  e.preventDefault();
  const fd = new FormData(infForm);
  const res = await fetch('/infer', {{ method: 'POST', body: fd }});
  const txt = await res.text();
  document.getElementById('inferOut').textContent = txt;
}});
</script>
</body>
</html>
"""


from fastapi import Request, HTTPException, UploadFile, File

@app.post("/upload", response_class=PlainTextResponse)
async def upload(request: Request, file: UploadFile = File(...)) -> str:
    filename = pathlib.Path(file.filename or "model.gguf")
    if filename.suffix.lower() != ".gguf":
        raise HTTPException(status_code=400, detail="Ожидается файл .gguf")

    max_bytes = MAX_UPLOAD_MB * 1024 * 1024
    cl = request.headers.get("content-length")
    if cl is not None and int(cl) > max_bytes:
        raise HTTPException(status_code=413, detail="Файл слишком большой")

    tmp_path = UPLOAD_DIR / ("upload_" + filename.name)
    size = 0
    try:
        with tmp_path.open("wb") as out:
            while True:
                chunk = await file.read(1024 * 1024)  # 1 МБ
                if not chunk:
                    break
                size += len(chunk)
                if size > max_bytes:
                    raise HTTPException(status_code=413, detail="Файл слишком большой")
                out.write(chunk)
    except:
        # чтобы не оставлять обрезанные файлы
        try:
            tmp_path.unlink()
        except FileNotFoundError:
            pass
        raise
    finally:
        await file.close()

    # дальше — как у тебя: переносим во final_path, сбрасываем модель и т.д.


    final_path = UPLOAD_DIR / filename.name
    if final_path.exists():
        final_path.unlink()
    shutil.move(str(tmp_path), final_path)

    _reset_model()
    try:
        _load_model(final_path)
    except Exception as e:
        return f"[LOAD:ERROR] {type(e).__name__}: {e}"
    return f"[LOAD:OK] Файл сохранён как {final_path} ({size} байт). Модель инициализирована."


@app.post("/infer", response_class=PlainTextResponse)
async def infer(prompt: str = Form("Hello!")) -> str:
    if CURRENT_MODEL is None:
        raise HTTPException(
            status_code=400, detail="Сначала загрузите GGUF через /upload"
        )

    try:
        out = CURRENT_MODEL.create_chat_completion(  # type: ignore[operator]
            messages=[
                {"role": "system", "content": "You are a concise assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            top_p=0.9,
            max_tokens=N_PREDICT,
        )
        msg = out.get("choices", [{}])[0].get("message", {}).get("content", "")
        if msg:
            return f"[INFER:OK]\n{msg}".strip()

        # fallback: text completion
        out2 = CURRENT_MODEL(prompt=prompt, max_tokens=N_PREDICT, temperature=0.2, top_p=0.9)  # type: ignore[operator]
        text = out2.get("choices", [{}])[0].get("text", "")
        return f"[INFER:FALLBACK]\n{text}".strip()
    except Exception as e:
        return f"[INFER:ERROR] {type(e).__name__}: {e}"


@app.get("/healthz", response_class=PlainTextResponse)
async def healthz() -> str:
    status = "ready" if CURRENT_MODEL is not None else "idle"
    return f"ok:{status}"


@app.exception_handler(HTTPException)
async def http_exc_handler(request: Request, exc: HTTPException):
    return PlainTextResponse(str(exc.detail), status_code=exc.status_code)


@app.get("/about", response_class=JSONResponse)
async def about():
    # Пытаемся достать версию пакета (если доступна)
    llama_ver = None
    try:
        from importlib.metadata import version as _v  # py3.8+: stdlib

        llama_ver = _v("llama-cpp-python")
    except Exception:
        pass

    return {
        "service": "CTF GGUF Loader",
        "max_upload_mb": MAX_UPLOAD_MB,
        "upload_dir": str(UPLOAD_DIR),
        "n_ctx": N_CTX,
        "n_threads": N_THREADS,
        "n_predict": N_PREDICT,
        "model_path": str(CURRENT_MODEL_PATH) if CURRENT_MODEL_PATH else None,
        "llama_cpp_python": llama_ver,
    }


@app.get("/meta", response_class=JSONResponse)
async def meta():
    if CURRENT_MODEL is None:
        return {"error": "no model loaded"}
    meta = getattr(CURRENT_MODEL, "metadata", {}) or {}
    tpl = meta.get("tokenizer.chat_template") or meta.get("chat_template")
    return {
        "has_tokenizer_chat_template": "tokenizer.chat_template" in meta,
        "has_chat_template": "chat_template" in meta,
        "template_preview": (
            (tpl[:200] + "...") if isinstance(tpl, str) and len(tpl) > 200 else tpl
        ),
    }
