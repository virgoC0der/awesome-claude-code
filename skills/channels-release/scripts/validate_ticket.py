#!/usr/bin/env python3
"""Validate high-risk invariants in a normal Release Train JSON payload."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


COMMIT_RE = re.compile(r"^[0-9a-fA-F]{7,64}$")


def fail(message: str) -> None:
    raise ValueError(message)


def positive_int(value: object, field: str) -> None:
    if not isinstance(value, int) or value <= 0:
        fail(f"{field} must be a positive integer")


def validate_task(task: dict, prefix: str, allowed_envs: set[str]) -> tuple[int, str]:
    env = task.get("env")
    category = task.get("env_category")
    if env not in allowed_envs or category not in allowed_envs:
        fail(f"{prefix} targets unauthorized environment: env={env!r}, env_category={category!r}")
    if env != category:
        fail(f"{prefix} env and env_category must match")
    version = task.get("version")
    if not isinstance(version, str) or not version.strip():
        fail(f"{prefix}.version is required")
    positive_int(task.get("image_id"), f"{prefix}.image_id")
    positive_int(task.get("ci_id"), f"{prefix}.ci_id")
    positive_int(task.get("env_id"), f"{prefix}.env_id")
    commit = task.get("github_committed_id")
    if not isinstance(commit, str) or not COMMIT_RE.fullmatch(commit):
        fail(f"{prefix}.github_committed_id must be a Git commit hash")
    images = task.get("images")
    if not isinstance(images, list) or len(images) != 1:
        fail(f"{prefix}.images must contain exactly one artifact")
    image = images[0]
    if image.get("image_id") != task.get("image_id"):
        fail(f"{prefix}.images[0].image_id does not match task image_id")
    if image.get("version") != version or image.get("name") != version:
        fail(f"{prefix}.images[0] version/name does not match task version")
    if image.get("github_committed_id") != commit:
        fail(f"{prefix}.images[0] commit does not match task commit")
    return int(task.get("application_id", 0)), env


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("payload", type=Path)
    parser.add_argument("--allowed-env", action="append", required=True)
    args = parser.parse_args()

    allowed_envs = set(args.allowed_env)
    if not allowed_envs <= {"staging", "production"}:
        fail("allowed environments may only be staging or production")

    payload = json.loads(args.payload.read_text(encoding="utf-8"))
    if payload.get("release_type") != "release":
        fail("release_type must be release")
    if payload.get("has_tasks") is not True:
        fail("has_tasks must be true")
    if payload.get("is_duplicated") is not False:
        fail("is_duplicated must be false")
    positive_int(payload.get("product_id"), "product_id")
    if not payload.get("co_editors"):
        fail("co_editors must not be empty")
    if not payload.get("jira_issues"):
        fail("jira_issues must not be empty")
    if payload.get("approval", {}).get("approvers") != []:
        fail("approval.approvers must be empty")
    if payload.get("qa_approval", {}).get("approvers") != []:
        fail("normal release qa_approval.approvers must be empty")

    pre_types = {item.get("checklist_type") for item in payload.get("pre_checklist", [])}
    if not {"security", "qa", "po"} <= pre_types or not ({"fe", "be"} & pre_types):
        fail("pre_checklist needs security, qa, po, and at least one fe/be segment")
    post_types = {item.get("checklist_type") for item in payload.get("post_checklist", [])}
    if not ({"fe", "be"} & post_types):
        fail("post_checklist needs at least one fe/be segment")

    services = payload.get("services")
    rollbacks = payload.get("rollbacks")
    if not isinstance(services, list) or not services:
        fail("services must not be empty")
    if not isinstance(rollbacks, list) or not rollbacks:
        fail("rollbacks must not be empty")

    deploy_dimensions: set[tuple[int, str]] = set()
    rollback_dimensions: set[tuple[int, str]] = set()
    deploy_versions: dict[tuple[int, str], str] = {}

    for service_index, service in enumerate(services):
        app_id = service.get("application_id")
        positive_int(app_id, f"services[{service_index}].application_id")
        if service.get("deploy_type") != "deploy":
            fail(f"services[{service_index}].deploy_type must be deploy")
        tasks = service.get("tasks") or []
        if not tasks:
            fail(f"services[{service_index}].tasks must not be empty")
        for task_index, task in enumerate(tasks):
            task = dict(task)
            task["application_id"] = app_id
            dimension = validate_task(task, f"services[{service_index}].tasks[{task_index}]", allowed_envs)
            if dimension in deploy_dimensions:
                fail(f"duplicate deploy task dimension: {dimension}")
            deploy_dimensions.add(dimension)
            deploy_versions[dimension] = task["version"]

    for service_index, service in enumerate(rollbacks):
        app_id = service.get("application_id")
        positive_int(app_id, f"rollbacks[{service_index}].application_id")
        if service.get("deploy_type") != "rollback":
            fail(f"rollbacks[{service_index}].deploy_type must be rollback")
        tasks = service.get("tasks") or []
        if not tasks:
            fail(f"rollbacks[{service_index}].tasks must not be empty")
        for task_index, task in enumerate(tasks):
            task = dict(task)
            task["application_id"] = app_id
            dimension = validate_task(task, f"rollbacks[{service_index}].tasks[{task_index}]", allowed_envs)
            if dimension in rollback_dimensions:
                fail(f"duplicate rollback task dimension: {dimension}")
            rollback_dimensions.add(dimension)
            if deploy_versions.get(dimension) == task.get("version"):
                fail(f"rollback version equals deploy version for {dimension}")

    if deploy_dimensions != rollback_dimensions:
        fail(f"deploy/rollback dimensions differ: deploy={sorted(deploy_dimensions)}, rollback={sorted(rollback_dimensions)}")

    print(
        json.dumps(
            {
                "valid": True,
                "product": payload.get("product_name"),
                "allowed_environments": sorted(allowed_envs),
                "deploy_dimensions": sorted(deploy_dimensions),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"invalid: {exc}", file=sys.stderr)
        raise SystemExit(1)
