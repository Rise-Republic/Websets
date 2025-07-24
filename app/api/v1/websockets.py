from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional
from loguru import logger

from app.websockets import get_websocket_manager, get_progress_tracker, ConnectionType
from app.auth.dependencies import get_current_user_optional

router = APIRouter(prefix="/ws", tags=["v1-websockets"])


@router.websocket("/jobs/{job_id}")
async def websocket_job_updates(
    websocket: WebSocket,
    job_id: str,
    token: Optional[str] = Query(None)
):
    """WebSocket endpoint for job-specific updates."""
    manager = get_websocket_manager()
    
    # Extract user from token if provided
    user_id = None
    if token:
        # Simple token extraction - in production, verify JWT properly
        try:
            from app.auth.jwt_handler import verify_token
            email = verify_token(token)
            if email:
                from app.database import SessionLocal
                from app.models.user import User
                db = SessionLocal()
                try:
                    user = db.query(User).filter(User.email == email).first()
                    if user:
                        user_id = str(user.id)
                finally:
                    db.close()
        except Exception as e:
            logger.warning(f"Failed to authenticate WebSocket connection: {e}")
    
    try:
        # Connect to WebSocket manager
        connection_id = await manager.connect(websocket, user_id, ConnectionType.JOB_UPDATES)
        
        # Subscribe to job-specific topic
        job_topic = f"job_{job_id}"
        await manager.subscribe_to_topic(connection_id, job_topic)
        
        # If authenticated, also subscribe to user's jobs
        if user_id:
            user_topic = f"user_jobs_{user_id}"
            await manager.subscribe_to_topic(connection_id, user_topic)
        
        # Send current job state if available
        progress_tracker = get_progress_tracker()
        current_state = progress_tracker.get_job_state(job_id)
        if current_state:
            await manager.send_to_connection(connection_id, {
                "job_id": job_id,
                "current_state": current_state
            }, "current_state")
        
        # Handle the connection lifecycle
        await manager.handle_websocket(websocket, ConnectionType.JOB_UPDATES, user_id)
        
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for job: {job_id}")
    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {e}")


@router.websocket("/user")
async def websocket_user_updates(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """WebSocket endpoint for user-specific updates."""
    manager = get_websocket_manager()
    
    # Authentication is required for user-specific updates
    user_id = None
    if token:
        try:
            from app.auth.jwt_handler import verify_token
            email = verify_token(token)
            if email:
                from app.database import SessionLocal
                from app.models.user import User
                db = SessionLocal()
                try:
                    user = db.query(User).filter(User.email == email).first()
                    if user:
                        user_id = str(user.id)
                finally:
                    db.close()
        except Exception as e:
            logger.warning(f"Failed to authenticate user WebSocket: {e}")
    
    if not user_id:
        await websocket.close(code=4001, reason="Authentication required")
        return
    
    try:
        # Connect to WebSocket manager
        connection_id = await manager.connect(websocket, user_id, ConnectionType.JOB_UPDATES)
        
        # Subscribe to user's job topic
        user_topic = f"user_jobs_{user_id}"
        await manager.subscribe_to_topic(connection_id, user_topic)
        
        # Send current states of user's jobs
        progress_tracker = get_progress_tracker()
        all_states = progress_tracker.get_all_job_states()
        user_job_states = {}
        
        # Filter jobs that belong to this user (basic filtering)
        # In production, you'd want to query the database for user's jobs
        for job_id, state in all_states.items():
            if state.get("user_id") == user_id:
                user_job_states[job_id] = state
        
        if user_job_states:
            await manager.send_to_connection(connection_id, {
                "user_job_states": user_job_states
            }, "user_states")
        
        # Handle the connection lifecycle
        await manager.handle_websocket(websocket, ConnectionType.JOB_UPDATES, user_id)
        
    except WebSocketDisconnect:
        logger.info(f"User WebSocket disconnected: {user_id}")
    except Exception as e:
        logger.error(f"User WebSocket error for {user_id}: {e}")


@router.websocket("/system")
async def websocket_system_updates(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """WebSocket endpoint for system status updates."""
    manager = get_websocket_manager()
    
    # Optional authentication for system updates
    user_id = None
    if token:
        try:
            from app.auth.jwt_handler import verify_token
            email = verify_token(token)
            if email:
                from app.database import SessionLocal
                from app.models.user import User
                db = SessionLocal()
                try:
                    user = db.query(User).filter(User.email == email).first()
                    if user:
                        user_id = str(user.id)
                finally:
                    db.close()
        except Exception:
            pass  # Anonymous connections allowed for system status
    
    try:
        # Connect to WebSocket manager
        connection_id = await manager.connect(websocket, user_id, ConnectionType.SYSTEM_STATUS)
        
        # Subscribe to system status topic
        await manager.subscribe_to_topic(connection_id, "system_status")
        await manager.subscribe_to_topic(connection_id, "health_check")
        
        # Send current system stats
        system_stats = manager.get_connection_stats()
        await manager.send_to_connection(connection_id, {
            "system_stats": system_stats
        }, "system_status")
        
        # Handle the connection lifecycle
        await manager.handle_websocket(websocket, ConnectionType.SYSTEM_STATUS, user_id)
        
    except WebSocketDisconnect:
        logger.info(f"System WebSocket disconnected")
    except Exception as e:
        logger.error(f"System WebSocket error: {e}")


@router.websocket("/general")
async def websocket_general(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """General purpose WebSocket endpoint."""
    manager = get_websocket_manager()
    
    # Optional authentication
    user_id = None
    if token:
        try:
            from app.auth.jwt_handler import verify_token
            email = verify_token(token)
            if email:
                from app.database import SessionLocal
                from app.models.user import User
                db = SessionLocal()
                try:
                    user = db.query(User).filter(User.email == email).first()
                    if user:
                        user_id = str(user.id)
                finally:
                    db.close()
        except Exception:
            pass  # Anonymous connections allowed
    
    try:
        # Handle the connection lifecycle
        await manager.handle_websocket(websocket, ConnectionType.GENERAL, user_id)
        
    except WebSocketDisconnect:
        logger.info(f"General WebSocket disconnected")
    except Exception as e:
        logger.error(f"General WebSocket error: {e}")


# REST endpoints for WebSocket management
@router.get("/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics."""
    manager = get_websocket_manager()
    return manager.get_connection_stats()


@router.get("/topics")
async def get_active_topics():
    """Get list of active WebSocket topics."""
    manager = get_websocket_manager()
    return {"topics": manager.get_topics()}


@router.post("/broadcast")
async def broadcast_message(
    message: dict,
    topic: Optional[str] = None
):
    """Broadcast a message to WebSocket connections."""
    manager = get_websocket_manager()
    
    if topic:
        sent_count = await manager.broadcast_to_topic(topic, message, "admin_broadcast")
    else:
        sent_count = await manager.broadcast_to_all(message, "admin_broadcast")
    
    return {"message": "Broadcast sent", "recipients": sent_count}
