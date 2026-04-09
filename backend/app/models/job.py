from sqlalchemy import Column, Integer, String, JSON
from app.core.db import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    status = Column(String, default="queued")
    result = Column(JSON, nullable=True)