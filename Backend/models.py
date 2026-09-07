from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    DateTime
)

from database import Base


class GPSRecord(Base):

    __tablename__ = "gps_records"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    latitude = Column(
        Float,
        nullable=False
    )

    longitude = Column(
        Float,
        nullable=False
    )

    speed = Column(
        Float,
        nullable=True
    )

    road_type = Column(
        String,
        nullable=True
    )

    confidence = Column(
        Float,
        nullable=True
    )

    road_name = Column(
        String,
        nullable=True
    )

    highway_class = Column(
        String,
        nullable=True
    )

    road_length = Column(
        Float,
        nullable=True
    )

    lanes = Column(
        Float,
        nullable=True
    )

    max_speed = Column(
        Float,
        nullable=True
    )

    road_width = Column(
        Float,
        nullable=True
    )

    curvature = Column(
        Float,
        nullable=True
    )

    timestamp = Column(
        DateTime,
        default=datetime.utcnow
    )