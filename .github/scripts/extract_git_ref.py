#!/usr/bin/env python3

from typing import Optional
import os
import re


def get_branch(gh_event: str, gh_ref: str, gh_head_ref: Optional[str]) -> str:
    """Process GitHub Actions env variables to extract the branch or tag name"""

    if gh_event not in ["pull_request", "push", "workflow_dispatch"]:
        raise ValueError(f"Unanticipated GitHub Event: {gh_event}")

    if gh_event == "pull_request":
        if gh_head_ref is None:
            raise ValueError("GITHUB_HEAD_REF isn't set")
        return f"BRANCH={gh_head_ref}"

    # Extract the branch name from the current git ref
    ref_match = re.match(r"refs/(heads|tags)/(.+)$", gh_ref)

    if not ref_match or (gh_event == "workflow_dispatch" and ref_match[1] != "heads"):
        raise ValueError(
            f"Unanticipated git ref from a GitHub {gh_event} event: {gh_ref}"
        )

    return f"BRANCH={ref_match[2]}"


if __name__ == "__main__":
    gh_event = os.environ["GITHUB_EVENT_NAME"]
    gh_ref = os.environ["GITHUB_REF"]
    gh_head_ref = os.environ.get("GITHUB_HEAD_REF")  # only exists in PRs
    branch = get_branch(gh_event, gh_ref, gh_head_ref)

    gh_env_file = os.environ["GITHUB_ENV"]
    with open(gh_env_file, "a") as env_file:
        env_file.write(branch + "\n")
