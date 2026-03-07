"""CLI script for checking job status."""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from packages.core.config import settings
from packages.core.logging import setup_logging
from packages.db.session import SessionLocal
from packages.db.models import ProcessingJob, ProcessingStageLog
import logging

setup_logging(settings.log_level)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Check job status')
    parser.add_argument('job_id', help='Job ID to check')

    args = parser.parse_args()
    db = SessionLocal()

    try:
        # Get job
        job = db.query(ProcessingJob).filter(
            ProcessingJob.job_id == args.job_id
        ).first()

        if not job:
            print(f"Job not found: {args.job_id}")
            sys.exit(1)

        print(f"\nJob Status:")
        print(f"  Job ID: {job.job_id}")
        print(f"  Type: {job.job_type}")
        print(f"  Status: {job.status}")
        print(f"  Target Doc: {job.target_doc_id or 'N/A'}")
        print(f"  Started: {job.started_at}")
        print(f"  Completed: {job.completed_at or 'In progress'}")

        if job.error_message:
            print(f"  Error: {job.error_message}")

        # Get stages
        stages = db.query(ProcessingStageLog).filter(
            ProcessingStageLog.job_id == args.job_id
        ).order_by(ProcessingStageLog.created_at).all()

        if stages:
            print(f"\nStages ({len(stages)}):")
            for stage in stages:
                status_icon = "✓" if stage.status == "success" else "✗" if stage.status == "failed" else "⋯"
                print(f"  {status_icon} {stage.stage_name}: {stage.status}")
                if stage.doc_id:
                    print(f"    Doc: {stage.doc_id}")
                if stage.elapsed_ms:
                    print(f"    Time: {stage.elapsed_ms}ms")
                if stage.error_message:
                    print(f"    Error: {stage.error_message}")

    finally:
        db.close()


if __name__ == '__main__':
    main()
