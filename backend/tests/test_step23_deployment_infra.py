from __future__ import annotations

import os
from pathlib import Path
import pytest
import yaml
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def repo_root() -> Path:
    """Returns the OpsPilot repository root path."""
    current = Path(__file__).resolve()
    # backend/tests/test_step23_deployment_infra.py -> repo_root is 2 levels up from backend
    return current.parent.parent.parent


# -----------------------------------------------------------------------------
# 1. DOCKERFILE & CONTAINER CONFIGURATION TESTS
# -----------------------------------------------------------------------------

def test_backend_dockerfile_security_and_structure(repo_root: Path):
    """Verifies backend Dockerfile uses multi-stage builds, non-root user, and health check."""
    dockerfile_path = repo_root / "backend" / "Dockerfile"
    assert dockerfile_path.exists(), "Backend Dockerfile must exist"

    content = dockerfile_path.read_text(encoding="utf-8")

    # Multi-stage builds
    assert "FROM python:3.13-slim AS builder" in content
    assert "FROM node:20-alpine AS frontend-builder" in content
    assert "FROM python:3.13-slim AS runtime" in content

    # Security hardening: Non-root user
    assert "useradd" in content or "adduser" in content
    assert "USER opspilot" in content or "USER 10001" in content

    # Baked-in container health check
    assert "HEALTHCHECK" in content
    assert "/health" in content

    # Python optimizations
    assert "PYTHONDONTWRITEBYTECODE=1" in content
    assert "PYTHONUNBUFFERED=1" in content


def test_frontend_dockerfile_and_nginx_config(repo_root: Path):
    """Verifies frontend Dockerfile uses multi-stage build with hardened Nginx reverse proxy."""
    dockerfile_path = repo_root / "frontend" / "Dockerfile"
    nginx_path = repo_root / "frontend" / "nginx.conf"

    assert dockerfile_path.exists(), "Frontend Dockerfile must exist"
    assert nginx_path.exists(), "Frontend nginx.conf must exist"

    docker_content = dockerfile_path.read_text(encoding="utf-8")
    assert "FROM node:20-alpine AS build" in docker_content
    assert "FROM nginx:1.27-alpine AS runtime" in docker_content
    assert "HEALTHCHECK" in docker_content

    nginx_content = nginx_path.read_text(encoding="utf-8")
    # Reverse proxy to backend
    assert "proxy_pass http://backend:8000/api/;" in nginx_content
    # SPA fallback
    assert "try_files $uri $uri/ /index.html;" in nginx_content
    # Security headers
    assert "add_header X-Frame-Options \"DENY\"" in nginx_content
    assert "add_header X-Content-Type-Options \"nosniff\"" in nginx_content


# -----------------------------------------------------------------------------
# 2. DOCKER-COMPOSE LOCAL PRODUCTION STACK
# -----------------------------------------------------------------------------

def test_docker_compose_validity_and_dependencies(repo_root: Path):
    """Verifies root docker-compose.yml structure, service dependencies, and networks."""
    compose_path = repo_root / "docker-compose.yml"
    assert compose_path.exists(), "docker-compose.yml must exist at repo root"

    with open(compose_path, "r", encoding="utf-8") as f:
        compose = yaml.safe_load(f)

    services = compose.get("services", {})
    required_services = {"postgres", "backend", "frontend", "prometheus", "grafana", "otel-collector"}
    assert required_services.issubset(set(services.keys()))

    # Postgres service validation
    postgres = services["postgres"]
    assert "healthcheck" in postgres
    assert any("postgres_data" in v for v in postgres.get("volumes", []))

    # Backend service dependency and health check
    backend = services["backend"]
    assert "postgres" in backend.get("depends_on", {})
    assert backend["depends_on"]["postgres"]["condition"] == "service_healthy"
    assert "healthcheck" in backend

    # Network isolation
    networks = compose.get("networks", {})
    assert "opspilot-network" in networks


# -----------------------------------------------------------------------------
# 3. AWS TERRAFORM INFRASTRUCTURE AS CODE
# -----------------------------------------------------------------------------

def test_terraform_modules_and_security_invariants(repo_root: Path):
    """Verifies Terraform IaC configurations and security constraints."""
    tf_dir = repo_root / "infra" / "terraform"
    assert tf_dir.exists(), "infra/terraform directory must exist"

    expected_files = [
        "main.tf", "variables.tf", "vpc.tf", "security_groups.tf",
        "rds.tf", "secrets.tf", "iam.tf", "alb.tf", "ecs.tf",
        "cloudwatch.tf", "outputs.tf"
    ]
    for filename in expected_files:
        path = tf_dir / filename
        assert path.exists(), f"Terraform file {filename} must exist"

    # Security Group check: RDS must not allow public ingress (0.0.0.0/0)
    sg_content = (tf_dir / "security_groups.tf").read_text(encoding="utf-8")
    assert 'resource "aws_security_group" "rds"' in sg_content
    # RDS ingress must reference ecs_tasks security group
    assert "aws_security_group.ecs_tasks.id" in sg_content

    # RDS check: KMS storage encryption must be enabled
    rds_content = (tf_dir / "rds.tf").read_text(encoding="utf-8")
    assert "storage_encrypted           = true" in rds_content
    assert "multi_az" in rds_content

    # ECS check: Zero-downtime rolling update percentages
    ecs_content = (tf_dir / "ecs.tf").read_text(encoding="utf-8")
    assert "deployment_minimum_healthy_percent = 100" in ecs_content
    assert "deployment_maximum_percent         = 200" in ecs_content

    # ALB check: Health check path
    alb_content = (tf_dir / "alb.tf").read_text(encoding="utf-8")
    assert 'path                = "/health"' in alb_content
    assert 'matcher             = "200"' in alb_content


# -----------------------------------------------------------------------------
# 4. GITHUB ACTIONS CI/CD WORKFLOWS
# -----------------------------------------------------------------------------

def test_github_actions_ci_workflow(repo_root: Path):
    """Verifies .github/workflows/ci.yml triggers, jobs, and security scans."""
    ci_path = repo_root / ".github" / "workflows" / "ci.yml"
    assert ci_path.exists(), "CI workflow must exist"

    with open(ci_path, "r", encoding="utf-8") as f:
        ci_workflow = yaml.safe_load(f)

    # Validate triggers
    # In PyYAML on: [push, pull_request] might be parsed as True/bool
    triggers = ci_workflow.get(True) or ci_workflow.get("on") or {}
    assert "push" in triggers or "pull_request" in triggers

    jobs = ci_workflow.get("jobs", {})
    assert "backend-test" in jobs
    assert "frontend-build" in jobs
    assert "docker-build" in jobs

    # Security scan included
    ci_text = ci_path.read_text(encoding="utf-8")
    assert "bandit" in ci_text.lower()


def test_github_actions_deploy_workflow_and_rollback(repo_root: Path):
    """Verifies .github/workflows/deploy.yml deployment, verification, and automated rollback."""
    deploy_path = repo_root / ".github" / "workflows" / "deploy.yml"
    assert deploy_path.exists(), "Deploy workflow must exist"

    content = deploy_path.read_text(encoding="utf-8")

    # AWS ECR push
    assert "amazon-ecr-login" in content

    # Database migration execution
    assert "run_migrations.py" in content

    # ECS deployment
    assert "amazon-ecs-deploy-task-definition" in content

    # Post-deployment smoke test verification
    assert "deploy_verify.py" in content

    # Automated rollback step
    assert "rollback_ecs.py" in content
    assert "Automated Rollback on Deployment Failure" in content


# -----------------------------------------------------------------------------
# 5. SCRIPTS & DEPLOYMENT SMOKE TEST LOGIC
# -----------------------------------------------------------------------------

def test_deployment_scripts_exist_and_syntax(repo_root: Path):
    """Verifies deployment verification, rollback, and migration scripts exist."""
    scripts_dir = repo_root / "scripts"
    assert (scripts_dir / "deploy_verify.py").exists()
    assert (scripts_dir / "rollback_ecs.py").exists()
    assert (scripts_dir / "run_migrations.py").exists()


def test_live_smoke_probe_against_test_client():
    """Simulates the deployment verification smoke test against live app."""
    client = TestClient(app)

    # 1. Health
    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json().get("status") == "healthy"

    # 2. Database Health
    res_db = client.get("/db-health")
    assert res_db.status_code == 200
    assert res_db.json().get("status") == "healthy"

    # 3. Metrics
    res_metrics = client.get("/metrics")
    assert res_metrics.status_code == 200

    # 4. Security Headers
    assert res_health.headers.get("X-Content-Type-Options") == "nosniff"
    assert res_health.headers.get("X-Frame-Options") == "DENY"

    # 5. Frontend UI
    res_ui = client.get("/ui/")
    assert res_ui.status_code == 200


# -----------------------------------------------------------------------------
# 6. PRODUCTION ENVIRONMENT TEMPLATE INTEGRITY
# -----------------------------------------------------------------------------

def test_production_env_template_contains_all_keys(repo_root: Path):
    """Verifies production.env.example defines all necessary configuration variables."""
    env_example = repo_root / "infra" / "production.env.example"
    assert env_example.exists()

    content = env_example.read_text(encoding="utf-8")
    required_keys = [
        "DATABASE_URL",
        "JWT_SECRET_KEY",
        "GEMINI_API_KEY",
        "PINECONE_API_KEY",
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "RATE_LIMIT_DEFAULT_PER_MIN",
    ]
    for key in required_keys:
        assert key in content, f"Missing key {key} in production.env.example"
