import os
import sys
from pathlib import Path

# Add backend directory to sys.path so app modules are resolvable
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.ai.rag.evaluation.runner import load_eval_cases
from app.ai.rag.evaluation.threshold_runner import RAGThresholdSweepRunner
from app.ai.rag.retrieval.factory import create_knowledge_retrieval_service
from app.db.session import SessionLocal
from app.repositories.knowledge_document_repository import (
    KnowledgeDocumentRepository,
)


def main():
    # 1. Resolve dataset path
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
        print("ERROR: Evaluation cases dataset not found in expected locations.")
        sys.exit(1)

    print(f"Loading evaluation dataset from: {dataset_path}")
    dataset_version, cases = load_eval_cases(dataset_path)
    print(f"Loaded {len(cases)} cases (dataset version {dataset_version})")

    # 2. Setup retrieval service
    db = SessionLocal()
    try:
        doc_repo = KnowledgeDocumentRepository(db)
        retrieval_service = create_knowledge_retrieval_service(
            document_repository=doc_repo
        )

        thresholds = [0.25, 0.35, 0.45, 0.55, 0.65, 0.75]
        runner = RAGThresholdSweepRunner(
            retrieval_service=retrieval_service,
            top_k=5,
            embedding_model="gemini-embedding-2",
            embedding_dimensions=1536,
        )

        # Output paths
        output_report_backend = BACKEND_DIR / "reports" / "rag_threshold_sweep.json"
        output_report_root = BACKEND_DIR.parent / "reports" / "rag_threshold_sweep.json"

        print("Executing RAG threshold sweep across:", thresholds)
        report = runner.run_sweep(
            cases,
            dataset_version=dataset_version,
            thresholds=thresholds,
            output_path=output_report_backend,
        )

        # Also save to root reports directory
        try:
            output_report_root.parent.mkdir(parents=True, exist_ok=True)
            output_report_root.write_text(
                report.model_dump_json(indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            print(f"Notice: Could not write to root reports: {e}")

        # 3. Print formatted results
        print("\nRAG Threshold Sweep")
        print("===================")
        print(f"{'Threshold':<11}{'Recall@5':<11}{'Precision@5':<14}{'MRR':<8}{'Unwanted':<11}{'CleanReject':<13}{'AuthAcc':<10}{'Leakage':<9}")
        for p in report.thresholds:
            print(
                f"{p.threshold:<11.2f}"
                f"{p.positive_recall_at_k:<11.4f}"
                f"{p.positive_precision_at_k:<14.4f}"
                f"{p.positive_mrr:<8.4f}"
                f"{p.unwanted_retrieval_rate:<11.4f}"
                f"{p.clean_rejection_rate:<13.4f}"
                f"{p.authorization_accuracy:<10.4f}"
                f"{p.unauthorized_leakage_rate:<9.4f}"
            )

        print("\nScore Distributions")
        print("-------------------")
        for p in report.thresholds:
            pos_dist = p.positive_score_distribution
            neg_dist = p.negative_score_distribution
            pos_str = (
                f"min={pos_dist.min_score}, max={pos_dist.max_score}, mean={pos_dist.mean_score} (N={pos_dist.sample_count})"
                if pos_dist.sample_count > 0
                else "No docs retrieved"
            )
            neg_str = (
                f"min={neg_dist.min_score}, max={neg_dist.max_score}, mean={neg_dist.mean_score} (N={neg_dist.sample_count})"
                if neg_dist.sample_count > 0
                else "No docs retrieved"
            )
            print(f"Threshold {p.threshold:.2f}:")
            print(f"  Positive cases:   {pos_str}")
            print(f"  Negative control: {neg_str}")

        print(f"\nSelected threshold: {report.selected_threshold}")
        print(f"Reason: {report.selection_reason}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
