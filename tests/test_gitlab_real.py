"""P1-7.1: real GitLab adapter normalizer tests. Mock the REST transport so
the suite stays offline; the live path is verified via scripts/probe_gitlab.py
+ scripts/run_code_review.py against MR !1.
"""

from __future__ import annotations

import pytest

import integrations.gitlab.real as real_mod
from shared.config import settings


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setattr(settings, "gitlab_url", "https://gitlab.com")
    monkeypatch.setattr(settings, "gitlab_project_id", 83079708)
    monkeypatch.setattr(settings, "gitlab_token", "glpat-test")
    return settings


class _RestStub:
    """Stand-in for GitLabReal._rest that records every call and returns canned
    payloads keyed by URL path."""

    def __init__(self, by_path: dict):
        self.by_path = by_path
        self.calls: list[tuple[str, str, dict]] = []

    def __call__(self, method, path, **kwargs):
        self.calls.append((method, path, kwargs))
        if path not in self.by_path:
            raise AssertionError(f"unexpected REST call: {method} {path}")
        return self.by_path[path]


def test_requires_url_project_and_token(monkeypatch):
    monkeypatch.setattr(settings, "gitlab_url", "")
    with pytest.raises(RuntimeError, match="GITLAB_URL"):
        real_mod.GitLabReal()
    monkeypatch.setattr(settings, "gitlab_url", "https://gitlab.com")
    monkeypatch.setattr(settings, "gitlab_project_id", 0)
    with pytest.raises(RuntimeError, match="GITLAB_PROJECT_ID"):
        real_mod.GitLabReal()
    monkeypatch.setattr(settings, "gitlab_project_id", 1)
    monkeypatch.setattr(settings, "gitlab_token", "")
    with pytest.raises(RuntimeError, match="GITLAB_TOKEN"):
        real_mod.GitLabReal()


def test_get_mr_diff_resolves_iid_then_reads_mr_and_changes(monkeypatch, configured):
    rest = _RestStub(
        {
            "/projects/83079708/repository/commits/abc1234/merge_requests": [
                {"iid": 1, "title": "X"}
            ],
            "/projects/83079708/merge_requests/1": {
                "iid": 1,
                "title": "Show full order history on checkout confirmation",
                "author": {"username": "dev.jane"},
                "merged_at": "2026-06-10T12:00:00Z",
            },
            "/projects/83079708/merge_requests/1/changes": {
                "changes": [
                    {
                        "old_path": "checkout/views.py",
                        "new_path": "checkout/views.py",
                        "diff": "@@ removed select_related @@",
                    }
                ]
            },
        }
    )
    adapter = real_mod.GitLabReal()
    monkeypatch.setattr(adapter, "_rest", rest)

    diff = adapter.get_mr_diff("abc1234")
    assert diff["commit"] == "abc1234"
    assert diff["mr_id"] == 1
    assert diff["mr_title"].startswith("Show full order history")
    assert diff["author"] == "dev.jane"
    assert diff["files_changed"] == ["checkout/views.py"]
    assert "removed select_related" in diff["diff"]
    # Three REST calls in order: resolve, MR detail, MR changes.
    assert [c[1] for c in rest.calls] == [
        "/projects/83079708/repository/commits/abc1234/merge_requests",
        "/projects/83079708/merge_requests/1",
        "/projects/83079708/merge_requests/1/changes",
    ]


def test_get_mr_diff_unknown_commit_returns_error(monkeypatch, configured):
    rest = _RestStub(
        {"/projects/83079708/repository/commits/deadbeef/merge_requests": []}
    )
    adapter = real_mod.GitLabReal()
    monkeypatch.setattr(adapter, "_rest", rest)

    diff = adapter.get_mr_diff("deadbeef")
    assert "error" in diff
    assert diff["known_commit"] == "deadbeef"


def test_get_pipeline_logs_picks_first_failed_job(monkeypatch, configured):
    rest = _RestStub(
        {
            "/projects/83079708/merge_requests/1/pipelines": [
                {"id": 9001, "status": "failed", "sha": "abc1234"}
            ],
            "/projects/83079708/pipelines/9001/jobs": [
                {"id": 100, "name": "lint", "status": "success"},
                {"id": 200, "name": "test:checkout", "status": "failed"},
            ],
        }
    )

    class _FakeResp:
        text = "FAILED 1 test in 12s\n"

        def raise_for_status(self):
            return None

    class _FakeClient:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return None

        def get(self, url, headers=None):
            assert url.endswith("/jobs/200/trace")
            return _FakeResp()

    adapter = real_mod.GitLabReal()
    monkeypatch.setattr(adapter, "_rest", rest)
    monkeypatch.setattr(real_mod.httpx, "Client", _FakeClient)

    logs = adapter.get_pipeline_logs(1)
    assert logs["status"] == "failed"
    assert logs["pipeline_id"] == 9001
    assert logs["failed_job"] == "test:checkout"
    assert "FAILED 1 test" in logs["logs"]


def test_get_pipeline_logs_green_pipeline_returns_empty_logs(monkeypatch, configured):
    rest = _RestStub(
        {"/projects/83079708/merge_requests/1/pipelines": [{"id": 9002, "status": "success"}]}
    )
    adapter = real_mod.GitLabReal()
    monkeypatch.setattr(adapter, "_rest", rest)
    logs = adapter.get_pipeline_logs(1)
    assert logs["status"] == "success"
    assert logs["logs"] == ""


def test_get_pipeline_logs_no_pipeline_returns_error(monkeypatch, configured):
    rest = _RestStub({"/projects/83079708/merge_requests/99/pipelines": []})
    adapter = real_mod.GitLabReal()
    monkeypatch.setattr(adapter, "_rest", rest)
    logs = adapter.get_pipeline_logs(99)
    assert "error" in logs
    assert logs["known_mr_id"] == 99


def test_post_mr_note_returns_web_url(monkeypatch, configured):
    rest = _RestStub(
        {
            "/projects/83079708/merge_requests/1/notes": {
                "id": 4242,
                "web_url": "https://gitlab.com/x/-/merge_requests/1#note_4242",
            }
        }
    )
    adapter = real_mod.GitLabReal()
    monkeypatch.setattr(adapter, "_rest", rest)

    dest = adapter.post_mr_note(1, "# Review")
    assert dest.endswith("#note_4242")
    method, path, kwargs = rest.calls[0]
    assert method == "POST"
    assert kwargs["json"] == {"body": "# Review"}
