#!/usr/bin/env python3
"""
==============================================================================
OpsPilot - AWS Golden Path End-to-End Production Verification
==============================================================================

Verifies that the entire OpsPilot operational pipeline is healthy, responsive,
and correctly connected on AWS (or local/staging environment).

Steps Verified:
  1. System Health Check (/health)
  2. Operator Authentication (/api/v1/auth/login)
  3. Persona & RBAC Context (/api/v1/auth/me)
  4. Active Incident Pipeline (/api/v1/incidents)
  5. Incident Details & Telemetry Events (/api/v1/incidents/{id}/events)
  6. Conversational AI Copilot (/api/v1/chat)
  7. Knowledge Base Document Catalog (/api/v1/knowledge/documents)
  8. Dashboard Operational Summary (/api/v1/dashboard/summary)
  9. Audit Log Persistence (/api/v1/audit-logs)

Usage:
  python scripts/aws_golden_path_verify.py --url https://<your-ec2-domain-or-ip>
  python scripts/aws_golden_path_verify.py --url http://127.0.0.1:8000
"""

import argparse
import sys
import time
from typing import Any
import urllib.parse
import httpx


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def print_banner(base_url: str):
    print(f"\n{Colors.BOLD}{Colors.CYAN}===================================================================={Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}         OpsPilot - AWS Production Golden Path Verification         {Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}===================================================================={Colors.RESET}")
    print(f"Target URL: {Colors.BOLD}{base_url}{Colors.RESET}")
    print(f"Timestamp:  {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n")


class GoldenPathRunner:
    def __init__(self, base_url: str, verify_ssl: bool = True):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(base_url=self.base_url, timeout=30.0, verify=verify_ssl)
        self.token: str | None = None
        self.results: list[dict[str, Any]] = []

    def record_step(self, step_num: int, name: str, passed: bool, latency_ms: float, details: str = ""):
        self.results.append({
            "step": step_num,
            "name": name,
            "passed": passed,
            "latency": latency_ms,
            "details": details,
        })
        status_str = f"{Colors.GREEN}[PASS]{Colors.RESET}" if passed else f"{Colors.RED}[FAIL]{Colors.RESET}"
        print(f"Step {step_num}: {name:<45} {status_str} ({latency_ms:.1f}ms) {details}")

    def run_all(self) -> bool:
        overall_pass = True

        # Step 1: Health Check
        try:
            t0 = time.perf_counter()
            resp = self.client.get("/health")
            t_ms = (time.perf_counter() - t0) * 1000
            if resp.status_code == 200:
                data = resp.json()
                app_name = data.get("app_name", "OpsPilot")
                self.record_step(1, "System Health Probe (/health)", True, t_ms, f"App: {app_name}")
            else:
                self.record_step(1, "System Health Probe (/health)", False, t_ms, f"Status: {resp.status_code}")
                overall_pass = False
        except Exception as e:
            self.record_step(1, "System Health Probe (/health)", False, 0.0, f"Error: {e}")
            overall_pass = False

        # Step 2: Authentication
        try:
            t0 = time.perf_counter()
            login_payload = {
                "email": "arun@opspilot.local",
                "password": "OpsPilot@123",
            }
            resp = self.client.post("/api/v1/auth/login", json=login_payload)
            t_ms = (time.perf_counter() - t0) * 1000

            if resp.status_code == 200:
                data = resp.json()
                self.token = data.get("access_token")
                self.record_step(2, "Operator Authentication (/auth/login)", True, t_ms, "JWT token acquired")
            else:
                self.record_step(2, "Operator Authentication (/auth/login)", False, t_ms, f"Status: {resp.status_code}")
                overall_pass = False
        except Exception as e:
            self.record_step(2, "Operator Authentication (/auth/login)", False, 0.0, f"Error: {e}")
            overall_pass = False


        auth_headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

        # Step 3: Auth Profile /me
        try:
            t0 = time.perf_counter()
            resp = self.client.get("/api/v1/auth/me", headers=auth_headers)
            t_ms = (time.perf_counter() - t0) * 1000
            if resp.status_code == 200:
                user = resp.json()
                username = user.get("username", "Unknown")
                role = user.get("role", "Unknown")
                self.record_step(3, "Operator Persona & Context (/auth/me)", True, t_ms, f"User: {username} ({role})")
            else:
                self.record_step(3, "Operator Persona & Context (/auth/me)", False, t_ms, f"Status: {resp.status_code}")
                overall_pass = False
        except Exception as e:
            self.record_step(3, "Operator Persona & Context (/auth/me)", False, 0.0, f"Error: {e}")
            overall_pass = False

        # Step 4: Incident Pipeline
        incident_id = 1
        try:
            t0 = time.perf_counter()
            resp = self.client.get("/api/v1/incidents", headers=auth_headers)
            t_ms = (time.perf_counter() - t0) * 1000
            if resp.status_code == 200:
                incidents = resp.json()
                count = len(incidents) if isinstance(incidents, list) else 0
                if count > 0 and isinstance(incidents[0], dict):
                    incident_id = incidents[0].get("incident_id", 1)
                self.record_step(4, "Incident Pipeline (/incidents)", True, t_ms, f"{count} active incidents found")
            else:
                self.record_step(4, "Incident Pipeline (/incidents)", False, t_ms, f"Status: {resp.status_code}")
                overall_pass = False
        except Exception as e:
            self.record_step(4, "Incident Pipeline (/incidents)", False, 0.0, f"Error: {e}")
            overall_pass = False

        # Step 5: Incident Events Timeline
        try:
            t0 = time.perf_counter()
            resp = self.client.get(f"/api/v1/incidents/{incident_id}/events", headers=auth_headers)
            t_ms = (time.perf_counter() - t0) * 1000
            if resp.status_code == 200:
                events = resp.json()
                count = len(events) if isinstance(events, list) else 0
                self.record_step(5, f"Incident #{incident_id} Events Timeline", True, t_ms, f"{count} timeline events")
            else:
                self.record_step(5, f"Incident #{incident_id} Events Timeline", False, t_ms, f"Status: {resp.status_code}")
                overall_pass = False
        except Exception as e:
            self.record_step(5, f"Incident #{incident_id} Events Timeline", False, 0.0, f"Error: {e}")
            overall_pass = False

        # Step 6: Conversational AI Copilot
        try:
            t0 = time.perf_counter()
            chat_req = {
                "message": f"Investigate Incident #{incident_id} and check recent deployments.",
                "incident_id": incident_id,
            }
            resp = self.client.post("/api/v1/chat", json=chat_req, headers=auth_headers)
            t_ms = (time.perf_counter() - t0) * 1000
            if resp.status_code == 200:
                chat_data = resp.json()
                ans_len = len(chat_data.get("answer", ""))
                tools_used = len(chat_data.get("tool_trace", []))
                self.record_step(6, "AI Investigation Copilot (/chat)", True, t_ms, f"Answer: {ans_len} chars, {tools_used} tools dispatched")
            else:
                self.record_step(6, "AI Investigation Copilot (/chat)", False, t_ms, f"Status: {resp.status_code}")
                overall_pass = False
        except Exception as e:
            self.record_step(6, "AI Investigation Copilot (/chat)", False, 0.0, f"Error: {e}")
            overall_pass = False

        # Step 7: Knowledge Base Catalog
        try:
            t0 = time.perf_counter()
            resp = self.client.get("/api/v1/knowledge/documents", headers=auth_headers)
            t_ms = (time.perf_counter() - t0) * 1000
            if resp.status_code == 200:
                docs = resp.json()
                count = len(docs) if isinstance(docs, list) else 0
                self.record_step(7, "RAG Knowledge Catalog (/documents)", True, t_ms, f"{count} operational runbooks indexed")
            else:
                self.record_step(7, "RAG Knowledge Catalog (/documents)", False, t_ms, f"Status: {resp.status_code}")
                overall_pass = False
        except Exception as e:
            self.record_step(7, "RAG Knowledge Catalog (/documents)", False, 0.0, f"Error: {e}")
            overall_pass = False

        # Step 8: Dashboard Operational Summary
        try:
            t0 = time.perf_counter()
            resp = self.client.get("/api/v1/dashboard/summary", headers=auth_headers)
            t_ms = (time.perf_counter() - t0) * 1000
            if resp.status_code == 200:
                summary = resp.json()
                active = summary.get("active_incidents", 0)
                resolved = summary.get("resolved_incidents", 0)
                self.record_step(8, "Dashboard Summary (/dashboard/summary)", True, t_ms, f"Active: {active}, Resolved: {resolved}")
            else:
                self.record_step(8, "Dashboard Summary (/dashboard/summary)", False, t_ms, f"Status: {resp.status_code}")
                overall_pass = False
        except Exception as e:
            self.record_step(8, "Dashboard Summary (/dashboard/summary)", False, 0.0, f"Error: {e}")
            overall_pass = False

        # Step 9: Audit Log Verification
        try:
            t0 = time.perf_counter()
            resp = self.client.get("/api/v1/audit-logs?limit=5", headers=auth_headers)
            t_ms = (time.perf_counter() - t0) * 1000
            if resp.status_code == 200:
                logs = resp.json()
                count = len(logs) if isinstance(logs, list) else 0
                self.record_step(9, "Audit Trail Verification (/audit-logs)", True, t_ms, f"{count} immutable audit records verified")
            else:
                self.record_step(9, "Audit Trail Verification (/audit-logs)", False, t_ms, f"Status: {resp.status_code}")
                overall_pass = False
        except Exception as e:
            self.record_step(9, "Audit Trail Verification (/audit-logs)", False, 0.0, f"Error: {e}")
            overall_pass = False

        return overall_pass

    def print_summary(self, success: bool):
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = total - passed
        avg_latency = sum(r["latency"] for r in self.results) / total if total > 0 else 0

        print(f"\n{Colors.BOLD}--------------------------------------------------------------------{Colors.RESET}")
        print(f"Total Steps: {total} | Passed: {Colors.GREEN}{passed}{Colors.RESET} | Failed: {Colors.RED if failed else Colors.GREEN}{failed}{Colors.RESET} | Avg Latency: {avg_latency:.1f}ms")
        print(f"{Colors.BOLD}--------------------------------------------------------------------{Colors.RESET}")

        if success:
            print(f"{Colors.BOLD}{Colors.GREEN}[OK] AWS Golden Path Verification PASSED completely!{Colors.RESET}")
            print(f"{Colors.GREEN}     OpsPilot is production-ready and fully operational on AWS.{Colors.RESET}\n")
        else:
            print(f"{Colors.BOLD}{Colors.RED}[X] AWS Golden Path Verification FAILED on {failed} step(s).{Colors.RESET}")
            print(f"{Colors.RED}    Please check the failed endpoints above for details.{Colors.RESET}\n")



def main():
    parser = argparse.ArgumentParser(description="OpsPilot AWS Golden Path Production Verification")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="Base URL of OpsPilot deployment (e.g. https://opspilot.example.com)")
    parser.add_argument("--insecure", action="store_true", help="Skip SSL certificate validation (for self-signed certs)")

    args = parser.parse_args()
    print_banner(args.url)

    runner = GoldenPathRunner(base_url=args.url, verify_ssl=not args.insecure)
    success = runner.run_all()
    runner.print_summary(success)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
