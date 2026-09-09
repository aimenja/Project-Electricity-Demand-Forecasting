from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .model import PowerPlusEngine

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI(title="PowerPlus Dashboard API")
engine = PowerPlusEngine()


class ForecastRequest(BaseModel):
    city: str
    house: str
    start_date: date
    horizon: int = Field(default=7, ge=1, le=30)
    overrides: dict[str, float | str | None] = Field(default_factory=dict)
    include_sensitivity: bool = True


@app.get("/api/meta")
def meta():
    return {
        "cities": engine.cities(),
        "houses_by_city": {c: engine.houses(c) for c in engine.cities()},
        "default": engine.default_selection(),
        "model": engine.model_info(),
        "profile_model": engine.profile_model_info(),
    }


@app.get("/api/house/{city}/{house}")
def house(city: str, house: str):
    try:
        return engine.house_profile(city, house)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/api/forecast")
def forecast(req: ForecastRequest):
    overrides = {k: v for k, v in req.overrides.items() if v is not None and v != ""}
    try:
        daily = engine.forecast(req.city, req.house, req.start_date, req.horizon, overrides)
        sensitivity = (
            engine.sensitivity(req.city, req.house, req.start_date, overrides)
            if req.include_sensitivity else []
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    total = sum(d["kwh"] for d in daily)
    return {
        "daily": daily,
        "total_kwh": round(total, 4),
        "average_kwh": round(total / len(daily), 4) if daily else 0.0,
        "peak_day": max(daily, key=lambda d: d["kwh"]) if daily else None,
        "sensitivity": sensitivity,
    }


@app.get("/")
def index():
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/", StaticFiles(directory=FRONTEND_DIR), name="static")
