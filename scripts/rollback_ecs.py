#!/usr/bin/env python3
"""
Automated ECS Service Rollback Script
Restores an AWS ECS service to a previously verified stable task definition revision
when post-deployment verification fails.
"""

from __future__ import annotations

import argparse
import sys
import boto3
from botocore.exceptions import ClientError


def rollback_ecs_service(cluster: str, service: str, target_task_def: str) -> bool:
    print(f"[*] Initiating automated rollback for service '{service}' in cluster '{cluster}'...")
    print(f"[*] Target stable Task Definition: {target_task_def}")

    try:
        ecs_client = boto3.client("ecs")

        # 1. Update service to target task definition
        response = ecs_client.update_service(
            cluster=cluster,
            service=service,
            taskDefinition=target_task_def,
            forceNewDeployment=True,
        )
        print("[+] Service updated successfully. Waiting for rollback deployment to stabilize...")

        # 2. Wait for service stability
        waiter = ecs_client.get_waiter("services_stable")
        waiter.wait(
            cluster=cluster,
            services=[service],
            WaiterConfig={"Delay": 15, "MaxAttempts": 40},
        )

        print("[+] Rollback deployment reached stable state.")
        print("=" * 60)
        print("✅ ROLLBACK COMPLETE: System restored to stable revision!")
        print("=" * 60)
        return True

    except ClientError as err:
        print(f"[-] AWS ECS API Error during rollback: {err}")
        return False
    except Exception as exc:
        print(f"[-] Unexpected error during rollback: {exc}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Rollback ECS service to stable task definition")
    parser.add_argument("--cluster", required=True, help="ECS Cluster Name")
    parser.add_argument("--service", required=True, help="ECS Service Name")
    parser.add_argument("--target-task-def", required=True, help="Target Task Definition ARN/Name")

    args = parser.parse_args()
    success = rollback_ecs_service(
        cluster=args.cluster,
        service=args.service,
        target_task_def=args.target_task_def,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
