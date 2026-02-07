"""Evento canônico - base do sistema ACOA."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4


@dataclass(frozen=True)
class Event:
    """Evento canônico imutável."""

    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    payload: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = "1.0.0"
    author: Optional[str] = None
    context_hash: Optional[str] = None
    previous_event_id: Optional[str] = None
    signature: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.payload, dict):
            raise TypeError("Payload deve ser um dicionário")
        if self.context_hash is None:
            object.__setattr__(self, "context_hash", self.calculate_hash())

    def calculate_hash(self) -> str:
        """Calcula hash SHA-256 determinístico do evento."""
        content = {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
            "schema_version": self.schema_version,
            "previous_event_id": self.previous_event_id,
        }
        serialized = json.dumps(content, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dicionário."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
            "schema_version": self.schema_version,
            "author": self.author,
            "context_hash": self.context_hash,
            "previous_event_id": self.previous_event_id,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Deserializa de dicionário."""
        payload = dict(data)
        timestamp = payload.get("timestamp")
        if isinstance(timestamp, str):
            payload["timestamp"] = datetime.fromisoformat(timestamp)
        return cls(**payload)

    def validate(self) -> bool:
        """Valida integridade do evento."""
        if self.context_hash != self.calculate_hash():
            return False
        if not self.id or len(self.id) != 36:
            return False
        return True
