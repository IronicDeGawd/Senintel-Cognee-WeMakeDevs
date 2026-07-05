"""GitLab simulator: the P2-4 correlation seam (get_mr_diff) + the P1 review
operations (get_pipeline_logs, post_mr_note). Offline, no creds."""

from integrations.gitlab.factory import get as get_gitlab
from integrations.gitlab.simulator import GitLabSimulator


def test_factory_returns_simulator_in_sim():
    assert isinstance(get_gitlab("sim"), GitLabSimulator)


def test_get_mr_diff_returns_canned_diff_for_known_commit():
    diff = get_gitlab("sim").get_mr_diff("abc1234")
    assert diff["commit"] == "abc1234"
    assert diff["service"] == "checkout-service"
    assert "select_related" in diff["diff"]  # the N+1 regression is in the diff


def test_get_mr_diff_short_sha_matches():
    diff = get_gitlab("sim").get_mr_diff("abc1234"[:7])
    assert "error" not in diff


def test_get_mr_diff_unknown_commit_returns_error():
    diff = get_gitlab("sim").get_mr_diff("deadbeef")
    assert "error" in diff
    assert diff["known_commit"] == "abc1234"


def test_get_pipeline_logs_returns_failing_run_for_known_mr():
    logs = get_gitlab("sim").get_pipeline_logs(42)
    assert logs["status"] == "failed"
    assert logs["failed_job"] == "test:checkout"
    # The CI failure points at the same N+1 regression that get_mr_diff returns.
    assert "27 were done" in logs["logs"]


def test_get_pipeline_logs_unknown_mr_returns_error():
    logs = get_gitlab("sim").get_pipeline_logs(999)
    assert "error" in logs
    assert logs["known_mr_id"] == 42


def test_post_mr_note_writes_markdown_to_out(tmp_path, monkeypatch):
    monkeypatch.setattr("integrations.gitlab.simulator._OUT_DIR", tmp_path)
    dest = get_gitlab("sim").post_mr_note(42, "# Review\n\nLGTM")
    assert dest.endswith("mr_note_42.md")
    assert (tmp_path / "mr_note_42.md").read_text(encoding="utf-8").startswith("# Review")
