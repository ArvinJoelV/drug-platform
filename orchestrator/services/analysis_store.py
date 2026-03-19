from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, Optional
from uuid import uuid4


class InMemoryAnalysisStore:
    def __init__(self) -> None:
        self._records: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()

    def create_pending(self, molecule: str) -> str:
        analysis_id = str(uuid4())
        with self._lock:
            self._records[analysis_id] = {
                "analysis_id": analysis_id,
                "molecule": molecule,
                "status": "running",
                "created_at": self._timestamp(),
                "updated_at": self._timestamp(),
                "result": None,
                "error": None,
            }
        return analysis_id

    def complete(self, analysis_id: str, result: Dict[str, Any]) -> None:
        with self._lock:
            if analysis_id not in self._records:
                return
            self._records[analysis_id]["status"] = "completed"
            self._records[analysis_id]["updated_at"] = self._timestamp()
            self._records[analysis_id]["result"] = deepcopy(result)
            self._records[analysis_id]["error"] = None

    def fail(self, analysis_id: str, error: str) -> None:
        with self._lock:
            if analysis_id not in self._records:
                return
            self._records[analysis_id]["status"] = "failed"
            self._records[analysis_id]["updated_at"] = self._timestamp()
            self._records[analysis_id]["error"] = error

    def get(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            record = self._records.get(analysis_id)
            return deepcopy(record) if record else None

    def status(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        record = self.get(analysis_id)
        if not record:
            return None
        return {
            "analysis_id": record["analysis_id"],
            "molecule": record["molecule"],
            "status": record["status"],
            "created_at": record["created_at"],
            "updated_at": record["updated_at"],
            "error": record["error"],
        }

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()


analysis_store = InMemoryAnalysisStore()
