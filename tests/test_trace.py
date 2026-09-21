from __future__ import annotations

from datetime import UTC, datetime

from shadowflow.engine.trace import normalize_bundle
from shadowflow.models import ActionKind, TargetSnapshot, TraceBundle, TraceEvent


def test_secret_like_input_is_redacted_before_persistence() -> None:
    trace = TraceBundle(
        id="secret-trace",
        title="secret",
        source="recorded",
        events=[
            TraceEvent(
                id="evt-1",
                seq=9,
                at=datetime.now(UTC),
                page="/settings",
                action=ActionKind.INPUT,
                target=TargetSnapshot(label="API Key", role="textbox", accessible_name="API Key"),
                value="sk-do-not-store",
            )
        ],
    )
    normalized = normalize_bundle(trace)
    assert normalized.events[0].seq == 0
    assert normalized.events[0].value == "<redacted>"
    assert normalized.redactions
    assert "sk-do-not-store" not in normalized.model_dump_json()
