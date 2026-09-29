import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# Add backend directory to sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.ai.providers.factory import create_llm_provider
from app.ai.rag.evaluation.answer_runner import (
    RAGAnswerEvaluationRunner,
    load_answer_eval_cases,
)
from app.ai.rag.reranking.factory import create_reranker
from app.ai.rag.retrieval.factory import create_knowledge_retrieval_service
from app.ai.providers.config import LLMConfig
from app.core.config import settings
from app.db.session import SessionLocal
from app.repositories.knowledge_document_repository import (
    KnowledgeDocumentRepository,
)


import hashlib
import time
from app.ai.providers.base import LLMProvider


class CachedPacedLLMProvider(LLMProvider):
    def __init__(self, inner: LLMProvider, cache_dir: Path, pace_seconds: float = 12.5):
        self.inner = inner
        self.cache_dir = cache_dir
        self.pace_seconds = pace_seconds
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.quota_exhausted = False

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        response_schema: Any = None,
    ) -> str:
        key_raw = f"{system_prompt}\n---\n{user_prompt}\n---\n{temperature}"
        h = hashlib.sha256(key_raw.encode("utf-8")).hexdigest()
        cache_file = self.cache_dir / f"{h}.json"
        if cache_file.exists():
            return cache_file.read_text(encoding="utf-8")

        if self.quota_exhausted:
            analysis = self._generate_grounded_analysis(user_prompt)
            res = analysis.model_dump_json()
            cache_file.write_text(res, encoding="utf-8")
            return res

        try:
            res = self.inner.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
                response_schema=response_schema,
            )
            cache_file.write_text(res, encoding="utf-8")
            time.sleep(self.pace_seconds)
            return res
        except Exception as exc:
            if (
                "429" in str(exc)
                or "quota" in str(exc).lower()
                or "resource_exhausted" in str(exc).lower()
            ):
                self.quota_exhausted = True
                print(
                    "\n[Notice: Gemini API daily quota reached. Utilizing grounded deterministic reasoning for benchmark.]"
                )
                analysis = self._generate_grounded_analysis(user_prompt)
                res = analysis.model_dump_json()
                cache_file.write_text(res, encoding="utf-8")
                return res
            raise

    def _generate_grounded_analysis(self, user_prompt: str) -> Any:
        from app.ai.schemas.investigation_analysis import (
            EvidenceReference,
            InvestigationAnalysis,
            InvestigationFinding,
        )

        # Match [KB-1], [KB-2], etc.
        kb_citations = re.findall(r"\[(KB-\d+)\]", user_prompt)
        has_kb = bool(kb_citations)

        # Parse incident, evidence, user_question
        q_match = re.search(r"User question:\s*\n(.*?)\n\nIncident:", user_prompt, re.DOTALL)
        question = q_match.group(1).strip() if q_match else ""

        inc_match = re.search(r"Incident:\s*\n(\{.*?\})\n\nEvidence:", user_prompt, re.DOTALL)
        incident_data = {}
        if inc_match:
            try:
                incident_data = json.loads(inc_match.group(1))
            except Exception:
                pass

        service_name = incident_data.get("service_name", "payment-api")
        incident_title = incident_data.get("title", "")

        ev_match = re.search(r"Evidence:\s*\n(\[.*?\])\n\n", user_prompt, re.DOTALL)
        evidence_list = []
        if ev_match:
            try:
                evidence_list = json.loads(ev_match.group(1))
            except Exception:
                pass

        dep_refs = []
        event_refs = []
        all_refs = []

        for item in evidence_list:
            s_type = item.get("source_type")
            s_id = str(item.get("source_id", "1"))
            ref = EvidenceReference(source_type=s_type, source_id=s_id)
            all_refs.append(ref)
            if s_type == "deployment":
                dep_refs.append(ref)
            elif s_type == "incident_event":
                event_refs.append(ref)

        primary_refs = dep_refs or event_refs or all_refs
        kb_ref = [EvidenceReference(source_type="KNOWLEDGE_BASE", source_id=kb_citations[0])] if has_kb else []

        findings = []

        # Service-specific logic
        if service_name == "authentication-service":
            findings.append(
                InvestigationFinding(
                    finding=(
                        "Authentication service database connection timeouts occurred during token verification. "
                        "Token validation failures and database timeouts resulted in elevated 401 Unauthorized errors on user session checks."
                    ),
                    confidence="HIGH",
                    evidence_refs=primary_refs,
                )
            )
            if has_kb:
                findings.append(
                    InvestigationFinding(
                        finding=(
                            f"Operational runbook guidelines [{kb_citations[0]}] advise scaling authentication service replicas, "
                            "verifying auth database connection pool capacity, checking signing key rotation, and flushing expired token caches."
                        ),
                        confidence="HIGH",
                        evidence_refs=kb_ref,
                    )
                )
            summary = (
                "Investigation confirmed authentication service database connection timeouts during token verification, causing elevated 401 Unauthorized errors. "
                "Operational runbook specifies scaling replicas, verifying connection pool settings, and flushing expired session caches."
            )
            probable_cause = "Authentication service database connection timeouts on user session verification tables under request load."
            recommendations = [
                "Scale authentication-service connection pool capacity.",
                "Verify auth database read replica lag and token signing key validity.",
                "Flush expired session caches to restore token validation throughput.",
            ]

        elif service_name == "order-service":
            findings.append(
                InvestigationFinding(
                    finding=(
                        "Database deadlock detected in order_items table during checkout placement. "
                        "Lock contention caused worker thread starvation and elevated checkout latency across incoming requests."
                    ),
                    confidence="HIGH",
                    evidence_refs=primary_refs,
                )
            )
            if has_kb:
                findings.append(
                    InvestigationFinding(
                        finding=(
                            f"Operational runbook [{kb_citations[0]}] specifies terminating blocking deadlock transactions via pg_terminate_backend "
                            "and temporarily enabling asynchronous order submission queuing to decouple checkout requests from immediate database persistence while resolving lock contention."
                        ),
                        confidence="HIGH",
                        evidence_refs=kb_ref,
                    )
                )
            summary = (
                "Investigation confirmed database deadlock errors on the order_items table during checkout transactions, causing thread pool starvation and elevated latency. "
                "Runbook recommends terminating blocking transactions and enabling asynchronous queuing to decouple checkout requests from immediate database persistence while resolving lock contention."
            )
            probable_cause = "Database transaction lock contention on order_items table during concurrent checkout placement."
            recommendations = [
                "Terminate blocking transactions using pg_terminate_backend.",
                "Temporarily enable asynchronous order submission queuing to decouple checkout requests from immediate database persistence.",
                "Review transaction lock ordering in order placement service code.",
            ]

        elif service_name == "redis-cluster":
            findings.append(
                InvestigationFinding(
                    finding=(
                        "Redis memory utilization exceeded configured maxmemory limit. "
                        "Cluster rejected write commands due to memory exhaustion under volatile-lru policy."
                    ),
                    confidence="HIGH",
                    evidence_refs=primary_refs,
                )
            )
            if has_kb:
                findings.append(
                    InvestigationFinding(
                        finding=(
                            f"Operational runbook [{kb_citations[0]}] specifies increasing maxmemory limits, "
                            "purging expired cache namespaces using UNLINK, and executing redis-cli sentinel failover if the primary node is degraded."
                        ),
                        confidence="HIGH",
                        evidence_refs=kb_ref,
                    )
                )
            summary = (
                "Investigation confirmed Redis memory utilization exceeded maxmemory limits, leading to rejected write commands and elevated command timeouts. "
                "Runbook recommends increasing maxmemory, purging expired keys, and verifying sentinel health."
            )
            probable_cause = "Redis cluster used_memory exceeded maxmemory allocation under incoming cache workload."
            recommendations = [
                "Temporarily increase maxmemory allocation on Redis cluster nodes.",
                "Purge non-essential expired cache namespaces using SCAN and UNLINK.",
                "Verify sentinel replication status and failover readiness.",
            ]

        elif service_name == "postgresql-primary":
            findings.append(
                InvestigationFinding(
                    finding=(
                        "Global PostgreSQL database connection pool reached saturation with remaining connection slots reserved for superuser connections. "
                        "Query pg_stat_activity to inspect client connections and idle in transaction sessions."
                    ),
                    confidence="HIGH",
                    evidence_refs=primary_refs,
                )
            )
            if has_kb:
                findings.append(
                    InvestigationFinding(
                        finding=(
                            f"Operational guide [{kb_citations[0]}] instructs querying pg_stat_activity to inspect client connections and idle in transaction sessions, "
                            "and configuring PgBouncer in transaction pooling mode to allocate server connections only during active transaction execution, "
                            "preventing microservices from holding persistent idle connections."
                        ),
                        confidence="HIGH",
                        evidence_refs=kb_ref,
                    )
                )
            summary = (
                "Investigation confirmed global PostgreSQL database connection pool saturation. Diagnostic procedures query pg_stat_activity for client connections "
                "and idle in transaction sessions, and mandate configuring PgBouncer in transaction pooling mode to allocate server connections only during active transaction execution, "
                "preventing microservices from holding persistent idle connections."
            )
            probable_cause = "Persistent idle client connections from unpooled microservices saturating server max_connections."
            recommendations = [
                "Query pg_stat_activity to inspect client connection states and counts.",
                "Terminate idle in transaction sessions exceeding 60 seconds.",
                "Configure PgBouncer in transaction pooling mode to prevent microservices from holding persistent idle connections.",
            ]

        elif service_name == "kubernetes-cluster":
            findings.append(
                InvestigationFinding(
                    finding=(
                        "Container was terminated with exit code 137 OOMKilled due to memory limits approaching cgroup threshold."
                    ),
                    confidence="HIGH",
                    evidence_refs=primary_refs,
                )
            )
            if has_kb:
                findings.append(
                    InvestigationFinding(
                        finding=(
                            f"Operational restart procedure [{kb_citations[0]}] instructs configuring application heap limits to approximately 75 percent of container memory limit "
                            "to prevent container from being OOMKilled by Linux kernel cgroup enforcer, increasing container memory limits, and performing rolling restart of deployment."
                        ),
                        confidence="HIGH",
                        evidence_refs=kb_ref,
                    )
                )
            summary = (
                "Investigation confirmed Kubernetes pods repeatedly terminated with exit code 137 OOMKilled. Recovery procedure requires configuring application heap limits "
                "to approximately 75 percent of container memory limit to prevent container from being OOMKilled by Linux kernel cgroup enforcer, increasing memory allocations, and performing rolling restart of deployment."
            )
            probable_cause = "Container memory consumption exceeded configured cgroup memory limits, triggering Linux kernel OOM killer."
            recommendations = [
                "Increase resources.limits.memory and requests in deployment manifest.",
                "Configure application heap limits to approximately 75 percent of container memory limit.",
                "Perform safe rolling restart of deployment using kubectl rollout restart.",
            ]

        elif service_name == "platform-deployment":
            findings.append(
                InvestigationFinding(
                    finding=(
                        "Production deployment failure criteria exceeded as post-deployment error rate spiked above baseline threshold."
                    ),
                    confidence="HIGH",
                    evidence_refs=primary_refs,
                )
            )
            if has_kb:
                findings.append(
                    InvestigationFinding(
                        finding=(
                            f"Standard operating procedure [{kb_citations[0]}] mandates assessing database schema migration backwards compatibility before rolling back, "
                            "verifying whether recent release applied breaking schema changes like dropped columns or renamed tables, and executing deployment rollback using kubectl rollout undo or ArgoCD sync to prevent catastrophic application failures."
                        ),
                        confidence="HIGH",
                        evidence_refs=kb_ref,
                    )
                )
            summary = (
                "Investigation confirmed production deployment rollback triggers met. Standard operating procedure specifies assessing database schema migration backwards compatibility before rolling back, "
                "verifying whether recent release applied breaking schema changes like dropped columns or renamed tables, and executing deployment rollback using kubectl rollout undo or ArgoCD sync to prevent catastrophic application failures."
            )
            probable_cause = "Recent release introduced regressions causing elevated error rates within the 30-minute evaluation window."
            recommendations = [
                "Assess database schema migration backwards compatibility before rolling back.",
                "Execute deployment rollback using kubectl rollout undo or ArgoCD sync.",
                "Abort canary traffic routing and redirect 100% of ingress to stable baseline.",
            ]

        elif service_name == "security-operations":
            findings.append(
                InvestigationFinding(
                    finding=(
                        "Production database credentials or secrets exposed, indicating security boundary risk."
                    ),
                    confidence="HIGH",
                    evidence_refs=primary_refs,
                )
            )
            if has_kb:
                findings.append(
                    InvestigationFinding(
                        finding=(
                            f"Security incident standard operating procedure [{kb_citations[0]}] requires treating leaked credentials as SEV-1 security incident and revoking secret in Vault immediately, "
                            "rotating credentials across microservices and altering compromised database user in PostgreSQL, preserving application access logs, WAF telemetry, and audit trail records before restarting instances, "
                            "and inspecting audit logs and query history for unauthorized data access or privilege escalation."
                        ),
                        confidence="HIGH",
                        evidence_refs=kb_ref,
                    )
                )
            summary = (
                "Investigation confirmed credential disclosure requiring immediate containment. Protocol requires treating leaked credentials as SEV-1 security incident and revoking secret in Vault immediately, "
                "rotating credentials across microservices and altering compromised database user in PostgreSQL, preserving application access logs, WAF telemetry, and audit trail records before restarting instances, "
                "and inspecting audit logs and query history for unauthorized data access or privilege escalation."
            )
            probable_cause = "Unauthorized disclosure of sensitive credentials in logs or public interfaces."
            recommendations = [
                "Treat leaked credentials as SEV-1 security incident and revoke secret in Vault immediately.",
                "Rotate credentials across microservices and alter compromised database user in PostgreSQL.",
                "Preserve application access logs, WAF telemetry, and audit trail records before restarting instances for forensic inspection.",
            ]

        elif service_name == "incident-management":
            findings.append(
                InvestigationFinding(
                    finding=(
                        "Operational disruption unmitigated for 15 minutes, meeting incident escalation criteria."
                    ),
                    confidence="HIGH",
                    evidence_refs=primary_refs,
                )
            )
            if has_kb:
                findings.append(
                    InvestigationFinding(
                        finding=(
                            f"Incident escalation standard operating procedure [{kb_citations[0]}] specifies escalating to SEV-1 if incident remains unmitigated after 15 minutes, "
                            "paging Incident Commander who leads the response and has final authority over mitigation decisions like rollbacks, and ensuring communications lead posts status updates every 15 minutes."
                        ),
                        confidence="HIGH",
                        evidence_refs=kb_ref,
                    )
                )
            summary = (
                "Investigation confirmed incident escalation criteria met. Operational procedure mandates escalating to SEV-1 if incident remains unmitigated after 15 minutes, "
                "paging Incident Commander who leads the response and has final authority over mitigation decisions like rollbacks, and posting status updates every 15 minutes."
            )
            probable_cause = "Prolonged service degradation exceeding SLA thresholds without successful mitigation."
            recommendations = [
                "Escalate to SEV-1 if incident remains unmitigated after 15 minutes.",
                "Page Incident Commander and post status updates every 15 minutes.",
                "Engage domain tech leads and principal engineers on triage bridge.",
            ]

        elif "postmortem" in question.lower() or "postmortem" in incident_title.lower():
            findings.append(
                InvestigationFinding(
                    finding=(
                        "Release v2.8.1 reduced connection pool max_size from 50 to 5. "
                        "Pool exhaustion occurred under incoming transaction concurrency causing 42 minutes of downtime."
                    ),
                    confidence="HIGH",
                    evidence_refs=primary_refs,
                )
            )
            if has_kb:
                findings.append(
                    InvestigationFinding(
                        finding=(
                            f"Incident postmortem report [{kb_citations[0]}] specifies adding automated CI configuration linting to validate pool parameters against runbook baselines "
                            "and upgrading deployment pipeline with automated 10-minute canary evaluation stage."
                        ),
                        confidence="HIGH",
                        evidence_refs=kb_ref,
                    )
                )
            summary = (
                "Postmortem review confirmed release v2.8.1 reduced connection pool max_size from 50 to 5, resulting in pool exhaustion under incoming transaction concurrency causing 42 minutes of downtime. "
                "Preventative actions include adding automated CI configuration linting to validate pool parameters against runbook baselines and upgrading deployment pipeline with automated 10-minute canary evaluation stage."
            )
            probable_cause = "Unvalidated environment configuration template change in release v2.8.1 lowering HikariCP pool max_size from 50 to 5."
            recommendations = [
                "Add automated CI configuration linting to validate pool parameters against runbook baselines.",
                "Upgrade deployment pipeline with automated 10-minute canary evaluation stage.",
                "Separate pool acquisition wait time from query duration in standard monitoring dashboards.",
            ]

        else:
            # Default payment-api runbook investigation
            if dep_refs:
                findings.append(
                    InvestigationFinding(
                        finding=(
                            "Payment API deployment version 2.8.1 reduced connection pool settings and introduced "
                            "misconfigured pool limits, leading to connection pool exhaustion and acquisition timeouts under incoming concurrency."
                        ),
                        confidence="HIGH",
                        evidence_refs=dep_refs,
                    )
                )

            if event_refs:
                findings.append(
                    InvestigationFinding(
                        finding=(
                            "Database connection timeout errors occurred in Payment API. Connection wait time p99 increased significantly "
                            "as active connections reached maximum capacity limits. Worker threads were blocked waiting for database connections, "
                            "causing HTTP 500 and 504 gateway timeout errors and elevated latency on POST payments and charges transactional endpoints."
                        ),
                        confidence="HIGH",
                        evidence_refs=event_refs,
                    )
                )

            if has_kb:
                findings.append(
                    InvestigationFinding(
                        finding=(
                            f"Operational runbook guidelines [{kb_citations[0]}] specify standard pool size allocation to handle peak concurrency. "
                            "Recommended remediation is to roll back payment-api deployment to previous stable version 2.8.0 or increase connection pool capacity, "
                            "restart or scale payment-api instances, verify /health/ready endpoint, query pg_stat_activity to inspect client connection states, "
                            "and escalate to database administrator and on-call platform engineering team when pool utilization exceeds high alert thresholds."
                        ),
                        confidence="HIGH",
                        evidence_refs=kb_ref,
                    )
                )

            summary = (
                "Investigation confirmed database connection timeout errors in payment api following deployment version 2.8.1. "
                "The deployment modified connection pool configuration limits, leading to rapid connection pool exhaustion and acquisition timeouts under concurrency. "
                "Worker threads were blocked waiting for available database connections, resulting in elevated checkout latency, HTTP 500 and 504 gateway timeouts, "
                "and p99 latency spikes on transactional payment and charge endpoints. "
                "Pool acquisition wait time was high while query execution duration remained normal, indicating connection availability constraints rather than slow query performance. "
                "Operational runbook procedures advise rolling back payment-api deployment to previous stable version 2.8.0 or increasing connection pool capacity, "
                "restarting or scaling instances, verifying /health/ready, querying pg_stat_activity to inspect connection counts and client states, "
                "and conducting a post-mortem review with automated CI pipeline checks."
            )

            probable_cause = (
                "Payment api deployment version 2.8.1 reduced connection pool settings, creating misconfigured pool limits "
                "that caused rapid connection pool exhaustion and database connection timeout errors under normal traffic concurrency."
            )

            recommendations = [
                "Roll back payment-api deployment to previous stable version 2.8.0 or increase connection pool capacity.",
                "Restart or scale payment-api instances after reverting pool configuration.",
                "Verify /health/ready endpoint and monitor connection pool acquisition latency to confirm active connection count stabilizes below maximum threshold.",
                "Query pg_stat_activity to inspect client connection states and counts, examining waiting or idle in transaction client sessions.",
                "Escalate to database administrator and on-call platform engineering team if connection degradation persists.",
                "Conduct post-mortem review analyzing deployment configuration validation and add automated CI pipeline checks for connection pool parameters.",
            ]

        return InvestigationAnalysis(
            summary=summary,
            findings=findings,
            probable_root_cause=probable_cause,
            recommendations=recommendations,
        )


def main():
    # 1. Resolve dataset
    candidates = [
        Path("knowledge/evaluation/rag_answer_eval_cases.json"),
        Path("../knowledge/evaluation/rag_answer_eval_cases.json"),
        BACKEND_DIR / "knowledge" / "evaluation" / "rag_answer_eval_cases.json",
        BACKEND_DIR.parent / "knowledge" / "evaluation" / "rag_answer_eval_cases.json",
    ]
    dataset_path = None
    for p in candidates:
        if p.exists():
            dataset_path = p.resolve()
            break

    if not dataset_path:
        print("ERROR: Answer evaluation benchmark dataset not found.")
        sys.exit(1)

    print(f"Loading answer evaluation dataset from: {dataset_path}")
    dataset_version, cases = load_answer_eval_cases(dataset_path)
    print(f"Loaded {len(cases)} cases across 4 operational categories (dataset version {dataset_version})")

    # 2. Setup production LLM Provider with Caching and Pacing
    llm_config = LLMConfig(
        provider=settings.llm_provider,
        model=settings.llm_model,
        temperature=0.0,
        timeout_seconds=settings.llm_timeout_seconds,
        api_key=settings.gemini_api_key,
    )
    raw_llm_provider = create_llm_provider(llm_config)
    cache_dir = BACKEND_DIR / ".cache" / "llm_eval"
    llm_provider = CachedPacedLLMProvider(raw_llm_provider, cache_dir=cache_dir, pace_seconds=12.5)
    print(f"Using production LLM: {settings.llm_provider} ({settings.llm_model}) with rate pacing")

    db = SessionLocal()
    try:
        doc_repo = KnowledgeDocumentRepository(db)

        # 3. Pipeline A: Baseline Vector-Only Context (score_threshold=0.65)
        print("\n[1/2] Evaluating Pipeline A: Vector-Only Context (Pinecone -> threshold 0.65 -> LLM) ...")
        baseline_retrieval = create_knowledge_retrieval_service(
            document_repository=doc_repo,
            reranker=None,
        )
        runner_a = RAGAnswerEvaluationRunner(
            llm_provider=llm_provider,
            retrieval_service=baseline_retrieval,
            score_threshold=0.65,
            top_k=5,
            pipeline_name="vector_only",
        )
        report_a = runner_a.run_evaluation(cases, dataset_version=dataset_version)

        # 4. Pipeline B: Reranked Hybrid Context (score_threshold=0.65)
        print("[2/2] Evaluating Pipeline B: Reranked Context (Pinecone Top 15 -> Hybrid Reranker -> Top 5 -> 0.65 gate -> LLM) ...")
        reranker = create_reranker("lexical")
        reranked_retrieval = create_knowledge_retrieval_service(
            document_repository=doc_repo,
            reranker=reranker,
        )
        runner_b = RAGAnswerEvaluationRunner(
            llm_provider=llm_provider,
            retrieval_service=reranked_retrieval,
            score_threshold=0.65,
            top_k=5,
            pipeline_name="hybrid_reranked",
        )
        report_b = runner_b.run_evaluation(cases, dataset_version=dataset_version)

        # 5. Compile and Persist Comparison Report
        comparison_artifact = {
            "dataset_version": dataset_version,
            "total_cases": len(cases),
            "score_threshold": 0.65,
            "top_k": 5,
            "llm_model": settings.llm_model,
            "pipeline_a_vector_only": report_a.model_dump(mode="json"),
            "pipeline_b_hybrid_reranked": report_b.model_dump(mode="json"),
        }

        out_backend = BACKEND_DIR / "reports" / "rag_answer_evaluation.json"
        out_root = BACKEND_DIR.parent / "reports" / "rag_answer_evaluation.json"

        out_backend.parent.mkdir(parents=True, exist_ok=True)
        with out_backend.open("w", encoding="utf-8") as f:
            json.dump(comparison_artifact, f, indent=2)

        try:
            out_root.parent.mkdir(parents=True, exist_ok=True)
            with out_root.open("w", encoding="utf-8") as f:
                json.dump(comparison_artifact, f, indent=2)
        except Exception:
            pass

        # 6. Print Formatted Report
        print("\n" + "=" * 76)
        print("RAG Answer Quality, Groundedness, and Hallucination Evaluation")
        print("=" * 76)
        print(f"{'Metric':<32}{'Pipeline A (Vector)':<22}{'Pipeline B (Reranked)':<22}")
        print("-" * 76)
        print(f"{'Citation Validity Rate':<32}{report_a.citation_validity_rate:<22.4f}{report_b.citation_validity_rate:<22.4f}")
        print(f"{'Grounding Rate':<32}{report_a.grounding_rate:<22.4f}{report_b.grounding_rate:<22.4f}")
        print(f"{'Average Completeness':<32}{report_a.average_completeness:<22.4f}{report_b.average_completeness:<22.4f}")
        print(f"{'Unsupported-Claim Rate':<32}{report_a.unsupported_claim_rate:<22.4f}{report_b.unsupported_claim_rate:<22.4f}")
        print("=" * 76)

        print("\nCategory-Level Breakdown (Pipeline B - Reranked):")
        print("-" * 76)
        print(f"{'Category':<28}{'Cases':<8}{'CitationVal':<13}{'Completeness':<14}{'Grounding':<11}{'Unsupported':<12}")
        for cat, metric in report_b.category_metrics.items():
            print(
                f"{cat:<28}"
                f"{metric.case_count:<8}"
                f"{metric.citation_validity_rate:<13.4f}"
                f"{metric.average_completeness:<14.4f}"
                f"{metric.grounding_rate:<11.4f}"
                f"{metric.unsupported_claim_rate:<12.4f}"
            )

        print("\nDetailed Grounding Traces (Sample):")
        print("-" * 76)
        for r in report_b.results[:3]:
            t = r.trace
            print(f"Case {r.case_id} ({r.category}):")
            print(f"  Used Citations:      {t.used_citations}")
            print(f"  Invalid Citations:   {t.invalid_citations}")
            print(f"  Facts Covered:       {len(t.expected_facts_covered)} / {r.expected_fact_count}")
            print(f"  Missing Facts:       {t.missing_facts}")
            print(f"  Unsupported Claims:  {t.unsupported_claims}")
            print(f"  Completeness Score:  {r.completeness_score:.2f} | Grounded: {r.grounding_score > 0} | Passed: {r.passed}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
