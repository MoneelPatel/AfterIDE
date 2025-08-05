"""
AfterIDE - Security Monitoring Service

Tracks security events, generates alerts, and provides security analytics.
"""

import time
import json
import structlog
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio

logger = structlog.get_logger(__name__)


class SecurityEventType(Enum):
    """Types of security events."""
    LOGIN_FAILED = "login_failed"
    LOGIN_SUCCESS = "login_success"
    ACCOUNT_LOCKED = "account_locked"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    COMMAND_BLOCKED = "command_blocked"
    INJECTION_ATTEMPT = "injection_attempt"
    PATH_TRAVERSAL = "path_traversal"
    RESOURCE_LIMIT_EXCEEDED = "resource_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    SESSION_EXPIRED = "session_expired"
    TOKEN_INVALID = "token_invalid"
    FILE_ACCESS_VIOLATION = "file_access_violation"


class SecurityLevel(Enum):
    """Security event severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityEvent:
    """Security event data structure."""
    event_type: SecurityEventType
    level: SecurityLevel
    timestamp: datetime
    user_id: Optional[str]
    session_id: Optional[str]
    ip_address: Optional[str]
    details: Dict[str, Any]
    source: str
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            **asdict(self),
            'event_type': self.event_type.value,
            'level': self.level.value,
            'timestamp': self.timestamp.isoformat()
        }


class SecurityAlert:
    """Security alert configuration and management."""
    
    def __init__(self, alert_id: str, name: str, description: str, level: SecurityLevel):
        self.alert_id = alert_id
        self.name = name
        self.description = description
        self.level = level
        self.enabled = True
        self.threshold = 1
        self.time_window = 300  # 5 minutes
        self.triggered_count = 0
        self.last_triggered = None
    
    def should_trigger(self, event_count: int) -> bool:
        """Check if alert should be triggered."""
        if not self.enabled:
            return False
        
        return event_count >= self.threshold
    
    def trigger(self):
        """Mark alert as triggered."""
        self.triggered_count += 1
        self.last_triggered = datetime.utcnow()


class SecurityMonitor:
    """Main security monitoring service."""
    
    def __init__(self):
        self.events: deque = deque(maxlen=10000)  # Keep last 10k events
        self.alerts: Dict[str, SecurityAlert] = {}
        self.event_counters: Dict[str, int] = defaultdict(int)
        self.user_activity: Dict[str, Dict[str, Any]] = {}
        self.ip_activity: Dict[str, Dict[str, Any]] = {}
        self.session_activity: Dict[str, Dict[str, Any]] = {}
        
        # Initialize default alerts
        self._initialize_default_alerts()
        
        # Start monitoring tasks
        self.monitoring_task = None
        self.alert_task = None
    
    def _initialize_default_alerts(self):
        """Initialize default security alerts."""
        default_alerts = [
            SecurityAlert(
                "login_failed_threshold",
                "Multiple Failed Login Attempts",
                "Multiple failed login attempts detected",
                SecurityLevel.MEDIUM
            ),
            SecurityAlert(
                "rate_limit_exceeded",
                "Rate Limit Exceeded",
                "API rate limit exceeded",
                SecurityLevel.LOW
            ),
            SecurityAlert(
                "command_blocked",
                "Blocked Commands",
                "Dangerous commands blocked",
                SecurityLevel.HIGH
            ),
            SecurityAlert(
                "injection_attempt",
                "Injection Attempt",
                "SQL or command injection attempt detected",
                SecurityLevel.CRITICAL
            ),
            SecurityAlert(
                "suspicious_activity",
                "Suspicious Activity",
                "Unusual user activity detected",
                SecurityLevel.MEDIUM
            )
        ]
        
        for alert in default_alerts:
            self.alerts[alert.alert_id] = alert
    
    async def start_monitoring(self):
        """Start security monitoring tasks."""
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.alert_task = asyncio.create_task(self._alert_loop())
        
        logger.info("Security monitoring started")
    
    async def stop_monitoring(self):
        """Stop security monitoring tasks."""
        if self.monitoring_task:
            self.monitoring_task.cancel()
        if self.alert_task:
            self.alert_task.cancel()
        
        logger.info("Security monitoring stopped")
    
    def record_event(self, event: SecurityEvent):
        """Record a security event."""
        # Add event to queue
        self.events.append(event)
        
        # Update counters
        event_key = f"{event.event_type.value}_{event.user_id or 'anonymous'}_{event.ip_address or 'unknown'}"
        self.event_counters[event_key] += 1
        
        # Update activity tracking
        self._update_activity_tracking(event)
        
        # Log event
        logger.info(
            "Security event recorded",
            event_type=event.event_type.value,
            level=event.level.value,
            user_id=event.user_id,
            ip_address=event.ip_address,
            details=event.details
        )
    
    def _update_activity_tracking(self, event: SecurityEvent):
        """Update activity tracking for users, IPs, and sessions."""
        # User activity
        if event.user_id:
            if event.user_id not in self.user_activity:
                self.user_activity[event.user_id] = {
                    'events': [],
                    'last_activity': event.timestamp,
                    'event_count': 0,
                    'suspicious_score': 0
                }
            
            user_data = self.user_activity[event.user_id]
            user_data['events'].append(event)
            user_data['last_activity'] = event.timestamp
            user_data['event_count'] += 1
            
            # Keep only last 100 events per user
            if len(user_data['events']) > 100:
                user_data['events'] = user_data['events'][-100:]
        
        # IP activity
        if event.ip_address:
            if event.ip_address not in self.ip_activity:
                self.ip_activity[event.ip_address] = {
                    'events': [],
                    'last_activity': event.timestamp,
                    'event_count': 0,
                    'suspicious_score': 0
                }
            
            ip_data = self.ip_activity[event.ip_address]
            ip_data['events'].append(event)
            ip_data['last_activity'] = event.timestamp
            ip_data['event_count'] += 1
            
            # Keep only last 100 events per IP
            if len(ip_data['events']) > 100:
                ip_data['events'] = ip_data['events'][-100:]
        
        # Session activity
        if event.session_id:
            if event.session_id not in self.session_activity:
                self.session_activity[event.session_id] = {
                    'events': [],
                    'last_activity': event.timestamp,
                    'event_count': 0
                }
            
            session_data = self.session_activity[event.session_id]
            session_data['events'].append(event)
            session_data['last_activity'] = event.timestamp
            session_data['event_count'] += 1
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while True:
            try:
                # Analyze recent events for patterns
                await self._analyze_events()
                
                # Clean up old data
                await self._cleanup_old_data()
                
                # Wait before next iteration
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in monitoring loop", error=str(e))
                await asyncio.sleep(60)
    
    async def _alert_loop(self):
        """Alert processing loop."""
        while True:
            try:
                # Process alerts
                await self._process_alerts()
                
                # Wait before next iteration
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in alert loop", error=str(e))
                await asyncio.sleep(30)
    
    async def _analyze_events(self):
        """Analyze events for suspicious patterns."""
        current_time = datetime.utcnow()
        recent_events = [
            event for event in self.events
            if (current_time - event.timestamp).total_seconds() < 300  # Last 5 minutes
        ]
        
        # Analyze patterns
        await self._detect_brute_force_attempts(recent_events)
        await self._detect_suspicious_activity(recent_events)
        await self._detect_anomalous_behavior(recent_events)
    
    async def _detect_brute_force_attempts(self, events: List[SecurityEvent]):
        """Detect brute force login attempts."""
        failed_logins = [
            event for event in events
            if event.event_type == SecurityEventType.LOGIN_FAILED
        ]
        
        # Group by user and IP
        login_attempts = defaultdict(list)
        for event in failed_logins:
            key = f"{event.user_id or 'unknown'}_{event.ip_address or 'unknown'}"
            login_attempts[key].append(event)
        
        # Check for brute force patterns
        for key, attempts in login_attempts.items():
            if len(attempts) >= 5:  # 5 failed attempts in 5 minutes
                # Create alert event
                alert_event = SecurityEvent(
                    event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                    level=SecurityLevel.HIGH,
                    timestamp=datetime.utcnow(),
                    user_id=attempts[0].user_id,
                    session_id=None,
                    ip_address=attempts[0].ip_address,
                    details={
                        'pattern': 'brute_force_attempt',
                        'attempt_count': len(attempts),
                        'time_window': '5 minutes'
                    },
                    source='security_monitor'
                )
                
                self.record_event(alert_event)
    
    async def _detect_suspicious_activity(self, events: List[SecurityEvent]):
        """Detect suspicious activity patterns."""
        # Check for rapid command execution
        command_events = [
            event for event in events
            if event.event_type in [SecurityEventType.COMMAND_BLOCKED, SecurityEventType.INJECTION_ATTEMPT]
        ]
        
        if len(command_events) >= 10:  # 10 suspicious commands in 5 minutes
            alert_event = SecurityEvent(
                event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                level=SecurityLevel.MEDIUM,
                timestamp=datetime.utcnow(),
                user_id=command_events[0].user_id,
                session_id=command_events[0].session_id,
                ip_address=command_events[0].ip_address,
                details={
                    'pattern': 'rapid_suspicious_commands',
                    'command_count': len(command_events),
                    'time_window': '5 minutes'
                },
                source='security_monitor'
            )
            
            self.record_event(alert_event)
    
    async def _detect_anomalous_behavior(self, events: List[SecurityEvent]):
        """Detect anomalous user behavior."""
        # Check for unusual activity patterns
        for user_id, user_data in self.user_activity.items():
            recent_user_events = [
                event for event in user_data['events']
                if (datetime.utcnow() - event.timestamp).total_seconds() < 3600  # Last hour
            ]
            
            # Calculate suspicious score
            suspicious_score = 0
            for event in recent_user_events:
                if event.level == SecurityLevel.CRITICAL:
                    suspicious_score += 10
                elif event.level == SecurityLevel.HIGH:
                    suspicious_score += 5
                elif event.level == SecurityLevel.MEDIUM:
                    suspicious_score += 2
                elif event.level == SecurityLevel.LOW:
                    suspicious_score += 1
            
            user_data['suspicious_score'] = suspicious_score
            
            # Alert if score is too high
            if suspicious_score >= 20:
                alert_event = SecurityEvent(
                    event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                    level=SecurityLevel.HIGH,
                    timestamp=datetime.utcnow(),
                    user_id=user_id,
                    session_id=None,
                    ip_address=None,
                    details={
                        'pattern': 'high_suspicious_score',
                        'score': suspicious_score,
                        'time_window': '1 hour'
                    },
                    source='security_monitor'
                )
                
                self.record_event(alert_event)
    
    async def _process_alerts(self):
        """Process and trigger alerts."""
        current_time = datetime.utcnow()
        
        for alert_id, alert in self.alerts.items():
            if not alert.enabled:
                continue
            
            # Count recent events for this alert type
            recent_events = [
                event for event in self.events
                if (current_time - event.timestamp).total_seconds() < alert.time_window
                and self._matches_alert_pattern(event, alert_id)
            ]
            
            # Check if alert should be triggered
            if alert.should_trigger(len(recent_events)) and not alert.last_triggered:
                alert.trigger()
                await self._send_alert(alert, recent_events)
    
    def _matches_alert_pattern(self, event: SecurityEvent, alert_id: str) -> bool:
        """Check if event matches alert pattern."""
        if alert_id == "login_failed_threshold":
            return event.event_type == SecurityEventType.LOGIN_FAILED
        elif alert_id == "rate_limit_exceeded":
            return event.event_type == SecurityEventType.RATE_LIMIT_EXCEEDED
        elif alert_id == "command_blocked":
            return event.event_type == SecurityEventType.COMMAND_BLOCKED
        elif alert_id == "injection_attempt":
            return event.event_type == SecurityEventType.INJECTION_ATTEMPT
        elif alert_id == "suspicious_activity":
            return event.event_type == SecurityEventType.SUSPICIOUS_ACTIVITY
        
        return False
    
    async def _send_alert(self, alert: SecurityAlert, events: List[SecurityEvent]):
        """Send security alert."""
        alert_data = {
            'alert_id': alert.alert_id,
            'name': alert.name,
            'description': alert.description,
            'level': alert.level.value,
            'timestamp': datetime.utcnow().isoformat(),
            'event_count': len(events),
            'events': [event.to_dict() for event in events[-5:]]  # Last 5 events
        }
        
        # Log alert
        logger.warning(
            "Security alert triggered",
            alert_id=alert.alert_id,
            name=alert.name,
            level=alert.level.value,
            event_count=len(events)
        )
        
        # In a production environment, you would send this to:
        # - Email notifications
        # - Slack/Discord webhooks
        # - Security information and event management (SIEM) systems
        # - Incident response systems
        
        # For now, we'll just log it
        logger.info("Security alert data", alert_data=alert_data)
    
    async def _cleanup_old_data(self):
        """Clean up old monitoring data."""
        current_time = datetime.utcnow()
        cutoff_time = current_time - timedelta(hours=24)  # Keep 24 hours of data
        
        # Clean up old events
        self.events = deque(
            [event for event in self.events if event.timestamp > cutoff_time],
            maxlen=10000
        )
        
        # Clean up old activity data
        for user_id in list(self.user_activity.keys()):
            if self.user_activity[user_id]['last_activity'] < cutoff_time:
                del self.user_activity[user_id]
        
        for ip_address in list(self.ip_activity.keys()):
            if self.ip_activity[ip_address]['last_activity'] < cutoff_time:
                del self.ip_activity[ip_address]
        
        for session_id in list(self.session_activity.keys()):
            if self.session_activity[session_id]['last_activity'] < cutoff_time:
                del self.session_activity[session_id]
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics."""
        current_time = datetime.utcnow()
        last_hour = current_time - timedelta(hours=1)
        last_24_hours = current_time - timedelta(hours=24)
        
        # Count events by type and time period
        hourly_events = [e for e in self.events if e.timestamp > last_hour]
        daily_events = [e for e in self.events if e.timestamp > last_24_hours]
        
        stats = {
            'total_events': len(self.events),
            'events_last_hour': len(hourly_events),
            'events_last_24_hours': len(daily_events),
            'active_users': len(self.user_activity),
            'active_sessions': len(self.session_activity),
            'unique_ips': len(self.ip_activity),
            'alerts_triggered': sum(1 for alert in self.alerts.values() if alert.last_triggered),
            'event_types': defaultdict(int),
            'security_levels': defaultdict(int)
        }
        
        # Count by event type and security level
        for event in daily_events:
            stats['event_types'][event.event_type.value] += 1
            stats['security_levels'][event.level.value] += 1
        
        return dict(stats)
    
    def get_user_security_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get security profile for a specific user."""
        if user_id not in self.user_activity:
            return None
        
        user_data = self.user_activity[user_id]
        
        return {
            'user_id': user_id,
            'event_count': user_data['event_count'],
            'suspicious_score': user_data['suspicious_score'],
            'last_activity': user_data['last_activity'].isoformat(),
            'recent_events': [event.to_dict() for event in user_data['events'][-10:]]
        }


# Global security monitor instance
security_monitor = SecurityMonitor() 