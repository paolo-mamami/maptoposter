"""
SQLite database module for job tracking.
"""
import os
import json
from datetime import datetime
from typing import Optional, List
from contextlib import contextmanager

from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database configuration
DB_DIR = os.environ.get("DB_DIR", "data")
os.makedirs(DB_DIR, exist_ok=True)
DATABASE_URL = f"sqlite:///{os.path.join(DB_DIR, 'jobs.db')}"

# SQLAlchemy setup
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Job(Base):
    """Job model for poster generation tracking."""
    __tablename__ = "jobs"
    
    job_id = Column(String, primary_key=True, index=True)
    status = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    completed_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)
    poster_path = Column(String, nullable=True)
    request_data = Column(Text, nullable=False)
    
    def to_dict(self):
        """Convert job to dictionary."""
        return {
            "job_id": self.job_id,
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "error": self.error,
            "poster_path": self.poster_path,
            "request_data": json.loads(self.request_data) if self.request_data else {},
        }


# Create tables
Base.metadata.create_all(bind=engine)


@contextmanager
def get_db():
    """Get database session context manager."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_job_db(job_id: str, request_data: dict) -> Job:
    """Create a new job in the database."""
    with get_db() as db:
        job = Job(
            job_id=job_id,
            status="pending",
            created_at=datetime.now(),
            request_data=json.dumps(request_data),
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job


def get_job_db(job_id: str) -> Optional[Job]:
    """Get a job by ID."""
    with get_db() as db:
        return db.query(Job).filter(Job.job_id == job_id).first()


def update_job_status_db(job_id: str, status: str, **kwargs) -> Optional[Job]:
    """Update job status and other fields."""
    with get_db() as db:
        job = db.query(Job).filter(Job.job_id == job_id).first()
        if job:
            job.status = status
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)
            db.commit()
            db.refresh(job)
            return job
        return None


def get_all_jobs_db(limit: int = 100, status: Optional[str] = None) -> List[Job]:
    """Get all jobs, optionally filtered by status."""
    with get_db() as db:
        query = db.query(Job)
        if status:
            query = query.filter(Job.status == status)
        return query.order_by(Job.created_at.desc()).limit(limit).all()


def delete_old_jobs_db(days: int = 7) -> int:
    """Delete jobs older than specified days."""
    from datetime import timedelta
    
    cutoff_date = datetime.now() - timedelta(days=days)
    with get_db() as db:
        deleted = db.query(Job).filter(Job.created_at < cutoff_date).delete()
        db.commit()
        return deleted
