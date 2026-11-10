import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from langserve import add_routes

from assistant import make_chat_chain


BASE_DIR = Path(__file__).resolve().parent
local_env = BASE_DIR / ".env"
if not local_env.exists():
    local_env = BASE_DIR.parent / ".env"
load_dotenv(local_env)

# LangServe prints box-drawing characters while starting; keep Windows consoles
# from failing when their active code page cannot display them.
if os.name == "nt":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


app = FastAPI(title="India Weather & Movies Assistant")
app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)
add_routes(app, make_chat_chain(), path="/agent", playground_type="default")


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8765"))
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=port)
