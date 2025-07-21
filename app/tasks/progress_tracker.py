"""
Job progress tracking with real-time WebSocket updates.
"""
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio
from loguru import logger

from app.database import SessionLocal
from app.models import Job, JobStatus
from app.websockets.manager import WebSocketManager, WebSocketMessage


class JobProgressTracker:
    """Tracks job progress and sends real-time updates via WebSocket."""
    
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.websocket_manager = WebSocketManager()
        self.db = SessionLocal()
    
    async def update_status(self, status: JobStatus, message: str = None):
        """Update job status and notify via WebSocket."""
        try:
            job = self.db.query(Job).filter(Job.id == self.job_id).first()
            if job:
                old_status = job.status
                job.status = status
                if message:
                    job.logs = (job.logs or "") + f"\n{datetime.utcnow().isoformat()}: {message}"
                self.db.commit()
                
                # Send WebSocket update
                await self._send_update({
                    "type": "status_change",
                    "job_id": str(self.job_id),
                    "old_status": old_status.value,
                    "new_status": status.value,
                    "message": message,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                logger.info(f"Job {self.job_id} status updated: {old_status.value} -> {status.value}")
                
        except Exception as e:
            logger.error(f"Failed to update job status: {e}")
            self.db.rollback()
    
    async def update_progress(self, phase: str, progress: int, details: Dict[str, Any] = None):
        """Update job progress and notify via WebSocket."""
        try:
            job = self.db.query(Job).filter(Job.id == self.job_id).first()
            if job:
                # Update progress fields based on phase
                if phase == "crawling":
                    job.crawled_urls = details.get("completed", 0)
                    job.total_urls = details.get("total", 0)
                elif phase == "extraction":
                    job.extracted_records = details.get("extracted", 0)
                
                self.db.commit()
                
                # Send WebSocket update
                await self._send_update({
                    "type": "progress_update",
                    "job_id": str(self.job_id),
                    "phase": phase,
                    "progress": progress,
                    "details": details or {},
                    "timestamp": datetime.utcnow().isoformat()
                })
                
        except Exception as e:
            logger.error(f"Failed to update job progress: {e}")
            self.db.rollback()
    
    async def add_log(self, level: str, message: str, details: Dict[str, Any] = None):
        """Add log entry and notify via WebSocket."""
        try:
            job = self.db.query(Job).filter(Job.id == self.job_id).first()
            if job:
                log_entry = f"\n{datetime.utcnow().isoformat()} [{level.upper()}] {message}"
                job.logs = (job.logs or "") + log_entry
                self.db.commit()
                
                # Send WebSocket update
                await self._send_update({
                    "type": "log",
                    "job_id": str(self.job_id),
                    "level": level,
                    "message": message,
                    "details": details or {},
                    "timestamp": datetime.utcnow().isoformat()
                })
                
        except Exception as e:
            logger.error(f"Failed to add job log: {e}")
            self.db.rollback()
    
    async def report_error(self, error: str, details: Dict[str, Any] = None):
        """Report error and update job status."""
        await self.update_status(JobStatus.FAILED, f"Error: {error}")
        await self.add_log("error", error, details)
    
    async def complete_job(self, summary: Dict[str, Any] = None):
        """Mark job as completed."""
        try:
            job = self.db.query(Job).filter(Job.id == self.job_id).first()
            if job:
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.utcnow()
                
                completion_message = f"Job completed successfully. "
                if summary:
                    completion_message += f"Summary: {summary}"
                
                job.logs = (job.logs or "") + f"\n{datetime.utcnow().isoformat()}: {completion_message}"
                self.db.commit()
                
                # Send final update
                await self._send_update({
                    "type": "job_completed",
                    "job_id": str(self.job_id),
                    "summary": summary or {},
                    "timestamp": datetime.utcnow().isoformat()
                })
                
        except Exception as e:
            logger.error(f"Failed to complete job: {e}")
            self.db.rollback()
    
    async def _send_update(self, data: Dict[str, Any]):
        """Send update via WebSocket."""
        try:
            message = WebSocketMessage(
                type="job_update",
                data=data
            )
            
            # Send to job-specific channel
            await self.websocket_manager.broadcast_to_channel(
                f"job_{self.job_id}",
                message
            )
            
            # Also send to user's jobs channel
            job = self.db.query(Job).filter(Job.id == self.job_id).first()
            if job and job.user_id:
                await self.websocket_manager.broadcast_to_channel(
                    f"user_{job.user_id}_jobs",
                    message
                )
                
        except Exception as e:
            logger.error(f"Failed to send WebSocket update: {e}")
    
    def __del__(self):
        """Cleanup database session."""
        if hasattr(self, 'db'):
            self.db.close()


class ProgressContext:
    """Context manager for tracking progress within phases."""
    
    def __init__(self, job_id: str, phase: str, total_steps: int = 100):
        self.job_id = job_id
        self.phase = phase
        self.total_steps = total_steps
        self.current_step = 0
        self.tracker = JobProgressTracker(job_id)
    
    async def __aenter__(self):
        await self.tracker.update_status(
            JobStatus[self.phase.upper()],
            f"Starting {self.phase} phase"
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.tracker.report_error(
                str(exc_val),
                {"phase": self.phase, "step": self.current_step}
            )
    
    async def update_step(self, step: int, details: Dict[str, Any] = None):
        """Update current step and calculate progress."""
        self.current_step = step
        progress = int((step / max(self.total_steps, 1)) * 100)
        await self.tracker.update_progress(self.phase, progress, details)
    
    async def increment(self, details: Dict[str, Any] = None):
        """Increment step by 1."""
        self.current_step += 1
        await self.update_step(self.current_step, details)
    
    async def log(self, message: str, level: str = "info", details: Dict[str, Any] = None):
        """Add log entry."""
        await self.tracker.add_log(level, message, details)
