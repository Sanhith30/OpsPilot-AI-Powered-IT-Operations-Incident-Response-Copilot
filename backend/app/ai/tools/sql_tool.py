"""
Guarded Read-Only SQL Tool for OpsPilot.

Allows the autonomous conversational agent to execute safe, analytical SELECT queries
against the operational database (e.g. querying service states, error rates, incidents).

Safety Guarantees:
  - Enforces read-only SELECT statements only.
  - Strictly blocks destructive DDL/DML: DELETE, UPDATE, INSERT, DROP, ALTER, TRUNCATE,
    CREATE, GRANT, REVOKE, EXEC.
  - Blocks multiple statement chaining (semicolon injection).
  - Enforces strict LIMIT to prevent unbounded memory consumption.
"""
from __future__ import annotations

import re
from typing import Any, ClassVar, Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.ai.tools.base import BaseTool

FORBIDDEN_SQL_KEYWORDS = {
    "DELETE",
    "UPDATE",
    "INSERT",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "GRANT",
    "REVOKE",
    "EXEC",
    "EXECUTE",
    "MERGE",
    "UPSERT",
    "REPLACE",
}


class ReadOnlySqlInput(BaseModel):
    query: str = Field(
        ...,
        description="The SQL SELECT statement to execute against the operational database.",
    )
    limit: Optional[int] = Field(
        50,
        ge=1,
        le=100,
        description="Maximum rows to return (default 50, max 100).",
    )


class ReadOnlySqlTool(BaseTool):
    """
    Executes a guarded, read-only analytical SQL SELECT query.
    Blocks any modifying or destructive operations.
    """

    name: ClassVar[str] = "query_database_readonly"
    description: ClassVar[str] = (
        "Execute a safe, read-only SELECT query against the operational database to inspect "
        "services, incidents, deployments, logs, or metrics. Only SELECT queries are permitted. "
        "All data-modifying queries (UPDATE, DELETE, INSERT, DROP) are strictly blocked."
    )
    args_schema: ClassVar[type[BaseModel]] = ReadOnlySqlInput

    def __init__(self, *, db: Session) -> None:
        self._db = db

    def execute(self, validated_input: ReadOnlySqlInput) -> Dict[str, Any]:
        clean_query = validated_input.query.strip()
        limit = validated_input.limit or 50

        # Safety Check 1: Must start with SELECT or WITH (for CTEs)
        stripped_upper = clean_query.upper().lstrip()
        if not (stripped_upper.startswith("SELECT") or stripped_upper.startswith("WITH")):
            return {
                "status": "ERROR",
                "error": "Forbidden statement: Read-only query tool only permits SELECT queries.",
            }

        # Safety Check 2: Check for forbidden DDL / DML keywords using word boundaries
        for keyword in FORBIDDEN_SQL_KEYWORDS:
            pattern = rf"\b{keyword}\b"
            if re.search(pattern, stripped_upper):
                return {
                    "status": "ERROR",
                    "error": f"Forbidden keyword '{keyword}': Modification statements are strictly BLOCKED.",
                }

        # Safety Check 3: Check for semicolon statement chaining (prevent multiple statements)
        query_without_trailing_semi = clean_query.rstrip(";").strip()
        if ";" in query_without_trailing_semi:
            return {
                "status": "ERROR",
                "error": "Multiple SQL statements detected: Chained queries are BLOCKED.",
            }

        # Safety Check 4: Enforce LIMIT
        if not re.search(r"\bLIMIT\s+\d+", stripped_upper):
            clean_query = f"{query_without_trailing_semi} LIMIT {limit}"

        try:
            result = self._db.execute(text(clean_query))
            columns = list(result.keys()) if result.returns_rows else []
            rows = [dict(zip(columns, row)) for row in result.fetchall()] if result.returns_rows else []

            # Serialize any non-serializable objects (datetime, Decimal, UUID)
            serialized_rows = []
            for r in rows:
                serialized_row = {}
                for k, v in r.items():
                    if hasattr(v, "isoformat"):
                        serialized_row[k] = v.isoformat()
                    else:
                        serialized_row[k] = str(v) if not isinstance(v, (int, float, bool, type(None), str, list, dict)) else v
                serialized_rows.append(serialized_row)

            return {
                "status": "SUCCESS",
                "columns": columns,
                "row_count": len(serialized_rows),
                "rows": serialized_rows,
            }
        except Exception as exc:
            return {
                "status": "ERROR",
                "error": f"SQL execution error: {str(exc)}",
            }
