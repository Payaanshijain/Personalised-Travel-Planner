from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import APP_NAME, FRONTEND_URL
from app.routers import health, trips

app = FastAPI(
    title=APP_NAME,
    description="Personalized Travel Itinerary Planner Backend with Groq AI & Route Optimization",
    version="1.0.0",
)

# Configure CORS to allow frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(trips.router)


@app.get("/")
def read_root():
    return {
        "app": APP_NAME,
        "version": "1.0.0",
        "message": "FastAPI backend is running. Visit /health, /api/trips, or /docs.",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "trips": "/api/trips/",
        }
    }
