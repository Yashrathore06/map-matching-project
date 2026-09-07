from datetime import datetime

from fastapi import (
    FastAPI,
    Depends,
    HTTPException
)

from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

from sqlalchemy.orm import Session

from database import (
    Base,
    engine,
    get_db
)

from models import GPSRecord

from map_matching import (
    get_nearest_road
)

from ml_model import (
    predict_road_type
)


app = FastAPI(
    title="AI Map Matching API",
    version="1.0"
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]
)


# --------------------------------------------------
# Database
# --------------------------------------------------

Base.metadata.create_all(
    bind=engine
)


# --------------------------------------------------
# Request Model
# --------------------------------------------------

class GPSData(BaseModel):

    latitude: float

    longitude: float

    speed: float | None = None


# --------------------------------------------------
# Home
# --------------------------------------------------

@app.get("/")
def home():

    return {
        "message": "AI Map Matching Backend is running"
    }


# --------------------------------------------------
# Health Check
# --------------------------------------------------

@app.get("/health")
def health():

    return {
        "status": "online",
        "database": "configured",
        "ml_model": "loaded"
    }


# --------------------------------------------------
# GPS Endpoint
# --------------------------------------------------

@app.post("/gps")
def receive_gps(
    data: GPSData,
    db: Session = Depends(get_db)
):

    try:

        # ------------------------------------------
        # 1. Find nearest OSM road
        # ------------------------------------------

        road = get_nearest_road(
            data.latitude,
            data.longitude
        )

        if road is None:

            raise HTTPException(
                status_code=404,
                detail="No nearby road found"
            )


        # ------------------------------------------
        # 2. AI/ML prediction
        # ------------------------------------------

        ml_result = predict_road_type(

            road["road_length"],

            road["lanes"],

            road["max_speed"],

            road["road_width"],

            road["curvature"]
        )


        # ------------------------------------------
        # 3. Final road classification
        # ------------------------------------------

        osm_type = road["road_type"]

        ml_prediction = ml_result["road_type"]

        confidence = ml_result["confidence"]


        # Local roads are outside the current
        # Random Forest training classes.
        if osm_type == "local_road":

            final_road_type = "local_road"

            final_confidence = 1.0

        else:

            final_road_type = ml_prediction

            final_confidence = confidence


        # ------------------------------------------
        # 4. Save GPS + result in PostgreSQL
        # ------------------------------------------

        record = GPSRecord(

            latitude=data.latitude,

            longitude=data.longitude,

            speed=data.speed,

            road_type=final_road_type,

            confidence=final_confidence,

            road_name=road["road_name"],

            highway_class=road["highway_class"],

            road_length=road["road_length"],

            lanes=road["lanes"],

            max_speed=road["max_speed"],

            road_width=road["road_width"],

            curvature=road["curvature"],

            timestamp=datetime.utcnow()
        )


        db.add(record)

        db.commit()

        db.refresh(record)


        # ------------------------------------------
        # 5. Response
        # ------------------------------------------

        return {

            "message": "GPS processed successfully",

            "record_id": record.id,

            "latitude": data.latitude,

            "longitude": data.longitude,

            "speed": data.speed,

            "road": {

                "name": road["road_name"],

                "highway_class":
                    road["highway_class"],

                "distance":
                    round(
                        road["distance"],
                        2
                    ),

                "length":
                    round(
                        road["road_length"],
                        2
                    ),

                "lanes":
                    road["lanes"],

                "max_speed":
                    road["max_speed"],

                "width":
                    round(
                        road["road_width"],
                        2
                    ),

                "curvature":
                    road["curvature"]
            },

            "ml": {

                "prediction":
                    ml_prediction,

                "confidence":
                    round(
                        confidence,
                        4
                    )
            },

            "final_classification":
                final_road_type,

            "final_confidence":
                round(
                    final_confidence,
                    4
                )
        }


    except HTTPException:

        raise


    except Exception as error:

        db.rollback()

        print(
            "GPS Processing Error:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )