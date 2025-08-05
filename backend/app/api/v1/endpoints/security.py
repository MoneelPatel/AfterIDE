"""
AfterIDE - Security API Endpoints

REST API endpoints for security monitoring and management.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from app.core.database import get_db
from app.services.security_monitor import security_monitor, SecurityEvent, SecurityEventType, SecurityLevel
from app.services.auth import AuthService
from app.api.v1.endpoints.auth import get_current_user_dependency
from app.models.user import User

router = APIRouter()


@router.get("/stats")
async def get_security_stats(
    current_user: User = Depends(get_current_user_dependency),
    db = Depends(get_db)
):
    """
    Get security statistics and monitoring data.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dict containing security statistics
    """
    try:
        # Only allow admin users to access security stats
        if current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Admin privileges required."
            )
        
        stats = security_monitor.get_security_stats()
        
        return {
            "success": True,
            "data": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve security statistics"
        )


@router.get("/user/{user_id}/profile")
async def get_user_security_profile(
    user_id: str,
    current_user: User = Depends(get_current_user_dependency),
    db = Depends(get_db)
):
    """
    Get security profile for a specific user.
    
    Args:
        user_id: User ID to get profile for
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dict containing user security profile
    """
    try:
        # Only allow admin users or the user themselves to access profiles
        if current_user.role.value != "admin" and str(current_user.id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only view your own security profile."
            )
        
        profile = security_monitor.get_user_security_profile(user_id)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User security profile not found"
            )
        
        return {
            "success": True,
            "data": profile,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user security profile"
        )


@router.get("/events")
async def get_security_events(
    event_type: Optional[str] = None,
    level: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user_dependency),
    db = Depends(get_db)
):
    """
    Get security events with optional filtering.
    
    Args:
        event_type: Filter by event type
        level: Filter by security level
        user_id: Filter by user ID
        limit: Maximum number of events to return
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of security events
    """
    try:
        # Only allow admin users to access security events
        if current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Admin privileges required."
            )
        
        # Get events from monitor
        events = list(security_monitor.events)
        
        # Apply filters
        if event_type:
            try:
                event_type_enum = SecurityEventType(event_type)
                events = [e for e in events if e.event_type == event_type_enum]
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid event type: {event_type}"
                )
        
        if level:
            try:
                level_enum = SecurityLevel(level)
                events = [e for e in events if e.level == level_enum]
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid security level: {level}"
                )
        
        if user_id:
            events = [e for e in events if e.user_id == user_id]
        
        # Limit results
        events = events[-limit:] if limit > 0 else events
        
        # Convert to dict format
        event_data = [event.to_dict() for event in events]
        
        return {
            "success": True,
            "data": {
                "events": event_data,
                "total_count": len(event_data),
                "filters_applied": {
                    "event_type": event_type,
                    "level": level,
                    "user_id": user_id,
                    "limit": limit
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve security events"
        )


@router.get("/alerts")
async def get_security_alerts(
    current_user: User = Depends(get_current_user_dependency),
    db = Depends(get_db)
):
    """
    Get security alert configurations and status.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dict containing alert configurations
    """
    try:
        # Only allow admin users to access security alerts
        if current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Admin privileges required."
            )
        
        alerts_data = []
        for alert_id, alert in security_monitor.alerts.items():
            alerts_data.append({
                "alert_id": alert.alert_id,
                "name": alert.name,
                "description": alert.description,
                "level": alert.level.value,
                "enabled": alert.enabled,
                "threshold": alert.threshold,
                "time_window": alert.time_window,
                "triggered_count": alert.triggered_count,
                "last_triggered": alert.last_triggered.isoformat() if alert.last_triggered else None
            })
        
        return {
            "success": True,
            "data": {
                "alerts": alerts_data,
                "total_alerts": len(alerts_data),
                "active_alerts": sum(1 for alert in alerts_data if alert["enabled"])
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve security alerts"
        )


@router.post("/alerts/{alert_id}/toggle")
async def toggle_security_alert(
    alert_id: str,
    enabled: bool,
    current_user: User = Depends(get_current_user_dependency),
    db = Depends(get_db)
):
    """
    Enable or disable a security alert.
    
    Args:
        alert_id: Alert ID to toggle
        enabled: Whether to enable or disable the alert
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dict containing updated alert status
    """
    try:
        # Only allow admin users to modify security alerts
        if current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Admin privileges required."
            )
        
        if alert_id not in security_monitor.alerts:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert '{alert_id}' not found"
            )
        
        alert = security_monitor.alerts[alert_id]
        alert.enabled = enabled
        
        return {
            "success": True,
            "data": {
                "alert_id": alert_id,
                "enabled": alert.enabled,
                "message": f"Alert '{alert_id}' {'enabled' if enabled else 'disabled'}"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle security alert"
        )


@router.get("/my-profile")
async def get_my_security_profile(
    current_user: User = Depends(get_current_user_dependency),
    db = Depends(get_db)
):
    """
    Get current user's security profile.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dict containing user's security profile
    """
    try:
        user_id = str(current_user.id)
        profile = security_monitor.get_user_security_profile(user_id)
        
        if not profile:
            # Create empty profile if none exists
            profile = {
                'user_id': user_id,
                'event_count': 0,
                'suspicious_score': 0,
                'last_activity': datetime.utcnow().isoformat(),
                'recent_events': []
            }
        
        return {
            "success": True,
            "data": profile,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve security profile"
        )


@router.get("/health")
async def get_security_health(
    current_user: User = Depends(get_current_user_dependency),
    db = Depends(get_db)
):
    """
    Get security system health status.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dict containing security system health
    """
    try:
        # Basic health check - accessible to all authenticated users
        stats = security_monitor.get_security_stats()
        
        # Determine overall security health
        critical_events = stats.get('security_levels', {}).get('critical', 0)
        high_events = stats.get('security_levels', {}).get('high', 0)
        
        if critical_events > 0:
            health_status = "critical"
        elif high_events > 5:
            health_status = "warning"
        else:
            health_status = "healthy"
        
        return {
            "success": True,
            "data": {
                "status": health_status,
                "critical_events": critical_events,
                "high_events": high_events,
                "total_events_24h": stats.get('events_last_24_hours', 0),
                "active_users": stats.get('active_users', 0),
                "alerts_triggered": stats.get('alerts_triggered', 0)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve security health status"
        ) 