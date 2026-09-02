from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from datetime import datetime

from database import Base


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)

    customer_name = Column(String, nullable=True)

    language = Column(String, nullable=True)

    state = Column(String, nullable=True)
    city = Column(String, nullable=True)
    area = Column(String, nullable=True)
    pincode = Column(String, nullable=True)

    intent = Column(String, nullable=True)

    priority = Column(String, default="MEDIUM")

    confidence = Column(Float, nullable=True)

    status = Column(String, default="ACTIVE")

    summary = Column(Text, nullable=True)

    escalation_reason = Column(Text, nullable=True)

    recommended_action = Column(Text, nullable=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )