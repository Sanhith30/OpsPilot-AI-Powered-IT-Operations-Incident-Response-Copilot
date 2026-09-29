from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, ClassVar, Dict, List, Optional

from pydantic import BaseModel, Field

from app.ai.tools.base import BaseTool
from app.repositories.service_metric_repository import ServiceMetricRepository


class GetServiceMetricsInput(BaseModel):
    """Input schema for the get_service_metrics tool."""

    service_name: str = Field(
        ...,
        description="Name of the service to fetch metrics for (e.g. 'payment-api', 'auth-service').",
    )
    metric_name: Optional[str] = Field(
        None,
        description=(
            "Specific metric to query: cpu_usage_percent, memory_usage_mb, error_rate, "
            "p99_latency_ms, request_rate_rps, db_connection_pool. "
            "Leave blank to return all metrics."
        ),
    )
    environment: Optional[str] = Field(
        "Production",
        description="Deployment environment.",
    )
    lookback_minutes: int = Field(
        60,
        ge=1,
        le=1440,
        description="How many minutes of historical data to fetch (default: last 60 minutes).",
    )
    limit: int = Field(
        50,
        ge=1,
        le=200,
        description="Maximum number of metric data points to return.",
    )


class GetServiceMetricsTool(BaseTool):
    """
    Retrieves recent time-series operational metrics for a service.

    Use this tool to assess the current health of a service: CPU utilization,
    memory usage, error rates, latency percentiles, request throughput, and
    database connection pool saturation.
    """

    name: ClassVar[str] = "get_service_metrics"
    description: ClassVar[str] = (
        "Retrieve time-series operational metrics (CPU, memory, error rate, latency, RPS, "
        "DB pool) for a named service over a configurable lookback window. "
        "Use to detect anomalies, correlate spikes with incidents, and assess service health."
    )
    args_schema: ClassVar[type[BaseModel]] = GetServiceMetricsInput

    def __init__(self, *, metric_repository: ServiceMetricRepository) -> None:
        self._repo = metric_repository

    def execute(self, validated_input: GetServiceMetricsInput) -> Dict[str, Any]:
        from_time = datetime.now(timezone.utc) - timedelta(
            minutes=validated_input.lookback_minutes
        )

        metrics = self._repo.get_by_service_name(
            service_name=validated_input.service_name,
            metric_name=validated_input.metric_name,
            from_time=from_time,
            limit=validated_input.limit,
        )

        data_points: List[Dict[str, Any]] = []
        aggregated: Dict[str, List[float]] = {}

        for m in metrics:
            data_points.append(
                {
                    "metric_name": m.metric_name,
                    "metric_value": m.metric_value,
                    "unit": m.unit,
                    "recorded_at": m.recorded_at.isoformat() if m.recorded_at else None,
                    "instance_id": m.instance_id,
                    "environment": m.environment,
                }
            )
            aggregated.setdefault(m.metric_name, []).append(m.metric_value)

        # Build summary statistics per metric name
        summary: Dict[str, Any] = {}
        for name, values in aggregated.items():
            summary[name] = {
                "count": len(values),
                "latest": values[0] if values else None,
                "avg": round(sum(values) / len(values), 4) if values else None,
                "min": round(min(values), 4) if values else None,
                "max": round(max(values), 4) if values else None,
            }

        # Anomaly flags
        anomalies: List[str] = []
        if "cpu_usage_percent" in summary and (summary["cpu_usage_percent"]["latest"] or 0) > 85:
            anomalies.append(f"⚠ CPU usage is critically high: {summary['cpu_usage_percent']['latest']}%")
        if "error_rate" in summary and (summary["error_rate"]["latest"] or 0) > 0.05:
            anomalies.append(f"⚠ Error rate elevated: {summary['error_rate']['latest'] * 100:.1f}%")
        if "p99_latency_ms" in summary and (summary["p99_latency_ms"]["latest"] or 0) > 1000:
            anomalies.append(f"⚠ p99 latency critical: {summary['p99_latency_ms']['latest']}ms")
        if "db_connection_pool" in summary and (summary["db_connection_pool"]["latest"] or 0) > 90:
            anomalies.append(f"⚠ DB connection pool nearly exhausted: {summary['db_connection_pool']['latest']}%")

        return {
            "service_name": validated_input.service_name,
            "environment": validated_input.environment,
            "lookback_minutes": validated_input.lookback_minutes,
            "total_data_points": len(data_points),
            "summary": summary,
            "anomalies": anomalies,
            "data_points": data_points,
        }
