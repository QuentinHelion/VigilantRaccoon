from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class Alert:
    id: Optional[int] = None
    server_name: str = ""
    log_source: str = ""
    rule: str = ""
    level: str = "medium"
    message: str = ""
    ip_address: Optional[str] = None
    username: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None


@dataclass
class Server:
    id: Optional[int] = None
    name: str = ""
    host: str = ""
    port: int = 22
    username: str = ""
    password: Optional[str] = None
    private_key_path: Optional[str] = None
    logs: List[str] = field(default_factory=list)


@dataclass
class AlertException:
    id: Optional[int] = None
    rule_type: str = ""  # "ip", "username", "server", "log_source", "rule_pattern"
    value: str = ""
    description: str = ""
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
