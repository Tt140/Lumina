"""LuminaLab Swarm - DynamoDB Impact Ledger Module."""

import json
import logging
import random
import time
import uuid
from pathlib import Path
from typing import Any
from src.config import get_config
from src.contracts.schemas import ImpactMetrics

logger = logging.getLogger("luminalab.dynamo_ledger")

AGGREGATE_SESSION_ID = "AGGREGATE#GLOBAL"
MAX_TRANSACTION_CONFLICT_RETRIES = 6


class DynamoImpactLedger:
    """
    Handles DynamoDB table interactions to record and retrieve impact metrics.
    Uses atomic TransactWriteItems + an O(1) aggregate summary item (AGGREGATE#GLOBAL)
    in live AWS mode, eliminating table Scan operations.
    In Mock mode: uses in-memory store and optional local JSON file.
    """

    AGGREGATE_SESSION_ID = AGGREGATE_SESSION_ID

    def __init__(self, persist_to_file: bool = False, file_path: str = "_mock_ledger.json") -> None:
        """
        Initializes connection to DynamoDB with production timeouts/retries
        or instantiates local mock store.
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
                connect_timeout=2.0,
                read_timeout=5.0,
                retries={"total_max_attempts": 3, "mode": "standard"},
            )
            self.client = boto3.client("dynamodb", region_name=config.AWS_REGION, config=boto_config)
            self.table_name = config.DYNAMO_TABLE_NAME

    @staticmethod
    def _zero_stats() -> dict[str, Any]:
        """Return clean zero-initialized aggregate statistics."""
        return {
            "total_sessions": 0,
            "avg_grade_reduction": 0.0,
            "avg_cognitive_load_reduction_pct": 0.0,
            "avg_lab_size_kb": 0.0,
            "total_offline_ready_labs": 0,
            "avg_generation_time_sec": 0.0,
        }

    @staticmethod
    def _parse_session_item(item: dict[str, Any]) -> dict[str, Any]:
        """Convert raw DynamoDB AttributeValue dict into plain session metrics dict."""
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

    def _compute_local_stats(self) -> dict[str, Any]:
        """Compute aggregate statistics from in-memory fallback records."""
        sessions = [
            v for k, v in self._local_store.items() if k != self.AGGREGATE_SESSION_ID
        ]
        total_sessions = len(sessions)
        if total_sessions == 0:
            return self._zero_stats()

        avg_grade_reduction = sum(float(s.get("grade_reduction", 0)) for s in sessions) / total_sessions
        avg_cognitive_load = sum(float(s.get("cognitive_load_reduction_pct", 0)) for s in sessions) / total_sessions
        avg_lab_size_kb = sum(float(s.get("lab_size_kb", 0)) for s in sessions) / total_sessions
        total_offline_ready = sum(1 for s in sessions if s.get("is_offline_ready") is True)
        avg_generation_time = sum(float(s.get("generation_time_sec", 0)) for s in sessions) / total_sessions

        return {
            "total_sessions": total_sessions,
            "avg_grade_reduction": round(avg_grade_reduction, 2),
            "avg_cognitive_load_reduction_pct": round(avg_cognitive_load, 2),
            "avg_lab_size_kb": round(avg_lab_size_kb, 2),
            "total_offline_ready_labs": total_offline_ready,
            "avg_generation_time_sec": round(avg_generation_time, 2),
        }

    def _store_local_fallback(self, impact: ImpactMetrics, session_id: str) -> None:
        """Persist record idempotently to in-memory store (and optional local file)."""
        if session_id not in self._local_store:
            record = impact.model_dump()
            record["session_id"] = session_id
            self._local_store[session_id] = record
            if self.persist_to_file:
                self.save_to_file()

    def record_impact(self, impact: ImpactMetrics, session_id: str | None = None) -> dict[str, Any]:
        """
        Atomically and idempotently records societal impact metrics for a lab session
        and updates the O(1) aggregate summary record.

        Parameters:
            impact: ImpactMetrics object.
            session_id: Session ID. If None, auto-generates a UUID.

        Returns:
            dict with structure:
            {
                "session_id": str,
                "table_name": str,
                "status": "recorded" | "recorded_local_fallback",
                "timestamp": str
            }
        """
        session_id = session_id or str(uuid.uuid4())
        if session_id == self.AGGREGATE_SESSION_ID:
            raise ValueError(f"session_id '{self.AGGREGATE_SESSION_ID}' is reserved for aggregate stats")

        if self.mock_mode:
            if session_id in self._local_store:
                return {
                    "session_id": session_id,
                    "table_name": self.table_name,
                    "status": "recorded",
                    "idempotent_duplicate": True,
                    "timestamp": self._local_store[session_id].get("timestamp", impact.timestamp),
                }
            self._store_local_fallback(impact, session_id)
            return {
                "session_id": session_id,
                "table_name": self.table_name,
                "status": "recorded",
                "timestamp": impact.timestamp,
            }

        from botocore.exceptions import ClientError

        session_item = {
            "session_id": {"S": session_id},
            "timestamp": {"S": impact.timestamp},
            "baseline_grade_level": {"N": str(impact.baseline_grade_level)},
            "simplified_grade_level": {"N": str(impact.simplified_grade_level)},
            "grade_reduction": {"N": str(impact.grade_reduction)},
            "cognitive_load_reduction_pct": {"N": str(impact.cognitive_load_reduction_pct)},
            "lab_size_kb": {"N": str(impact.lab_size_kb)},
            "is_offline_ready": {"BOOL": impact.is_offline_ready},
            "generation_time_sec": {"N": str(impact.generation_time_sec)},
        }
        transact_items = [
            {
                "Put": {
                    "TableName": self.table_name,
                    "Item": session_item,
                    "ConditionExpression": "attribute_not_exists(session_id)",
                }
            },
            {
                "Update": {
                    "TableName": self.table_name,
                    "Key": {"session_id": {"S": self.AGGREGATE_SESSION_ID}},
                    "UpdateExpression": (
                        "SET updated_at = :ts "
                        "ADD total_sessions :one, "
                        "sum_grade_reduction :gr, "
                        "sum_cognitive_load_reduction_pct :clr, "
                        "sum_lab_size_kb :lkb, "
                        "total_offline_ready_labs :off, "
                        "sum_generation_time_sec :gt"
                    ),
                    "ExpressionAttributeValues": {
                        ":ts": {"S": impact.timestamp},
                        ":one": {"N": "1"},
                        ":gr": {"N": str(impact.grade_reduction)},
                        ":clr": {"N": str(impact.cognitive_load_reduction_pct)},
                        ":lkb": {"N": str(impact.lab_size_kb)},
                        ":off": {"N": "1" if impact.is_offline_ready else "0"},
                        ":gt": {"N": str(impact.generation_time_sec)},
                    },
                }
            },
        ]

        last_exc: Exception | None = None
        for attempt in range(MAX_TRANSACTION_CONFLICT_RETRIES + 1):
            try:
                self.client.transact_write_items(TransactItems=transact_items)
                return {
                    "session_id": session_id,
                    "table_name": self.table_name,
                    "status": "recorded",
                    "timestamp": impact.timestamp,
                }
            except ClientError as exc:
                last_exc = exc
                err_code = exc.response.get("Error", {}).get("Code", "")
                reasons = exc.response.get("CancellationReasons", [])
                reason_codes = [
                    r.get("Code", "") for r in reasons if isinstance(r, dict)
                ]
                # Session already recorded; return idempotent success without double-counting
                if err_code == "TransactionCanceledException" and (
                    (reasons and isinstance(reasons[0], dict) and reasons[0].get("Code") == "ConditionalCheckFailed")
                    or ("ConditionalCheckFailed" in reason_codes and "TransactionConflict" not in reason_codes)
                ):
                    logger.info(
                        json.dumps({
                            "event": "dynamo_idempotent_duplicate",
                            "session_id": session_id,
                            "table_name": self.table_name,
                        })
                    )
                    return {
                        "session_id": session_id,
                        "table_name": self.table_name,
                        "status": "recorded",
                        "idempotent_duplicate": True,
                        "timestamp": impact.timestamp,
                    }

                is_conflict = (
                    err_code == "TransactionConflictException"
                    or (err_code == "TransactionCanceledException" and "TransactionConflict" in reason_codes)
                )
                if is_conflict and attempt < MAX_TRANSACTION_CONFLICT_RETRIES:
                    backoff = random.uniform(0.015, min(0.4, 0.025 * (2 ** attempt)))
                    time.sleep(backoff)
                    continue
                break
            except Exception as exc:
                last_exc = exc
                break

        self._store_local_fallback(impact, session_id)
        logger.warning(
            json.dumps({
                "event": "dynamo_write_fallback",
                "session_id": session_id,
                "table_name": self.table_name,
                "status": "recorded_local_fallback",
                "error": str(last_exc) if last_exc else "unknown_error",
            })
        )
        return {
            "session_id": session_id,
            "table_name": self.table_name,
            "status": "recorded_local_fallback",
            "error": str(last_exc) if last_exc else "unknown_error",
            "timestamp": impact.timestamp,
        }

    def get_aggregate_stats(self) -> dict[str, Any]:
        """
        Retrieves aggregate societal impact statistics in O(1) via a single GetItem
        against the atomic aggregate summary item (no table Scan).

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
            return self._compute_local_stats()

        try:
            response = self.client.get_item(
                TableName=self.table_name,
                Key={"session_id": {"S": self.AGGREGATE_SESSION_ID}},
            )
            item = response.get("Item")
            if not item:
                return self._zero_stats()

            total_sessions = int(float(item.get("total_sessions", {}).get("N", 0)))
            if total_sessions <= 0:
                return self._zero_stats()

            sum_grade = float(item.get("sum_grade_reduction", {}).get("N", 0))
            sum_cognitive = float(item.get("sum_cognitive_load_reduction_pct", {}).get("N", 0))
            sum_lab_kb = float(item.get("sum_lab_size_kb", {}).get("N", 0))
            total_offline = int(float(item.get("total_offline_ready_labs", {}).get("N", 0)))
            sum_gen_sec = float(item.get("sum_generation_time_sec", {}).get("N", 0))

            return {
                "total_sessions": total_sessions,
                "avg_grade_reduction": round(sum_grade / total_sessions, 2),
                "avg_cognitive_load_reduction_pct": round(sum_cognitive / total_sessions, 2),
                "avg_lab_size_kb": round(sum_lab_kb / total_sessions, 2),
                "total_offline_ready_labs": total_offline,
                "avg_generation_time_sec": round(sum_gen_sec / total_sessions, 2),
            }
        except Exception as exc:
            logger.warning(
                json.dumps({
                    "event": "dynamo_stats_read_fallback",
                    "table_name": self.table_name,
                    "error": str(exc),
                })
            )
            return self._compute_local_stats()

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """
        Retrieves record of a single session by its session ID.

        Parameters:
            session_id: Session identifier.

        Returns:
            dict containing session data, or None if not found.
        """
        if session_id == self.AGGREGATE_SESSION_ID:
            return None
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
            return self._parse_session_item(item)
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
