"""P3 DoD artifact: the gate-decision exporter must be deterministic and offline,
and must show a passing release alongside a blocked one."""

import scripts.export_eval_gate as exporter


def test_main_writes_pass_and_blocked(tmp_path, monkeypatch):
    out = tmp_path / "eval_gate.md"
    monkeypatch.setattr(exporter, "_OUT", out)

    exporter.main()

    text = out.read_text(encoding="utf-8")
    # A clean release passes, a regressed one is blocked — both appear.
    assert "✅ PASS" in text
    assert "🔴 BLOCKED" in text
    assert "checkout-llm-v1" in text
    assert "checkout-llm-v2" in text
