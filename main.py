# main.py
# Entry point for the Evidence AI FastAPI application.
# Run it with: uvicorn main:app --reload
# (or "python main.py", which reads the PORT environment variable for
# hosting platforms that assign one automatically)

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config import STATIC_DIR
from database import init_db
from routers import investigation, pages


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Make sure the SQLite database and its tables exist before serving requests."""
    init_db()
    yield


app = FastAPI(
    title="Evidence AI",
    description="AI-powered Corporate Investigation & Evidence Analysis Platform (MVP)",
    version="0.1.0",
    lifespan=lifespan,
)

# Serve everything in static/ (CSS, JS) at the /static URL path.
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# All page routes (/ and /demo-case) are defined in routers/pages.py.
app.include_router(pages.router)

# The investigation engine endpoints (/run-investigation, /analyze-custom-case)
# are defined in routers/investigation.py.
app.include_router(investigation.router)


@app.get("/health")
def health_check():
    """Simple health check for deployment platforms to confirm the app is running."""
    return {"status": "ok"}


if __name__ == "__main__":
    # Lets the app be started with "python main.py" on hosting platforms that
    # assign a port via the PORT environment variable (e.g. Render, Railway).
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
