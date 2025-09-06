from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from enum import Enum
from loguru import logger

from .manager import get_websocket_manager


class ProgressEventType(str, Enum):
    JOB_STARTED = "job_started"
    JOB_PROGRESS = "job_progress"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    JOB_CANCELLED = "job_cancelled"
    
    # Crawling events
    CRAWL_STARTED = "crawl_started"
    CRAWL_PROGRESS = "crawl_progress"
    CRAWL_COMPLETED = "crawl_completed"
    CRAWL_ERROR = "crawl_error"
    
    # Processing events
    PROCESSING_STARTED = "processing_started"
    PROCESSING_PROGRESS = "processing_progress"
    PROCESSING_COMPLETED = "processing_completed"
    
    # System events
    SYSTEM_STATUS = "system_status"
    HEALTH_CHECK = "health_check"


class ProgressEvent(BaseModel):
    """Represents a progress event."""
    
    event_type: ProgressEventType
    job_id: str
    user_id: Optional[str] = None
    progress_percentage: Optional[float] = None
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: str = None
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.utcnow().isoformat()
        super().__init__(**data)
    
    def to_websocket_data(self) -> Dict[str, Any]:
        """Convert to WebSocket message data."""
        return {
            "event_type": self.event_type,
            "job_id": self.job_id,
            "user_id": self.user_id,
            "progress_percentage": self.progress_percentage,
            "message": self.message,
            "details": self.details or {},
            "timestamp": self.timestamp
        }


class JobProgressTracker:
    """Tracks and broadcasts job progress events."""
    
    def __init__(self):
        self.websocket_manager = get_websocket_manager()
        self.job_states: Dict[str, Dict[str, Any]] = {}  # job_id -> state
    
    def get_topic_for_job(self, job_id: str) -> str:
        """Get the WebSocket topic for a job."""
        return f"job_{job_id}"
    
    def get_topic_for_user(self, user_id: str) -> str:
        """Get the WebSocket topic for a user's jobs."""
        return f"user_jobs_{user_id}"
    
    async def emit_event(self, event: ProgressEvent):
        """Emit a progress event to WebSocket subscribers."""
        try:
            # Update job state
            self.job_states[event.job_id] = {
                "event_type": event.event_type,
                "progress_percentage": event.progress_percentage,
                "message": event.message,
                "timestamp": event.timestamp,
                "details": event.details
            }
            
            # Prepare data for WebSocket
            websocket_data = event.to_websocket_data()
            
            # Broadcast to job-specific topic
            job_topic = self.get_topic_for_job(event.job_id)
            await self.websocket_manager.broadcast_to_topic(
                job_topic, 
                websocket_data, 
                "job_progress"
            )
            
            # Broadcast to user-specific topic if user_id provided
            if event.user_id:
                user_topic = self.get_topic_for_user(event.user_id)
                await self.websocket_manager.broadcast_to_topic(
                    user_topic,
                    websocket_data,
                    "job_progress"
                )
                
                # Also send directly to user's connections
                await self.websocket_manager.send_to_user(
                    event.user_id,
                    websocket_data,
                    "job_progress"
                )
            
            logger.debug(f"Emitted progress event: {event.event_type} for job {event.job_id}")
            
        except Exception as e:
            logger.error(f"Failed to emit progress event: {e}")
    
    async def start_job(self, job_id: str, user_id: str = None, message: str = None):
        """Emit job started event."""
        event = ProgressEvent(
            event_type=ProgressEventType.JOB_STARTED,
            job_id=job_id,
            user_id=user_id,
            progress_percentage=0.0,
            message=message or f"Job {job_id} started"
        )
        await self.emit_event(event)
    
    async def update_progress(self, job_id: str, progress: float, message: str, user_id: str = None, details: Dict[str, Any] = None):
        """Update job progress."""
        event = ProgressEvent(
            event_type=ProgressEventType.JOB_PROGRESS,
            job_id=job_id,
            user_id=user_id,
            progress_percentage=min(100.0, max(0.0, progress)),
            message=message,
            details=details
        )
        await self.emit_event(event)
    
    async def complete_job(self, job_id: str, user_id: str = None, message: str = None, details: Dict[str, Any] = None):
        """Emit job completed event."""
        event = ProgressEvent(
            event_type=ProgressEventType.JOB_COMPLETED,
            job_id=job_id,
            user_id=user_id,
            progress_percentage=100.0,
            message=message or f"Job {job_id} completed successfully",
            details=details
        )
        await self.emit_event(event)
    
    async def fail_job(self, job_id: str, error_message: str, user_id: str = None, details: Dict[str, Any] = None):
        """Emit job failed event."""
        event = ProgressEvent(
            event_type=ProgressEventType.JOB_FAILED,
            job_id=job_id,
            user_id=user_id,
            message=error_message,
            details=details
        )
        await self.emit_event(event)
    
    async def cancel_job(self, job_id: str, user_id: str = None, message: str = None):
        """Emit job cancelled event."""
        event = ProgressEvent(
            event_type=ProgressEventType.JOB_CANCELLED,
            job_id=job_id,
            user_id=user_id,
            message=message or f"Job {job_id} was cancelled"
        )
        await self.emit_event(event)
    
    async def crawl_started(self, job_id: str, url_count: int, user_id: str = None):
        """Emit crawl started event."""
        event = ProgressEvent(
            event_type=ProgressEventType.CRAWL_STARTED,
            job_id=job_id,
            user_id=user_id,
            message=f"Started crawling {url_count} URLs",
            details={"url_count": url_count}
        )
        await self.emit_event(event)
    
    async def crawl_progress(self, job_id: str, completed_urls: int, total_urls: int, current_url: str = None, user_id: str = None):
        """Emit crawl progress event."""
        progress = (completed_urls / total_urls * 100) if total_urls > 0 else 0
        message = f"Crawled {completed_urls}/{total_urls} URLs"
        if current_url:
            message += f" (current: {current_url})"
        
        event = ProgressEvent(
            event_type=ProgressEventType.CRAWL_PROGRESS,
            job_id=job_id,
            user_id=user_id,
            progress_percentage=progress,
            message=message,
            details={
                "completed_urls": completed_urls,
                "total_urls": total_urls,
                "current_url": current_url
            }
        )
        await self.emit_event(event)
    
    async def crawl_completed(self, job_id: str, successful_count: int, failed_count: int, user_id: str = None):
        """Emit crawl completed event."""
        event = ProgressEvent(
            event_type=ProgressEventType.CRAWL_COMPLETED,
            job_id=job_id,
            user_id=user_id,
            message=f"Crawling completed: {successful_count} successful, {failed_count} failed",
            details={
                "successful_count": successful_count,
                "failed_count": failed_count,
                "total_count": successful_count + failed_count
            }
        )
        await self.emit_event(event)
    
    async def processing_started(self, job_id: str, message: str, user_id: str = None):
        """Emit processing started event."""
        event = ProgressEvent(
            event_type=ProgressEventType.PROCESSING_STARTED,
            job_id=job_id,
            user_id=user_id,
            message=message
        )
        await self.emit_event(event)
    
    async def processing_progress(self, job_id: str, progress: float, message: str, user_id: str = None, details: Dict[str, Any] = None):
        """Emit processing progress event."""
        event = ProgressEvent(
            event_type=ProgressEventType.PROCESSING_PROGRESS,
            job_id=job_id,
            user_id=user_id,
            progress_percentage=progress,
            message=message,
            details=details
        )
        await self.emit_event(event)
    
    async def processing_completed(self, job_id: str, message: str, user_id: str = None, details: Dict[str, Any] = None):
        """Emit processing completed event."""
        event = ProgressEvent(
            event_type=ProgressEventType.PROCESSING_COMPLETED,
            job_id=job_id,
            user_id=user_id,
            message=message,
            details=details
        )
        await self.emit_event(event)
    
    def get_job_state(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get current state of a job."""
        return self.job_states.get(job_id)
    
    def get_all_job_states(self) -> Dict[str, Dict[str, Any]]:
        """Get states of all tracked jobs."""
        return self.job_states.copy()
    
    def cleanup_job_state(self, job_id: str):
        """Clean up job state after completion."""
        self.job_states.pop(job_id, None)


# Global progress tracker instance
_progress_tracker = None

def get_progress_tracker() -> JobProgressTracker:
    """Get the global progress tracker instance."""
    global _progress_tracker
    if _progress_tracker is None:
        _progress_tracker = JobProgressTracker()
    return _progress_tracker
