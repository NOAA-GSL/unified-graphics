#!/usr/bin/env python3

import os

def get_branch():
    gh_event = os.environ["GITHUB_EVENT_NAME"]
    gh_ref = os.environ["GITHUB_REF"]
    gh_head_ref = os.environ.get("GITHUB_HEAD_REF")  # only exists in PRs

    if gh_event == "pull_request":
        if gh_head_ref is not None:
            msg = f"BRANCH={gh_head_ref}"
        else:
            raise ValueError("GITHUB_HEAD_REF isn't set")
    elif gh_event == "push":
        # Handle differences between branches/tags
        branch = "refs/heads/"
        tag = "refs/tags/"
        if gh_ref.startswith(branch):
            msg = f"BRANCH={gh_ref[len(branch):]}"
        elif gh_ref.startswith(tag):
            msg = f"BRANCH={gh_ref[len(tag):]}"
        else:
            raise ValueError("Unanticipated git ref from a GitHub push event")
    elif gh_event == "workflow_dispatch":
        # Workflow Dispatch should only be able to trigger from branches
        branch = "refs/heads/"
        if gh_ref.startswith(branch):
            msg = f"BRANCH={gh_ref[len(branch):]}"
        else:
            raise ValueError("Unanticipated git ref from a GitHub workflow_dispatch event")
    else:
        raise ValueError("Unanticipated GitHub Event")
    return msg


if __name__ == '__main__':
    gh_env_file = os.environ["GITHUB_ENV"]
    branch = get_branch()

    with open(gh_env_file, "a") as env_file:
        env_file.write(branch + "\n")
