from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GPSData(BaseModel):
    latitude: float
    longitude: float
    speed: float | None = None


@app.get("/")
def home():
    return {"message": "GPS Backend is running"}


@app.post("/gps")
def receive_gps(data: GPSData):
    print("GPS Received:", data)

    return {
        "message": "GPS data received successfully",
        "latitude": data.latitude,
        "longitude": data.longitude,
        "speed": data.speed
    }