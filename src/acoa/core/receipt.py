"""Recibo de decisão - confirmação canônica do sistema ACOA."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4


@dataclass(frozen=True)
class Receipt:
    """Recibo imutável que confirma a decisão de um evento."""

    id: str = field(default_factory=lambda: str(uuid4()))
    event_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    decision: str = "pending"
    metrics: Dict[str, Any] = field(default_factory=dict)
    omega_score: Optional[float] = None
    signer: Optional[str] = None
    context_hash: Optional[str] = None
    previous_receipt_id: Optional[str] = None
    signature: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.event_id:
            raise ValueError("event_id é obrigatório")
        if not isinstance(self.metrics, dict):
            raise TypeError("metrics deve ser um dicionário")
        if self.context_hash is None:
            object.__setattr__(self, "context_hash", self.calculate_hash())

    def calculate_hash(self) -> str:
        """Calcula hash SHA-256 determinístico do recibo."""
        content = {
            "id": self.id,
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "decision": self.decision,
            "metrics": self.metrics,
            "omega_score": self.omega_score,
            "previous_receipt_id": self.previous_receipt_id,
        }
        serialized = json.dumps(content, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dicionário."""
        return {
            "id": self.id,
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "decision": self.decision,
            "metrics": self.metrics,
            "omega_score": self.omega_score,
            "signer": self.signer,
            "context_hash": self.context_hash,
            "previous_receipt_id": self.previous_receipt_id,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Receipt":
        """Deserializa de dicionário."""
        payload = dict(data)
        timestamp = payload.get("timestamp")
        if isinstance(timestamp, str):
            payload["timestamp"] = datetime.fromisoformat(timestamp)
        return cls(**payload)

    def validate(self) -> bool:
        """Valida integridade do recibo."""
        if self.context_hash != self.calculate_hash():
            return False
        if not self.id or len(self.id) != 36:
            return False
        if not self.event_id:
            return False
        return True
