"""Kilnify FastAPI application — carbon accounting for cement industries."""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import companies, dashboard, emissions, factors, production, reports
from .database import Base, engine

# Create tables on startup (dev convenience; use migrations for production).
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Kilnify API",
    description="Carbon accounting tool for cement manufacturing companies (Scope 1, 2, 3).",
    version="1.0.0",
)

_cors_origins = os.getenv(
    "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(companies.router)
app.include_router(production.router)
app.include_router(emissions.router)
app.include_router(reports.router)
app.include_router(factors.router)
app.include_router(dashboard.router)


@app.get("/")
def health():
    return {"status": "ok", "service": "kilnify", "version": "1.0.0"}
