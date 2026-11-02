"""LuminaLab Swarm - DynamoDB Impact Ledger Module."""

import json
import os
import uuid
from pathlib import Path
from typing import Any
from src.config import get_config
from src.contracts.schemas import ImpactMetrics


class DynamoImpactLedger:
    """
    Handles DynamoDB table interactions to record and retrieve impact metrics.
    In Mock mode: uses in-memory store and optional local JSON file.
    """

    def __init__(self, persist_to_file: bool = False, file_path: str = "_mock_ledger.json") -> None:
        """
        Initializes connection to DynamoDB or instantiates local mock store.
        """
        config = get_config()
        self.mock_mode = config.LUMINA_MOCK_MODE
        self.persist_to_file = persist_to_file
        self.file_path = Path(file_path)
        self._local_store: dict[str, dict[str, Any]] = {}

        if self.mock_mode:
            self.client = None
            self.table_name = "mock_local_store"
            if self.persist_to_file and self.file_path.exists():
                self.load_from_file()
        else:
            import boto3
            import botocore.config
            boto_config = botocore.config.Config(
                connect_timeout=0.6,
                read_timeout=0.6,
                retries={"max_attempts": 0}
            )
            self.client = boto3.client("dynamodb", region_name=config.AWS_REGION, config=boto_config)
            self.table_name = config.DYNAMO_TABLE_NAME

    def record_impact(self, impact: ImpactMetrics, session_id: str | None = None) -> dict[str, Any]:
        """
        Records societal impact metrics for a single lab generation session.

        Parameters:
            impact: ImpactMetrics object.
            session_id: Session ID. If None, auto-generates a UUID.

        Returns:
            dict with structure:
            {
                "session_id": str,
                "table_name": str,
                "status": "recorded",
                "timestamp": str
            }
        """
        session_id = session_id or str(uuid.uuid4())

        if self.mock_mode:
            record = impact.model_dump()
            record["session_id"] = session_id
            self._local_store[session_id] = record
            if self.persist_to_file:
                self.save_to_file()
            return {
                "session_id": session_id,
                "table_name": self.table_name,
                "status": "recorded",
                "timestamp": impact.timestamp,
            }
        else:
            try:
                self.client.put_item(
                    TableName=self.table_name,
                    Item={
                        "session_id": {"S": session_id},
                        "timestamp": {"S": impact.timestamp},
                        "baseline_grade_level": {"N": str(impact.baseline_grade_level)},
                        "simplified_grade_level": {"N": str(impact.simplified_grade_level)},
                        "grade_reduction": {"N": str(impact.grade_reduction)},
                        "cognitive_load_reduction_pct": {"N": str(impact.cognitive_load_reduction_pct)},
                        "lab_size_kb": {"N": str(impact.lab_size_kb)},
                        "is_offline_ready": {"BOOL": impact.is_offline_ready},
                        "generation_time_sec": {"N": str(impact.generation_time_sec)},
                    },
                )
                return {
                    "session_id": session_id,
                    "table_name": self.table_name,
                    "status": "recorded",
                    "timestamp": impact.timestamp,
                }
            except Exception as e:
                record = impact.model_dump()
                record["session_id"] = session_id
                self._local_store[session_id] = record
                if self.persist_to_file:
                    self.save_to_file()
                return {
                    "session_id": session_id,
                    "table_name": self.table_name,
                    "status": "recorded_local_fallback",
                    "error": str(e),
                    "timestamp": impact.timestamp,
                }

    def get_aggregate_stats(self) -> dict[str, Any]:
        """
        Retrieves aggregate societal impact statistics for all recorded sessions.

        Returns:
            dict with structure:
            {
                "total_sessions": int,
                "avg_grade_reduction": float,
                "avg_cognitive_load_reduction_pct": float,
                "avg_lab_size_kb": float,
                "total_offline_ready_labs": int,
                "avg_generation_time_sec": float
            }
        """
        if self.mock_mode:
            sessions = list(self._local_store.values())
        else:
            try:
                response = self.client.scan(TableName=self.table_name)
                items = response.get("Items", [])
                sessions = [
                    {
                        "session_id": item["session_id"]["S"],
                        "timestamp": item.get("timestamp", {}).get("S", ""),
                        "baseline_grade_level": float(item.get("baseline_grade_level", {}).get("N", 0)),
                        "simplified_grade_level": float(item.get("simplified_grade_level", {}).get("N", 0)),
                        "grade_reduction": float(item.get("grade_reduction", {}).get("N", 0)),
                        "cognitive_load_reduction_pct": float(item.get("cognitive_load_reduction_pct", {}).get("N", 0)),
                        "lab_size_kb": float(item.get("lab_size_kb", {}).get("N", 0)),
                        "is_offline_ready": item.get("is_offline_ready", {}).get("BOOL", False),
                        "generation_time_sec": float(item.get("generation_time_sec", {}).get("N", 0)),
                    }
                    for item in items
                ]
            except Exception:
                sessions = list(self._local_store.values())

        total_sessions = len(sessions)
        if total_sessions == 0:
            return {
                "total_sessions": 0,
                "avg_grade_reduction": 0.0,
                "avg_cognitive_load_reduction_pct": 0.0,
                "avg_lab_size_kb": 0.0,
                "total_offline_ready_labs": 0,
                "avg_generation_time_sec": 0.0,
            }

        avg_grade_reduction = sum(float(s.get("grade_reduction", 0)) for s in sessions) / total_sessions
        avg_cognitive_load_reduction_pct = sum(float(s.get("cognitive_load_reduction_pct", 0)) for s in sessions) / total_sessions
        avg_lab_size_kb = sum(float(s.get("lab_size_kb", 0)) for s in sessions) / total_sessions
        total_offline_ready = sum(1 for s in sessions if s.get("is_offline_ready") is True)
        avg_generation_time = sum(float(s.get("generation_time_sec", 0)) for s in sessions) / total_sessions

        return {
            "total_sessions": total_sessions,
            "avg_grade_reduction": round(avg_grade_reduction, 2),
            "avg_cognitive_load_reduction_pct": round(avg_cognitive_load_reduction_pct, 2),
            "avg_lab_size_kb": round(avg_lab_size_kb, 2),
            "total_offline_ready_labs": total_offline_ready,
            "avg_generation_time_sec": round(avg_generation_time, 2),
        }

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """
        Retrieves record of a single session by its session ID.

        Parameters:
            session_id: Session identifier.

        Returns:
            dict containing session data, or None if not found.
        """
        if self.mock_mode:
            return self._local_store.get(session_id, None)

        try:
            response = self.client.get_item(
                TableName=self.table_name,
                Key={"session_id": {"S": session_id}},
            )
            item = response.get("Item")
            if not item:
                return None
            return {
                "session_id": item["session_id"]["S"],
                "timestamp": item.get("timestamp", {}).get("S", ""),
                "baseline_grade_level": float(item.get("baseline_grade_level", {}).get("N", 0)),
                "simplified_grade_level": float(item.get("simplified_grade_level", {}).get("N", 0)),
                "grade_reduction": float(item.get("grade_reduction", {}).get("N", 0)),
                "cognitive_load_reduction_pct": float(item.get("cognitive_load_reduction_pct", {}).get("N", 0)),
                "lab_size_kb": float(item.get("lab_size_kb", {}).get("N", 0)),
                "is_offline_ready": item.get("is_offline_ready", {}).get("BOOL", False),
                "generation_time_sec": float(item.get("generation_time_sec", {}).get("N", 0)),
            }
        except Exception:
            return None

    def save_to_file(self, path: str | Path | None = None) -> None:
        """Persist session ledger to a local JSON file."""
        target_path = Path(path) if path else self.file_path
        try:
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(self._local_store, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def load_from_file(self, path: str | Path | None = None) -> None:
        """Load session ledger from a local JSON file."""
        target_path = Path(path) if path else self.file_path
        if target_path.exists():
            try:
                with open(target_path, "r", encoding="utf-8") as f:
                    self._local_store = json.load(f)
            except Exception:
                pass

    def clear(self) -> None:
        """Clear all in-memory session records."""
        self._local_store.clear()
