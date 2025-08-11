from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Iterable, List, Optional

from .entities import Alert, Server


class AlertRepository(ABC):
    @abstractmethod
    def save_alerts(self, alerts: Iterable[Alert]) -> int:
        raise NotImplementedError

    @abstractmethod
    def list_alerts(self, limit: int = 200, since: Optional[datetime] = None, acknowledged: Optional[bool] = None) -> List[Alert]:
        raise NotImplementedError

    @abstractmethod
    def acknowledge_alert(self, alert_id: int, acknowledged_by: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def acknowledge_alerts_by_rule(self, rule: str, acknowledged_by: str) -> int:
        raise NotImplementedError


class StateRepository(ABC):
    @abstractmethod
    def get_last_seen_timestamp(self, server_name: str, log_path: str) -> Optional[datetime]:
        raise NotImplementedError

    @abstractmethod
    def set_last_seen_timestamp(self, server_name: str, log_path: str, ts: datetime) -> None:
        raise NotImplementedError


class ServerRepository(ABC):
    @abstractmethod
    def list_servers(self) -> List[Server]:
        raise NotImplementedError

    @abstractmethod
    def upsert_server(self, server: Server) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete_server(self, name: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_server(self, name: str) -> Optional[Server]:
        raise NotImplementedError
