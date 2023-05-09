import pytest
from extract_git_ref import get_branch


def test_push_heads():
    branch = get_branch(gh_event="push", gh_ref="refs/heads/foo", gh_head_ref=None)

    assert branch == "BRANCH=foo"


def test_push_tags():
    branch = get_branch(gh_event="push", gh_ref="refs/tags/1.2.3", gh_head_ref=None)

    assert branch == "BRANCH=1.2.3"


def test_push_bad_ref():
    with pytest.raises(
        ValueError,
        match="Unanticipated git ref from a GitHub push event: refs/baz/1.2.3",
    ):
        get_branch(gh_event="push", gh_ref="refs/baz/1.2.3", gh_head_ref=None)


def test_pr_heads():
    branch = get_branch(
        gh_event="pull_request", gh_ref="refs/heads/baz", gh_head_ref="baz"
    )

    assert branch == "BRANCH=baz"


def test_pr_unset_head_ref():
    with pytest.raises(ValueError, match="GITHUB_HEAD_REF isn't set"):
        get_branch(gh_event="pull_request", gh_ref="refs/heads/baz", gh_head_ref=None)


def test_workflow_dispatch_heads():
    branch = get_branch(
        gh_event="workflow_dispatch", gh_ref="refs/heads/bar/baz", gh_head_ref=None
    )

    assert branch == "BRANCH=bar/baz"


def test_workflow_dispatch_tags():
    with pytest.raises(
        ValueError, match="Unanticipated git ref from a GitHub workflow_dispatch event"
    ):
        get_branch(
            gh_event="workflow_dispatch", gh_ref="refs/tags/x.y.z", gh_head_ref=None
        )


def test_bad_gh_event():
    with pytest.raises(ValueError, match="Unanticipated GitHub Event: foo"):
        get_branch(gh_event="foo", gh_ref="refs/tags/x.y.z", gh_head_ref=None)
