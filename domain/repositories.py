from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Iterable, List, Optional

from .entities import Alert, Server, AlertException


class AlertRepository(ABC):
    @abstractmethod
    def save_alerts(self, alerts: Iterable[Alert]) -> int:
        """Save multiple alerts and return count of saved alerts."""
        pass

    @abstractmethod
    def list_alerts(self, 
                   server_name: Optional[str] = None,
                   acknowledged: Optional[bool] = None,
                   limit: Optional[int] = None) -> List[Alert]:
        """List alerts with optional filtering."""
        pass

    @abstractmethod
    def acknowledge_alert(self, alert_id: int, acknowledged_by: str) -> bool:
        """Acknowledge an alert."""
        pass

    @abstractmethod
    def acknowledge_alerts_by_rule(self, rule: str, acknowledged_by: str) -> int:
        """Acknowledge all alerts matching a rule."""
        pass


class StateRepository(ABC):
    @abstractmethod
    def get_last_seen_timestamp(self, server_name: str, log_source: str) -> Optional[str]:
        """Get last seen timestamp for a server/log source combination."""
        pass

    @abstractmethod
    def set_last_seen_timestamp(self, server_name: str, log_source: str, timestamp: str) -> None:
        """Set last seen timestamp for a server/log source combination."""
        pass


class ServerRepository(ABC):
    @abstractmethod
    def save_server(self, server: Server) -> bool:
        """Save or update a server."""
        pass

    @abstractmethod
    def get_server(self, name: str) -> Optional[Server]:
        """Get server by name."""
        pass

    @abstractmethod
    def list_servers(self) -> List[Server]:
        """List all servers."""
        pass

    @abstractmethod
    def delete_server(self, name: str) -> bool:
        """Delete server by name."""
        pass


class AlertExceptionRepository(ABC):
    @abstractmethod
    def save_exception(self, exception: AlertException) -> bool:
        """Save or update an alert exception."""
        pass

    @abstractmethod
    def list_exceptions(self) -> List[AlertException]:
        """List all alert exceptions."""
        pass

    @abstractmethod
    def get_exception(self, exception_id: int) -> Optional[AlertException]:
        """Get exception by ID."""
        pass

    @abstractmethod
    def update_exception(self, exception: AlertException) -> bool:
        """Update an existing exception."""
        pass

    @abstractmethod
    def delete_exception(self, exception_id: int) -> bool:
        """Delete exception by ID."""
        pass

    @abstractmethod
    def is_alert_excepted(self, alert: Alert) -> bool:
        """Check if an alert should be excepted based on current rules."""
        pass
