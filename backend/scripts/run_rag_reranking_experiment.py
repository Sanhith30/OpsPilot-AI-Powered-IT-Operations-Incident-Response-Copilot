import json
import os
import sys
from pathlib import Path

# Add backend directory to sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.ai.rag.evaluation.runner import RAGEvaluationRunner, load_eval_cases
from app.ai.rag.reranking.factory import create_reranker
from app.ai.rag.retrieval.factory import create_knowledge_retrieval_service
from app.db.session import SessionLocal
from app.repositories.knowledge_document_repository import (
    KnowledgeDocumentRepository,
)


def main():
    # 1. Resolve dataset
    candidates = [
        Path("knowledge/evaluation/rag_eval_cases.json"),
        Path("../knowledge/evaluation/rag_eval_cases.json"),
        BACKEND_DIR / "knowledge" / "evaluation" / "rag_eval_cases.json",
        BACKEND_DIR.parent / "knowledge" / "evaluation" / "rag_eval_cases.json",
    ]
    dataset_path = None
    for p in candidates:
        if p.exists():
            dataset_path = p.resolve()
            break

    if not dataset_path:
        print("ERROR: Evaluation cases dataset not found.")
        sys.exit(1)

    print(f"Loading evaluation dataset from: {dataset_path}")
    dataset_version, cases = load_eval_cases(dataset_path)
    print(f"Loaded {len(cases)} cases (dataset version {dataset_version})")

    db = SessionLocal()
    try:
        doc_repo = KnowledgeDocumentRepository(db)

        # Baseline: Pinecone alone with score_threshold=0.65
        print("\n[1/2] Running Baseline: Pinecone -> threshold 0.65 ...")
        baseline_retrieval_service = create_knowledge_retrieval_service(
            document_repository=doc_repo,
            reranker=None,
        )
        baseline_runner = RAGEvaluationRunner(
            retrieval_service=baseline_retrieval_service,
            top_k=5,
            score_threshold=0.65,
            embedding_model="gemini-embedding-2",
            embedding_dimensions=1536,
        )
        baseline_report = baseline_runner.run_evaluation(
            cases,
            dataset_version=dataset_version,
        )

        # Experiment: Pinecone -> rerank -> threshold 0.65
        print("[2/2] Running Experiment: Pinecone -> Rerank -> threshold 0.65 ...")
        reranker = create_reranker("lexical")
        rerank_retrieval_service = create_knowledge_retrieval_service(
            document_repository=doc_repo,
            reranker=reranker,
        )
        rerank_runner = RAGEvaluationRunner(
            retrieval_service=rerank_retrieval_service,
            top_k=5,
            score_threshold=0.65,
            embedding_model="gemini-embedding-2",
            embedding_dimensions=1536,
        )
        rerank_report = rerank_runner.run_evaluation(
            cases,
            dataset_version=dataset_version,
        )

        # Compile comparison report
        comparison = {
            "dataset_version": dataset_version,
            "score_threshold": 0.65,
            "top_k": 5,
            "embedding_model": "gemini-embedding-2",
            "baseline": {
                "name": "Pinecone Vector Search (Threshold 0.65)",
                "positive_recall_at_5": baseline_report.positive_cases.recall_at_k,
                "positive_precision_at_5": baseline_report.positive_cases.precision_at_k,
                "positive_mrr": baseline_report.positive_cases.mrr,
                "document_metrics": {
                    "recall_at_5": baseline_report.document_metrics.recall_at_k if baseline_report.document_metrics else baseline_report.positive_cases.recall_at_k,
                    "precision_at_5": baseline_report.document_metrics.precision_at_k if baseline_report.document_metrics else baseline_report.positive_cases.precision_at_k,
                    "mrr": baseline_report.document_metrics.mrr if baseline_report.document_metrics else baseline_report.positive_cases.mrr,
                },
                "chunk_metrics": {
                    "recall_at_5": baseline_report.chunk_metrics.recall_at_k if baseline_report.chunk_metrics else baseline_report.positive_cases.recall_at_k,
                    "precision_at_5": baseline_report.chunk_metrics.precision_at_k if baseline_report.chunk_metrics else baseline_report.positive_cases.precision_at_k,
                    "mrr": baseline_report.chunk_metrics.mrr if baseline_report.chunk_metrics else baseline_report.positive_cases.mrr,
                },
                "unwanted_retrieval_rate": baseline_report.negative_controls.unwanted_retrieval_rate,
                "clean_rejection_rate": baseline_report.negative_controls.clean_rejection_rate,
                "authorization_accuracy": baseline_report.authorization_cases.authorization_accuracy,
                "unauthorized_leakage_rate": baseline_report.authorization_cases.unauthorized_leakage_rate,
                "grounding_rate": baseline_report.grounding.citation_grounding_rate,
            },
            "reranked_experiment": {
                "name": "Pinecone + Deterministic Lexical Reranker (Threshold 0.65)",
                "positive_recall_at_5": rerank_report.positive_cases.recall_at_k,
                "positive_precision_at_5": rerank_report.positive_cases.precision_at_k,
                "positive_mrr": rerank_report.positive_cases.mrr,
                "document_metrics": {
                    "recall_at_5": rerank_report.document_metrics.recall_at_k if rerank_report.document_metrics else rerank_report.positive_cases.recall_at_k,
                    "precision_at_5": rerank_report.document_metrics.precision_at_k if rerank_report.document_metrics else rerank_report.positive_cases.precision_at_k,
                    "mrr": rerank_report.document_metrics.mrr if rerank_report.document_metrics else rerank_report.positive_cases.mrr,
                },
                "chunk_metrics": {
                    "recall_at_5": rerank_report.chunk_metrics.recall_at_k if rerank_report.chunk_metrics else rerank_report.positive_cases.recall_at_k,
                    "precision_at_5": rerank_report.chunk_metrics.precision_at_k if rerank_report.chunk_metrics else rerank_report.positive_cases.precision_at_k,
                    "mrr": rerank_report.chunk_metrics.mrr if rerank_report.chunk_metrics else rerank_report.positive_cases.mrr,
                },
                "unwanted_retrieval_rate": rerank_report.negative_controls.unwanted_retrieval_rate,
                "clean_rejection_rate": rerank_report.negative_controls.clean_rejection_rate,
                "authorization_accuracy": rerank_report.authorization_cases.authorization_accuracy,
                "unauthorized_leakage_rate": rerank_report.authorization_cases.unauthorized_leakage_rate,
                "grounding_rate": rerank_report.grounding.citation_grounding_rate,
            },
        }

        # Persist report
        report_path_backend = BACKEND_DIR / "reports" / "rag_reranking_experiment.json"
        report_path_root = BACKEND_DIR.parent / "reports" / "rag_reranking_experiment.json"

        report_path_backend.parent.mkdir(parents=True, exist_ok=True)
        with report_path_backend.open("w", encoding="utf-8") as f:
            json.dump(comparison, f, indent=2)

        try:
            report_path_root.parent.mkdir(parents=True, exist_ok=True)
            with report_path_root.open("w", encoding="utf-8") as f:
                json.dump(comparison, f, indent=2)
        except Exception:
            pass

        # Persist Step 17.19/17.21 Multi-Document Baseline Snapshot
        from sqlalchemy import func
        from app.models.knowledge_document import KnowledgeDocument
        from app.models.knowledge_document_version import KnowledgeDocumentVersion

        doc_count = db.query(KnowledgeDocument).filter(KnowledgeDocument.status == "ACTIVE").count()
        chunk_count = db.query(func.sum(KnowledgeDocumentVersion.chunk_count)).filter(
            KnowledgeDocumentVersion.ingestion_status == "COMPLETED"
        ).scalar() or 0

        multidoc_baseline = {
            "dataset_version": dataset_version,
            "document_count": doc_count,
            "chunk_count": int(chunk_count),
            "embedding_model": "gemini-embedding-2",
            "embedding_dimensions": 1536,
            "threshold": 0.65,
            "candidate_k": 15,
            "final_k": 5,
            "reranker": "lexical",
            "chunk_metrics": {
                "vector_only": {
                    "recall_at_5": baseline_report.chunk_metrics.recall_at_k if baseline_report.chunk_metrics else baseline_report.positive_cases.recall_at_k,
                    "precision_at_5": baseline_report.chunk_metrics.precision_at_k if baseline_report.chunk_metrics else baseline_report.positive_cases.precision_at_k,
                    "mrr": baseline_report.chunk_metrics.mrr if baseline_report.chunk_metrics else baseline_report.positive_cases.mrr,
                },
                "hybrid_reranked": {
                    "recall_at_5": rerank_report.chunk_metrics.recall_at_k if rerank_report.chunk_metrics else rerank_report.positive_cases.recall_at_k,
                    "precision_at_5": rerank_report.chunk_metrics.precision_at_k if rerank_report.chunk_metrics else rerank_report.positive_cases.precision_at_k,
                    "mrr": rerank_report.chunk_metrics.mrr if rerank_report.chunk_metrics else rerank_report.positive_cases.mrr,
                }
            },
            "document_metrics": {
                "vector_only": {
                    "recall_at_5": baseline_report.document_metrics.recall_at_k if baseline_report.document_metrics else baseline_report.positive_cases.recall_at_k,
                    "precision_at_5": baseline_report.document_metrics.precision_at_k if baseline_report.document_metrics else baseline_report.positive_cases.precision_at_k,
                    "mrr": baseline_report.document_metrics.mrr if baseline_report.document_metrics else baseline_report.positive_cases.mrr,
                },
                "hybrid_reranked": {
                    "recall_at_5": rerank_report.document_metrics.recall_at_k if rerank_report.document_metrics else rerank_report.positive_cases.recall_at_k,
                    "precision_at_5": rerank_report.document_metrics.precision_at_k if rerank_report.document_metrics else rerank_report.positive_cases.precision_at_k,
                    "mrr": rerank_report.document_metrics.mrr if rerank_report.document_metrics else rerank_report.positive_cases.mrr,
                }
            },
            "vector_only": {
                "recall_at_5": baseline_report.positive_cases.recall_at_k,
                "precision_at_5": baseline_report.positive_cases.precision_at_k,
                "mrr": baseline_report.positive_cases.mrr,
                "unwanted_retrieval": baseline_report.negative_controls.unwanted_retrieval_rate,
                "clean_rejection": baseline_report.negative_controls.clean_rejection_rate,
                "authorization_accuracy": baseline_report.authorization_cases.authorization_accuracy,
                "authorization_leakage": baseline_report.authorization_cases.unauthorized_leakage_rate,
                "grounding": baseline_report.grounding.citation_grounding_rate,
            },
            "hybrid_reranked": {
                "recall_at_5": rerank_report.positive_cases.recall_at_k,
                "precision_at_5": rerank_report.positive_cases.precision_at_k,
                "mrr": rerank_report.positive_cases.mrr,
                "unwanted_retrieval": rerank_report.negative_controls.unwanted_retrieval_rate,
                "clean_rejection": rerank_report.negative_controls.clean_rejection_rate,
                "authorization_accuracy": rerank_report.authorization_cases.authorization_accuracy,
                "authorization_leakage": rerank_report.authorization_cases.unauthorized_leakage_rate,
                "grounding": rerank_report.grounding.citation_grounding_rate,
            }
        }

        baseline_out_backend = BACKEND_DIR / "reports" / "rag_multidoc_baseline.json"
        baseline_out_root = BACKEND_DIR.parent / "reports" / "rag_multidoc_baseline.json"
        with baseline_out_backend.open("w", encoding="utf-8") as f:
            json.dump(multidoc_baseline, f, indent=2)
        try:
            with baseline_out_root.open("w", encoding="utf-8") as f:
                json.dump(multidoc_baseline, f, indent=2)
        except Exception:
            pass

        print("\n" + "=" * 70)
        print("RAG Reranking Evaluation Experiment Comparison")
        print("=" * 70)
        print(f"{'Metric':<28}{'Baseline (Vector)':<22}{'Reranked (Hybrid)':<20}")
        print("-" * 70)
        b_doc = baseline_report.document_metrics or baseline_report.positive_cases
        r_doc = rerank_report.document_metrics or rerank_report.positive_cases
        b_chk = baseline_report.chunk_metrics or baseline_report.positive_cases
        r_chk = rerank_report.chunk_metrics or rerank_report.positive_cases

        print(f"{'Document Recall@5':<28}{b_doc.recall_at_k:<22.4f}{r_doc.recall_at_k:<20.4f}")
        print(f"{'Document Precision@5':<28}{b_doc.precision_at_k:<22.4f}{r_doc.precision_at_k:<20.4f}")
        print(f"{'Document MRR':<28}{b_doc.mrr:<22.4f}{r_doc.mrr:<20.4f}")
        print(f"{'Chunk Recall@5':<28}{b_chk.recall_at_k:<22.4f}{r_chk.recall_at_k:<20.4f}")
        print(f"{'Chunk Precision@5':<28}{b_chk.precision_at_k:<22.4f}{r_chk.precision_at_k:<20.4f}")
        print(f"{'Chunk MRR':<28}{b_chk.mrr:<22.4f}{r_chk.mrr:<20.4f}")
        print(f"{'Unwanted Retrieval Rate':<28}{baseline_report.negative_controls.unwanted_retrieval_rate:<22.4f}{rerank_report.negative_controls.unwanted_retrieval_rate:<20.4f}")
        print(f"{'Clean Rejection Rate':<28}{baseline_report.negative_controls.clean_rejection_rate:<22.4f}{rerank_report.negative_controls.clean_rejection_rate:<20.4f}")
        print(f"{'Authorization Accuracy':<28}{baseline_report.authorization_cases.authorization_accuracy:<22.4f}{rerank_report.authorization_cases.authorization_accuracy:<20.4f}")
        print(f"{'Unauthorized Leakage':<28}{baseline_report.authorization_cases.unauthorized_leakage_rate:<22.4f}{rerank_report.authorization_cases.unauthorized_leakage_rate:<20.4f}")
        print("=" * 70)


    finally:
        db.close()


if __name__ == "__main__":
    main()
