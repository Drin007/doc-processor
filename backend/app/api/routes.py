from fastapi import APIRouter, UploadFile, Depends
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.job import Job
from app.workers.tasks import process_document

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ Upload
@router.post("/upload")
def upload(file: UploadFile, db: Session = Depends(get_db)):
    job = Job(filename=file.filename, status="queued")
    db.add(job)
    db.commit()
    db.refresh(job)

    process_document.delay(job.id)

    return {"job_id": job.id}

# ✅ Get all jobs (FIXED - includes result)
@router.get("/jobs")
def get_jobs(db: Session = Depends(get_db)):
    jobs = db.query(Job).all()

    return [
        {
            "id": job.id,
            "filename": job.filename,
            "status": job.status,
            "result": job.result  # ✅ IMPORTANT
        }
        for job in jobs
    ]

# ✅ Get single job
@router.get("/jobs/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        return {"error": "Job not found"}

    return {
        "id": job.id,
        "filename": job.filename,
        "status": job.status,
        "result": job.result
    }

# ✅ Retry
@router.post("/jobs/{job_id}/retry")
def retry_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        return {"error": "Job not found"}

    job.status = "queued"
    job.result = None
    db.commit()

    process_document.delay(job.id)

    return {"message": "Retry started"}