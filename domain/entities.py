from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class Alert:
    server_name: str
    source_log: str
    timestamp: datetime
    level: str
    message: str
    ip_address: Optional[str] = None
    rule: Optional[str] = None
    id: Optional[int] = None


@dataclass
class Server:
    name: str
    host: str
    port: int
    username: str
    password: Optional[str] = None
    private_key_path: Optional[str] = None
    logs: List[str] = None
