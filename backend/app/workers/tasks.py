from celery_worker import celery
from app.core.db import SessionLocal
from app.models.job import Job
import redis
import time

r = redis.Redis(host="localhost", port=6379, db=0)

@celery.task(bind=True)
def process_document(self, job_id):
    db = SessionLocal()
    job = None

    try:
        job = db.query(Job).filter(Job.id == job_id).first()

        if not job:
            print(f"Job {job_id} not found")
            return

        job.status = "processing"
        job.result = {"progress": 0, "step": "starting"}
        db.commit()

        steps = [
            ("parsing document", 25),
            ("extracting data", 50),
            ("analyzing content", 75),
            ("finalizing", 100),
        ]

        for step, progress in steps:
            job.result = {
                "progress": progress,
                "step": step
            }
            db.commit()

            # ✅ send progress
            r.publish("job_updates", f"{job_id}:{progress}:{step}")

            time.sleep(1)

        job.status = "completed"
        job.result = {
            "title": "Sample Doc",
            "summary": "Processed successfully",
            "progress": 100
        }
        db.commit()

    except Exception as e:
        if job:
            job.status = "failed"
            job.result = {"error": str(e)}
            db.commit()

    finally:
        db.close()