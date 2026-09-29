#!/usr/bin/env python3
"""
OpsPilot Production Deployment Verification & Smoke Test Script
Executes automated health and endpoint probes against a deployed instance.
Returns exit code 0 on success, 1 on failure (triggering automated CI/CD rollback).
"""

from __future__ import annotations

import argparse
import sys
import time
import httpx


def verify_deployment(base_url: str, retries: int = 10, delay: int = 10) -> bool:
    client = httpx.Client(timeout=15.0, verify=False, follow_redirects=True)
    base_url = base_url.rstrip("/")
    print(f"[*] Starting deployment verification against: {base_url}")

    for attempt in range(1, retries + 1):
        print(f"\n[Attempt {attempt}/{retries}] Probing service endpoints...")
        try:
            # 1. API Health Check
            health_res = client.get(f"{base_url}/health")
            if health_res.status_code != 200 or health_res.json().get("status") != "healthy":
                print(f"[-] /health check failed: {health_res.status_code}")
                time.sleep(delay)
                continue
            print("[+] /health probe passed (200 OK)")

            # 2. Database Connectivity Probe
            db_res = client.get(f"{base_url}/db-health")
            if db_res.status_code != 200 or db_res.json().get("status") != "healthy":
                print(f"[-] /db-health probe failed: {db_res.status_code}")
                time.sleep(delay)
                continue
            print("[+] /db-health probe passed (PostgreSQL connected)")

            # 3. Telemetry / Metrics Probe
            metrics_res = client.get(f"{base_url}/metrics")
            if metrics_res.status_code != 200:
                print(f"[-] /metrics probe failed: {metrics_res.status_code}")
                time.sleep(delay)
                continue
            print("[+] /metrics telemetry probe passed")

            # 4. Security Headers Probe
            headers = health_res.headers
            if headers.get("X-Content-Type-Options") != "nosniff" or headers.get("X-Frame-Options") != "DENY":
                print("[-] OWASP security headers missing or incomplete")
                time.sleep(delay)
                continue
            print("[+] OWASP Security headers verified")

            # 5. Frontend UI Availability Probe
            ui_res = client.get(f"{base_url}/ui/")
            if ui_res.status_code not in (200, 304):
                print(f"[-] Frontend /ui probe returned {ui_res.status_code}")
                time.sleep(delay)
                continue
            print("[+] Frontend UI bundle probe passed")

            print("\n" + "="*60)
            print("[SUCCESS] DEPLOYMENT VERIFICATION SUCCESSFUL: All checks passed!")
            print("="*60)
            return True

        except Exception as exc:
            print(f"[-] Connection attempt failed: {exc}")
            time.sleep(delay)

    print("\n" + "="*60)
    print("[FAILURE] DEPLOYMENT VERIFICATION FAILED after maximum retries!")
    print("="*60)
    return False


def main():
    parser = argparse.ArgumentParser(description="Verify OpsPilot deployment health")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="Base URL of OpsPilot deployment")
    parser.add_argument("--retries", type=int, default=10, help="Maximum probe retry attempts")
    parser.add_argument("--delay", type=int, default=5, help="Delay in seconds between retries")

    args = parser.parse_args()
    success = verify_deployment(base_url=args.url, retries=args.retries, delay=args.delay)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
